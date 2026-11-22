'use strict';

const { spawn } = require('child_process');
const readline = require('readline');

// These are supported config-schema keys. The app-server is private to this
// provider; overrides never change the user's config or the parent thread.
const DISABLED_FEATURES = [
  'apps', 'plugins', 'hooks', 'multi_agent', 'multi_agent_v2', 'js_repl',
  'code_mode', 'code_mode_host', 'computer_use', 'browser_use',
  'browser_use_external', 'in_app_browser', 'image_generation',
  'request_permissions_tool', 'skill_mcp_dependency_install',
];

class CodexProvider {
  constructor({ mainSessionId, cwd, timeoutSec = 300,
    bin = process.env.UNDERSTAND_CODEX_BIN || 'codex' }) {
    if (!mainSessionId) throw new Error('Codex のメイン thread ID が必要です。');
    this.mainSessionId = mainSessionId;
    this.cwd = cwd;
    this.bin = bin;
    this.timeoutMs = Math.max(1, Number(timeoutSec) * 1000);
    this.nextId = 1;
    this.pending = new Map();
    this.created = new Set();
    this.disabledMcp = Object.create(null);
    this.queue = Promise.resolve();
    this.active = null;
    this.closing = false;
    this.failure = null;
  }

  _config(allowCommands) {
    return {
      features: Object.fromEntries([
        ...DISABLED_FEATURES.map(name => [name, false]),
        ['shell_tool', allowCommands], ['unified_exec', allowCommands],
      ]),
      agents: { enabled: false },
      web_search: 'disabled',
      thread_unload_delay_secs: 0,
      mcp_servers: this.disabledMcp,
    };
  }

  async _ready() {
    if (this.failure) throw this.failure;
    if (this.ready) return this.ready;
    this.ready = (async () => {
      const args = ['app-server', '--stdio'];
      for (const name of [...DISABLED_FEATURES, 'shell_tool', 'unified_exec']) {
        args.push('-c', `features.${name}=false`);
      }
      args.push('-c', 'agents.enabled=false', '-c', 'web_search="disabled"',
        '-c', 'thread_unload_delay_secs=0');
      this.child = spawn(this.bin, args, { cwd: this.cwd, env: process.env,
        stdio: ['pipe', 'pipe', 'pipe'] });
      this.stopped = new Promise(resolve => this.child.once('close', resolve));
      this.child.on('error', error => this._fail(new Error(`Codex を起動できません: ${error.message}`)));
      this.child.on('close', () => this._fail(new Error('Codex app-server が終了しました。')));
      this.child.stdin.on('error', error => this._fail(error));
      // Drain stderr without exposing config, credentials, or conversation text.
      this.child.stderr.on('data', () => {});
      readline.createInterface({ input: this.child.stdout }).on('line', line => {
        try { this._message(JSON.parse(line)); }
        catch (_) { this._fail(new Error('Codex app-server の応答形式が不正です。')); }
      });
      await this._request('initialize', {
        clientInfo: { name: 'understand-mode', version: '1.0.0' },
        capabilities: { experimentalApi: true },
      });
      this._send({ method: 'initialized' });
      // Disable direct MCP servers too: plugins=false does not disable servers
      // supplied by user/project config. Only names are retained, never secrets.
      const effective = await this._request('config/read', { cwd: this.cwd, includeLayers: true });
      const configs = [effective.config, ...(effective.layers || []).map(layer => layer.config)];
      for (const config of configs) {
        for (const name of Object.keys(config?.mcp_servers || {})) {
          this.disabledMcp[name] = { enabled: false };
        }
      }
    })();
    return this.ready;
  }

  _send(message) {
    if (this.failure) throw this.failure;
    this.child.stdin.write(JSON.stringify(message) + '\n');
  }

