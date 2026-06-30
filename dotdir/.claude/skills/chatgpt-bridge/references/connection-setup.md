# 接続セットアップ

Chrome 上の ChatGPT（Pro ログイン済み）に chrome-devtools MCP を attach するための一度きりのセットアップと、毎回のヘルスチェック手順。

## なぜ専用プロファイルか（Chrome 136 制約）

Chrome 136+（2025-04 stable）は、**デフォルトの user-data-dir で起動した Chrome の `--remote-debugging-port` を無視**する（cookie 窃取対策）。そのため remote-debugging には**非デフォルトの専用プロファイル**が必須。同一 ChatGPT Pro アカウントに一度ログインすれば、その専用プロファイルにセッションが永続し、普段の Chrome とは別プロセスで共存できる。
（出典: developer.chrome.com/blog/remote-debugging-port, 2025-03-17）

## 1. デバッグ Chrome を起動

```bash
bash ~/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh
```

- 既に :9222 が up なら冪等にスキップ。
- 環境変数で上書き可: `CHATGPT_BRIDGE_PORT` / `CHATGPT_BRIDGE_PROFILE` / `CHATGPT_BRIDGE_CHROME`。

## 2. 初回のみ ChatGPT にログイン

開いた Chrome 窓で `https://chatgpt.com` を開き、Pro アカウントでログインする。プロファイル `~/.cache/chatgpt-bridge-chrome` に永続するので 2 回目以降は不要。

## 3. MCP サーバを attach 設定（一度きり・要再起動）

既定の ecc `chrome-devtools` MCP は**自前の Chrome を起動**してしまうため、ChatGPT ログイン済みセッションには使えない。**`--browser-url` で起動済み Chrome に attach する MCP サーバ**を別途追加する。

> **重要（落とし穴）**: MCP サーバは **`settings.json` には書けない**。Claude Code の settings.json スキーマは `mcpServers` フィールドを受け付けず、バリデーションエラーで拒否される。ユーザー MCP は **`~/.claude.json`**（settings.json とは別ファイル）か プロジェクト **`.mcp.json`** に置く。手編集より公式コマンド `claude mcp add` が安全。

公式コマンドで user スコープに登録（推奨）:

```bash
claude mcp add chrome-cdp --scope user -- npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
# 確認（✔ Connected が出れば :9222 への attach 成功）:
claude mcp list
```

これは `~/.claude.json` の user スコープに登録される。登録後、**Claude Code の再起動**で `mcp__chrome-cdp__*` ツール群が有効になる（同一セッション内では有効化されない）。

> 既存の `mcp__plugin_ecc_chrome-devtools__*`（自前 Chrome 起動・ChatGPT 未ログイン）と混同しないこと。本スキルは **:9222 に attach した方**（上記 `chrome-cdp`）のツールを使う。

## 4. ヘルスチェック（毎回・操作前）

```bash
curl -sf http://127.0.0.1:9222/json/version >/dev/null && echo "UP" || echo "DOWN"
```

- `DOWN` → 手順 1 を実行。
- `UP` でも attach 直後は **bot 検証画面**（タイトル「しばらくお待ちください…」/「Just a moment」）や読み込み途中のことがある。**ページが settle するまで待ってから**判定する（早すぎる観測は誤判定の元）。

ChatGPT ログイン判定（MCP `evaluate_script`、attach 後）。**`#prompt-textarea` の有無だけでは判定できない**——ChatGPT はログアウト時のランディングでも composer を表示するため。`ログイン`/`Log in` ボタンの有無を主判定にする:

```js
async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  let s = {};
  for (let i = 0; i < 24; i++) {                 // 最大 ~12s、settle 待ち
    const interstitial = /お待ちください|just a moment|verifying/i.test(document.title);
    const composer = !!document.querySelector('#prompt-textarea');
    const authBtns = [...document.querySelectorAll('button,a')]
      .map(e => (e.textContent || '').trim())
      .filter(t => /^(log ?in|ログイン|sign ?up|無料で登録)$/i.test(t)).length;
    const sidebarChats = document.querySelectorAll('nav a[href^="/c/"]').length;
    s = { interstitial, composer, authBtns, sidebarChats,
          loggedIn: !interstitial && composer && authBtns === 0 };
    if (!interstitial && composer) break;
    await sleep(500);
  }
  return s;
}
```

判定ルール:
- `interstitial:true` のまま → bot 検証で停止。**突破は禁止**。ユーザーに当該 Chrome 窓での手動操作を促す。
- `authBtns > 0` → 未ログイン。手順 2（ログイン）をユーザーに促す（資格情報入力は行わない）。
- `loggedIn:true`（composer あり・auth ボタン無し）→ 送信可。`sidebarChats > 0` はログイン済みの追加根拠。

## トラブルシュート

- ポートが上がらない: 既存のデバッグ Chrome が別ポートにいないか、`CHATGPT_BRIDGE_CHROME` のパスが正しいか確認。
- `--browser-url` で attach できない: `curl` で :9222 が応答するか先に確認。応答するのに attach 失敗なら chrome-devtools-mcp のバージョン（1.4.0+ 想定）を確認。
