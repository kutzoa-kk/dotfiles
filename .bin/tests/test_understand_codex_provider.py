"""Drive the Node provider against a fake executable; never call a model."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import urllib.parse
import urllib.request


REPO = Path(__file__).resolve().parents[2]
PROVIDER = REPO / "dotdir/.claude/skills/understand/app/codex-provider.js"

FAKE_SERVER = r'''
import json, os, sys
counter = 0
turn_counter = 0
loaded = set()
settings = {}
def send(message):
    print(json.dumps(message), flush=True)
def notify(method, params):
    send({'method': method, 'params': params})
for line in sys.stdin:
    message = json.loads(line)
    with open(os.environ['FAKE_CODEX_LOG'], 'a') as log:
        log.write(json.dumps(message) + '\n')
    method = message.get('method')
    params = message.get('params', {})
    if 'id' not in message or not method:
        continue
    result = {}
    if method == 'config/read':
        result = {'config': {'mcp_servers': {'direct': {'command': 'never-run'}}},
                  'layers': [{'config': {'mcp_servers': {'project': {'url': 'not-contacted'}}}}]}
    elif method in ('thread/start', 'thread/fork'):
        counter += 1
        thread = 'parent' if os.environ.get('FAKE_RETURN_PARENT') else 'fork-' + str(counter)
        loaded.add(thread)
        settings[thread] = params['config']
        result = {'thread': {'id': thread}}
    elif method == 'thread/resume':
        # Real app-server ignores overrides when this client still subscribes.
        if params['threadId'] not in loaded:
            settings[params['threadId']] = params['config']
        loaded.add(params['threadId'])
        result = {'thread': {'id': params['threadId']}}
    elif method == 'thread/unsubscribe':
        if not os.environ.get('FAKE_KEEP_LOADED'):
            loaded.discard(params['threadId'])
        result = {'status': 'unsubscribed'}
    elif method == 'thread/loaded/list':
        result = {'data': sorted(loaded), 'nextCursor': None}
    elif method == 'turn/start':
        turn_counter += 1
        thread = params['threadId']
        turn = 'turn-' + str(turn_counter)
        result = {'turn': {'id': turn, 'status': 'inProgress', 'items': []}}
        prompt = params['input'][0]['text']
        if 'RPC_ERROR' in prompt:
            send({'id': message['id'], 'error': {'code': -32000, 'message': 'fixture RPC failure'}})
            continue
        if 'EARLY' not in prompt:
            send({'id': message['id'], 'result': result})
        if 'TIMEOUT' in prompt:
            continue
        if 'TURN_FAILED' in prompt:
            notify('turn/completed', {'threadId': thread, 'turn': {
                'id': turn, 'status': 'failed', 'items': [], 'error': {'message': 'fixture turn failure'}}})
            continue
        if ('SHELL_ON' in prompt and not settings[thread]['features']['shell_tool']) or (
                'SHELL_OFF' in prompt and settings[thread]['features']['shell_tool']):
            notify('turn/completed', {'threadId': thread, 'turn': {
                'id': turn, 'status': 'failed', 'items': [], 'error': {'message': 'wrong shell permissions'}}})
            continue
        if 'APPROVAL' in prompt:
            send({'id': 'approval-1', 'method': 'item/commandExecution/requestApproval',
                  'params': {'threadId': thread, 'turnId': turn, 'itemId': 'command-1'}})
            continue
        if 'UNKNOWN_TOOL' in prompt:
            send({'id': 'tool-1', 'method': 'item/tool/call',
                  'params': {'threadId': thread, 'turnId': turn, 'tool': 'unexpected'}})
            continue
        # Unrelated and stale turns must never provide this request's answer.
        notify('turn/completed', {'threadId': 'someone-else', 'turn': {
            'id': turn, 'status': 'completed', 'items': [
                {'type': 'agentMessage', 'id': 'foreign', 'text': 'WRONG'}]}})
        notify('turn/completed', {'threadId': thread, 'turn': {
            'id': 'turn-old', 'status': 'completed', 'items': [
                {'type': 'agentMessage', 'id': 'old', 'text': 'STALE'}]}})
        notify('item/completed', {'threadId': thread, 'turnId': turn, 'item': {
            'type': 'agentMessage', 'id': 'comment', 'phase': 'commentary', 'text': 'thinking'}})
        notify('item/completed', {'threadId': thread, 'turnId': turn, 'item': {
            'type': 'agentMessage', 'id': 'answer', 'phase': 'final_answer', 'text': 'answer:' + prompt}})
        notify('turn/completed', {'threadId': thread,
            'turn': {'id': turn, 'status': 'completed', 'items': []}})
        if 'EARLY' in prompt:
            send({'id': message['id'], 'result': result})
        continue
    if method == 'thread/delete' and os.environ.get('FAKE_DELETE_FAIL'):
        send({'id': message['id'], 'error': {'code': -32000, 'message': 'fixture delete failure'}})
    else:
        send({'id': message['id'], 'result': result})
'''


@unittest.skipUnless(shutil.which("node"), "Node is required")
class CodexProviderTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "rpc.jsonl"
        self.fake = self.root / "fake-codex"
        self.fake.write_text(f"#!{sys.executable}\n" + textwrap.dedent(FAKE_SERVER))
        self.fake.chmod(0o755)

    def run_provider(self, body, *, timeout=1, extra_env=None):
        script = """
