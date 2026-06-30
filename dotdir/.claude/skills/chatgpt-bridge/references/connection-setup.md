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

ユーザーの Claude Code 設定（例: `~/.claude/settings.json`。dotfiles では `dotdir/.claude/settings.json`）の `mcpServers` に以下を追加:

```json
{
  "mcpServers": {
    "chrome-cdp": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    }
  }
}
```

追加後、**Claude Code の再起動**で `mcp__chrome-cdp__*` ツール群が有効になる。

> 既存の `mcp__plugin_ecc_chrome-devtools__*`（自前 Chrome 起動）と混同しないこと。本スキルは **:9222 に attach した方**（上記 `chrome-cdp`）のツールを使う。

## 4. ヘルスチェック（毎回・操作前）

```bash
curl -sf http://127.0.0.1:9222/json/version >/dev/null && echo "UP" || echo "DOWN"
```

- `DOWN` → 手順 1 を実行。
- `UP` だがログインしていない場合は、MCP で `https://chatgpt.com` を開き、ログイン UI（"Log in" ボタン等）が出ていないかを `evaluate_script` で確認する。ログイン UI が見えたら手順 2 をユーザーに促す。

ChatGPT ログイン判定の例（MCP `evaluate_script`、attach 後）:

```js
() => {
  const loggedOut = !!document.querySelector('[data-testid="login-button"], a[href*="auth/login"]');
  const composer = !!document.querySelector('#prompt-textarea');
  return { loggedOut, composer };  // composer:true かつ loggedOut:false ならログイン済み
}
```

（`login-button` のセレクタは UNCONFIRMED。`composer` の有無を主判定にし、ログイン UI 検出は補助とする。）

## トラブルシュート

- ポートが上がらない: 既存のデバッグ Chrome が別ポートにいないか、`CHATGPT_BRIDGE_CHROME` のパスが正しいか確認。
- `--browser-url` で attach できない: `curl` で :9222 が応答するか先に確認。応答するのに attach 失敗なら chrome-devtools-mcp のバージョン（1.4.0+ 想定）を確認。