  _request(method, params, timeout = this.timeoutMs) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Codex の ${method} が時間切れになりました。`));
      }, timeout);
      this.pending.set(id, {
        resolve: value => { clearTimeout(timer); resolve(value); },
        reject: error => { clearTimeout(timer); reject(error); },
      });
      try { this._send({ id, method, params }); }
      catch (error) { this.pending.delete(id); clearTimeout(timer); reject(error); }
    });
  }

  _fail(error) {
    this.failure ||= error;
    for (const pending of this.pending.values()) pending.reject(error);
    this.pending.clear();
    this.active?.reject(error);
  }

  _message(message) {
    if (message.id !== undefined && !message.method) {
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message || 'Codex RPC error'));
      else pending.resolve(message.result);
      return;
    }
    if (message.id !== undefined && message.method) {
      // No unattended approval or dynamic tool execution. Unknown requests get
      // an RPC error rather than hanging or silently granting permissions.
      let result;
      if (['item/commandExecution/requestApproval', 'item/fileChange/requestApproval'].includes(message.method)) {
        result = { decision: 'decline' };
      } else if (message.method === 'item/permissions/requestApproval') {
        result = { permissions: {}, scope: 'turn' };
      }
      this._send(result ? { id: message.id, result } : {
        id: message.id, error: { code: -32601, message: 'understand-mode does not approve or execute client tool requests' },
      });
      this.active?.reject(new Error(`追加の承認またはクライアントツールが必要です: ${message.method}`));
      return;
    }
    const active = this.active;
    if (!active || message.params?.threadId !== active.threadId) return;
    if (!active.turnId) { active.early.push(message); return; }
    this._turnMessage(active, message);
  }

  _turnMessage(active, message) {
    const params = message.params;
    const turnId = params.turnId || params.turn?.id;
    if (turnId !== active.turnId) return;
    if (message.method === 'item/completed' && params.item?.type === 'agentMessage') {
      active.messages.set(params.item.id, params.item);
    }
    if (message.method === 'turn/completed') {
      const turn = params.turn;
      for (const item of turn.items || []) {
        if (item.type === 'agentMessage') active.messages.set(item.id, item);
      }
      if (turn.status !== 'completed') {
        active.reject(new Error(turn.error?.message || `Codex の応答が ${turn.status} で終了しました。`));
        return;
      }
      const messages = [...active.messages.values()];
      const finals = messages.filter(item => item.phase === 'final_answer');
      const text = (finals.length ? finals : messages).map(item => item.text).join('\n\n');
      if (!text) active.reject(new Error('Codex が回答本文を返しませんでした。'));
      else active.resolve(text);
    }
    if (message.method === 'error' && !params.willRetry) {
      active.reject(new Error(params.error?.message || 'Codex の応答でエラーが発生しました。'));
    }
  }

  run(options) {
    const task = this.queue.then(() => this._run(options));
    this.queue = task.catch(() => {});
    return task;
  }

  async _releaseThread(threadId) {
    try {
      const released = await this._request('thread/unsubscribe', { threadId }, 1500);
      if (!['notLoaded', 'notSubscribed', 'unsubscribed'].includes(released.status)) {
        throw new Error('不正な unsubscribe 応答です。');
      }
      // Unsubscribe is not synchronous unload. A loaded thread can ignore
      // resume config overrides; prove cold resume is possible before returning.
      const deadline = Date.now() + Math.min(5000, this.timeoutMs);
      while (true) {
        let cursor;
        let loaded = false;
        do {
          const page = await this._request('thread/loaded/list', cursor ? { cursor } : {}, 1500);
          if (!Array.isArray(page.data)) throw new Error('不正な loaded/list 応答です。');
          loaded ||= page.data.includes(threadId);
          cursor = page.nextCursor;
        } while (cursor);
        if (!loaded) return;
        if (Date.now() >= deadline) throw new Error('アンロードが時間切れになりました。');
        await new Promise(resolve => setTimeout(resolve, 30));
      }
    } catch (error) {
      this.policyFailure = new Error(`会話のアンロードを確認できないため、以降の質問を停止しました: ${error.message}`);
      throw this.policyFailure;
    }
  }

  async _run({ prompt, resume, fork = false, appendSystem = '', allowCommands = false }) {
    let threadId;
    let active;
    let timer;
    let releaseAttempted = false;
    try {
      if (this.closing) throw new Error('understand-mode は終了処理中です。');
      if (this.policyFailure) throw this.policyFailure;
      if (resume && !this.created.has(resume) && !(fork && resume === this.mainSessionId)) {
        throw new Error('このアプリで作成した会話だけを継続できます。');
      }
      if (fork && !resume) throw new Error('分岐元の thread ID が必要です。');
      await this._ready();
      const params = {
        cwd: this.cwd, sandbox: 'read-only', approvalPolicy: 'on-request',
        approvalsReviewer: 'user', config: this._config(allowCommands),
        ...(appendSystem ? { developerInstructions: appendSystem } : {}),
      };
      let response;
      if (fork) response = await this._request('thread/fork', { ...params, threadId: resume, ephemeral: false });
      else if (resume) response = await this._request('thread/resume', { ...params, threadId: resume });
      else response = await this._request('thread/start', { ...params, ephemeral: false });
      threadId = response.thread?.id;
      if (!threadId || threadId === this.mainSessionId || (!fork && resume && threadId !== resume)) {
        throw new Error('Codex が不正な分岐先 thread ID を返しました。');
      }
      this.created.add(threadId);
      const completed = new Promise((resolve, reject) => {
        active = { threadId, turnId: null, early: [], messages: new Map(), resolve, reject };
      });
      // The turn may finish before turn/start's response reaches us. Buffer its
      // notifications, then match the exact returned turn ID before delivery.
      completed.catch(() => {});
      this.active = active;
      const started = await this._request('turn/start', {
        threadId,
        input: [{ type: 'text', text: appendSystem ? `${appendSystem}\n\n${prompt}` : prompt }],
        effort: 'low', approvalPolicy: 'on-request', approvalsReviewer: 'user',
        sandboxPolicy: { type: 'readOnly', networkAccess: false },
      });
      active.turnId = started.turn?.id;
      if (!active.turnId) throw new Error('Codex が turn ID を返しませんでした。');
      timer = setTimeout(() => active.reject(new Error('Codex の回答が時間切れになりました。')), this.timeoutMs);
      for (const message of active.early) this._turnMessage(active, message);
      active.early = [];
      const text = await completed;
      clearTimeout(timer);
      releaseAttempted = true;
      await this._releaseThread(threadId);
      return { ok: true, text, sessionId: threadId };
    } catch (error) {
      if (!releaseAttempted && active?.turnId && !this.failure) {
        await this._request('turn/interrupt', { threadId, turnId: active.turnId }, 1500).catch(() => {});
      }
      if (!releaseAttempted && this.created.has(threadId)) {
        try { await this._releaseThread(threadId); }
        catch (releaseError) { error = new Error(`${error.message}\n${releaseError.message}`); }
      }
      return { ok: false, error: error.message,
        ...(this.created.has(threadId) ? { sessionId: threadId } : {}) };
    } finally {
      clearTimeout(timer);
      if (this.active === active) this.active = null;
    }
  }

  async close() {
    if (this.closePromise) return this.closePromise;
    this.closing = true;
    this.closePromise = (async () => {
      this.active?.reject(new Error('understand-mode を終了しました。'));
      await this.queue;
      const errors = [];
      if (this.child) {
        for (const threadId of [...this.created].reverse()) {
          try { await this._request('thread/delete', { threadId }, 1500); }
          catch (_) { errors.push(threadId); }
        }
        this.child.stdin.end();
        if (this.child.exitCode === null) this.child.kill('SIGTERM');
        const force = setTimeout(() => this.child.kill('SIGKILL'), 1000);
        await this.stopped;
        clearTimeout(force);
      }
      if (errors.length) throw new Error(`寄り道の会話を削除できませんでした: ${errors.join(', ')}`);
    })();
    return this.closePromise;
  }
}

module.exports = { CodexProvider };