const { CodexProvider } = require(process.argv[1]);
(async () => {
  const provider = new CodexProvider({mainSessionId:'parent', cwd:process.cwd(),
    bin:process.argv[2], timeoutSec:Number(process.argv[3])});
  let result;
  try { result = await (async () => { BODY })(); }
  finally { await provider.close(); }
  console.log(JSON.stringify(result));
})().catch(error => { console.error(error.message); process.exitCode=1; });
""".replace("BODY", body)
        result = subprocess.run(
            ["node", "-e", script, str(PROVIDER), str(self.fake), str(timeout)],
            cwd=self.root, env={**os.environ, "FAKE_CODEX_LOG": str(self.log), **(extra_env or {})},
            capture_output=True, text=True, timeout=12, check=True,
        )
        messages = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return json.loads(result.stdout), messages

    def requests(self, messages, method):
        return [m["params"] for m in messages if m.get("method") == method]

    def test_fork_followup_nested_and_draft_delete_only_created_threads(self):
        results, messages = self.run_provider("""
const first = await provider.run({prompt:'first',resume:'parent',fork:true,appendSystem:'explain'});
const follow = await provider.run({prompt:'follow',resume:first.sessionId});
const nested = await provider.run({prompt:'nested',resume:first.sessionId,fork:true});
const draft = await provider.run({prompt:'draft'});
return [first,follow,nested,draft];
""")
        self.assertTrue(all(result["ok"] for result in results))
        self.assertEqual([r["sessionId"] for r in results], ["fork-1", "fork-1", "fork-2", "fork-3"])
        self.assertEqual(results[0]["text"], "answer:explain\n\nfirst")
        forks = self.requests(messages, "thread/fork")
        self.assertEqual([r["threadId"] for r in forks], ["parent", "fork-1"])
        self.assertFalse(forks[0]["ephemeral"])
        self.assertEqual(forks[0]["developerInstructions"], "explain")
        self.assertEqual([r["threadId"] for r in self.requests(messages, "thread/delete")],
                         ["fork-3", "fork-2", "fork-1"])
        self.assertFalse(any("model" in r for r in forks + self.requests(messages, "turn/start")))

    def test_parent_and_foreign_resume_rejected_before_any_rpc(self):
        results, messages = self.run_provider("""
return [await provider.run({prompt:'bad',resume:'parent'}),
        await provider.run({prompt:'bad',resume:'someone-else',fork:true})];
""")
        self.assertTrue(all(not r["ok"] for r in results))
        self.assertEqual(messages, [])

    def test_question_resets_sql_shell_and_disables_direct_mcp_and_side_effects(self):
        results, messages = self.run_provider("""
const first=await provider.run({prompt:'SHELL_OFF',resume:'parent',fork:true});
const sql=await provider.run({prompt:'SHELL_ON',resume:first.sessionId,allowCommands:true});
const again=await provider.run({prompt:'SHELL_OFF',resume:first.sessionId});
return [first,sql,again];
""")
        self.assertTrue(all(r["ok"] for r in results))
        reloads = self.requests(messages, "thread/resume")
        self.assertEqual([r["config"]["features"]["shell_tool"] for r in reloads], [True, False])
        for request in self.requests(messages, "thread/fork") + reloads:
            config = request["config"]
            for name in ("apps", "plugins", "hooks", "multi_agent", "multi_agent_v2", "js_repl", "code_mode_host"):
                self.assertFalse(config["features"][name])
            self.assertEqual(config["mcp_servers"], {"direct": {"enabled": False}, "project": {"enabled": False}})
            self.assertEqual(request["sandbox"], "read-only")
            self.assertEqual(request["approvalPolicy"], "on-request")
            self.assertEqual(config["thread_unload_delay_secs"], 0)
        self.assertEqual(self.requests(messages, "thread/unsubscribe"), [{"threadId": "fork-1"}] * 3)
        for turn in self.requests(messages, "turn/start"):
            self.assertEqual(turn["sandboxPolicy"], {"type": "readOnly", "networkAccess": False})

    def test_timeout_interrupts_then_can_continue_without_stale_answer(self):
        results, messages = self.run_provider("""
const timed=await provider.run({prompt:'TIMEOUT',resume:'parent',fork:true});
const next=await provider.run({prompt:'after timeout',resume:timed.sessionId});
return [timed,next];
""", timeout=0.15)
        self.assertFalse(results[0]["ok"])
        self.assertIn("時間切れ", results[0]["error"])
        self.assertEqual(results[1]["text"], "answer:after timeout")
        self.assertEqual(self.requests(messages, "turn/interrupt"), [{"threadId": "fork-1", "turnId": "turn-1"}])

    def test_approval_is_declined_and_returned_as_error(self):
        result, messages = self.run_provider("return await provider.run({prompt:'APPROVAL',resume:'parent',fork:true});")
        self.assertFalse(result["ok"])
        self.assertIn("承認", result["error"])
        replies = [m for m in messages if m.get("id") == "approval-1"]
        self.assertEqual(replies, [{"id": "approval-1", "result": {"decision": "decline"}}])
        self.assertEqual(len(self.requests(messages, "turn/interrupt")), 1)

    def test_unknown_client_tool_is_rejected_without_execution(self):
        result, messages = self.run_provider("return await provider.run({prompt:'UNKNOWN_TOOL',resume:'parent',fork:true});")
        self.assertFalse(result["ok"])
        replies = [m for m in messages if m.get("id") == "tool-1"]
        self.assertEqual(replies[0]["error"]["code"], -32601)

    def test_rpc_failure_is_reported_and_created_thread_is_still_cleaned(self):
        result, messages = self.run_provider("return await provider.run({prompt:'RPC_ERROR',resume:'parent',fork:true});")
        self.assertFalse(result["ok"])
        self.assertIn("fixture RPC failure", result["error"])
        self.assertEqual(self.requests(messages, "thread/delete"), [{"threadId": "fork-1"}])

    def test_simultaneous_requests_are_serialized_and_not_mixed(self):
        results, messages = self.run_provider("""
return await Promise.all([
  provider.run({prompt:'one',resume:'parent',fork:true}),
  provider.run({prompt:'two',resume:'parent',fork:true})]);
""")
        self.assertEqual([r["text"] for r in results], ["answer:one", "answer:two"])
        self.assertEqual([r["threadId"] for r in self.requests(messages, "turn/start")], ["fork-1", "fork-2"])

    def test_notifications_before_turn_start_response_are_preserved(self):
        result, _ = self.run_provider("return await provider.run({prompt:'EARLY',resume:'parent',fork:true});")
        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "answer:EARLY")

    def test_failed_turn_is_not_reported_as_success(self):
        result, _ = self.run_provider("return await provider.run({prompt:'TURN_FAILED',resume:'parent',fork:true});")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "fixture turn failure")

    def test_invalid_fork_result_never_exposes_or_deletes_parent(self):
        result, messages = self.run_provider(
            "return await provider.run({prompt:'ask',resume:'parent',fork:true});",
            extra_env={"FAKE_RETURN_PARENT": "1"})
        self.assertFalse(result["ok"])
        self.assertNotIn("sessionId", result)
        self.assertEqual(self.requests(messages, "turn/start"), [])
        self.assertEqual(self.requests(messages, "thread/delete"), [])

    def test_cleanup_failure_is_reported_instead_of_claiming_logs_were_deleted(self):
        with self.assertRaises(subprocess.CalledProcessError) as raised:
            self.run_provider(
                "return await provider.run({prompt:'ask',resume:'parent',fork:true});",
                extra_env={"FAKE_DELETE_FAIL": "1"})
        self.assertIn("削除できませんでした: fork-1", raised.exception.stderr)

    def test_failed_unload_blocks_further_turns_but_allows_cleanup(self):
        results, messages = self.run_provider("""
const first=await provider.run({prompt:'ask',resume:'parent',fork:true});
const next=await provider.run({prompt:'must not run',resume:first.sessionId});
return [first,next];
""", timeout=0.15, extra_env={"FAKE_KEEP_LOADED": "1"})
        self.assertTrue(all(not result["ok"] for result in results))
        self.assertIn("アンロード", results[0]["error"])
        self.assertEqual(len(self.requests(messages, "turn/start")), 1)
        self.assertEqual(self.requests(messages, "thread/delete"), [{"threadId": "fork-1"}])

    def test_http_ask_followup_sql_return_and_cleanup(self):
        server_file = PROVIDER.parent / "server.js"
        work = self.root / "work"
        work.mkdir()
        (work / "main.md").write_text("# Main\nA fixture explanation.\n")
        process = subprocess.Popen(
            ["node", str(server_file), "--provider", "codex", "--dir", str(work),
             "--session", "main-id", "--cwd", str(self.root), "--no-open"],
            cwd=self.root, env={**os.environ, "FAKE_CODEX_LOG": str(self.log),
                                "UNDERSTAND_CODEX_BIN": str(self.fake)},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 3
            while not (work / "url.txt").exists():
                if process.poll() is not None:
                    self.fail("HTTP server exited: " + process.stderr.read())
                if time.monotonic() > deadline:
                    self.fail("HTTP server did not start")
                time.sleep(0.02)
            parsed = urllib.parse.urlsplit((work / "url.txt").read_text().strip())
            origin = f"{parsed.scheme}://{parsed.netloc}"
            token = urllib.parse.parse_qs(parsed.query)["t"][0]

            def request(endpoint, body=None):
                data = json.dumps(body).encode() if body is not None else None
                req = urllib.request.Request(origin + endpoint, data=data, headers={
                    "Content-Type": "application/json", "X-Understand-Token": token})
                with urllib.request.urlopen(req, timeout=4) as response:
                    return json.load(response)

            init = request("/api/init")
            self.assertTrue(init["hasSession"])
            self.assertFalse(init["autoRun"])
            first = request("/api/ask", {"action": "question", "anchor": "fixture", "question": "What?"})
            self.assertTrue(first["ok"])
            self.assertEqual(first["sessionId"], "fork-1")
            follow = request("/api/ask", {"sessionId": first["sessionId"],
                                         "continueSession": True, "followUp": "Why?"})
            self.assertTrue(follow["ok"])
            sql = request("/api/runsql", {"sessionId": first["sessionId"], "sql": "SELECT 1"})
            self.assertTrue(sql["ok"])
            returned = request("/api/return", {"text": "I understand.", "confusions": []})
            self.assertTrue(returned["ok"])
            process.wait(timeout=3)
            self.assertEqual(process.returncode, 0)
            self.assertEqual((work / "return.md").read_text(), "I understand.\n")
            messages = [json.loads(line) for line in self.log.read_text().splitlines()]
            self.assertEqual(self.requests(messages, "thread/fork")[0]["threadId"], "main-id")
            reloads = self.requests(messages, "thread/resume")
            self.assertEqual([r["config"]["features"]["shell_tool"] for r in reloads], [False, True])
            self.assertEqual(self.requests(messages, "thread/delete"), [{"threadId": "fork-1"}])
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=3)
            process.stdout.close()
            process.stderr.close()


if __name__ == "__main__":
    unittest.main()
