# chatgpt-bridge Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chrome 上の ChatGPT（Pro ログイン済み）を Claude Code から駆動し、新規/既存チャットを名前で選んで質問を投げ、回答を取得・集約する Claude スキル `chatgpt-bridge` を作る。

**Architecture:** `medical-ai-compliance` と同型のルータースキル。`SKILL.md` がモード（Single=単発セカンドオピニオン / Multi=複数チャット振り分け統合）を判定し、`references/`（接続・チャット選択・送信&取得の手順）と `assets/`（Chrome起動スクリプト・統合レポートテンプレート）へ誘導する。ブラウザ操作は chrome-devtools MCP を `--browser-url` で remote-debugging 起動済み Chrome に attach して行う。

**Tech Stack:** Claude Code skill（Markdown + frontmatter）、chrome-devtools-mcp 1.4.0（`evaluate_script`/`take_snapshot`/`type_text` 等）、Chrome remote debugging（CDP, port 9222）、bash（起動スクリプト）、macOS。

## テスト戦略（この成果物特有の適応）

このスキルは Markdown ドキュメント群 + 1本の shell script で構成される。pytest 型の単体テストが成立するのは shell script のみ。したがって本プランの「テスト」は対象ごとに以下へ適応する（これは手抜きではなく、prose/config に偽のユニットテストを被せない判断）:

- **shell script** → 振る舞いテスト（ポート down 時に起動して endpoint が上がる / up 時は冪等にスキップ）＋ `shellcheck`
- **SKILL.md** → frontmatter の YAML 妥当性 + 必須キー（name, description）検証
- **全ファイル横断** → 参照リンク先の実在検証
- **スキル全体** → ライブ E2E 検証（接続→質問→取得を実機で証明。MCP 再設定 + 再起動 + ChatGPT ログイン後に実施）

## Global Constraints

各タスクの要件は暗黙にこのセクションを含む。値は spec / 調査結果から逐語転記。

- スキル配置: `dotdir/.claude/skills/chatgpt-bridge/`（`make link` 対象。`$HOME/.claude/skills/` にリンクされる）
- 言語: 日本語（技術用語・コード識別子は英語のまま）
- chrome-devtools-mcp: **1.4.0**（Node `^20.19.0 || ^22.12.0 || >=23`）。attach フラグは **`--browser-url=http://127.0.0.1:9222`**（camelCase 別名 `--browserUrl`）
- Chrome 136+ は **デフォルト user-data-dir での remote-debugging を無効化**。必ず **非デフォルト `--user-data-dir`** を渡す（公式: developer.chrome.com/blog/remote-debugging-port, 2025-03-17）
- デバッグプロファイル: `$HOME/.cache/chatgpt-bridge-chrome`、デバッグポート: `9222`、ヘルスチェック: `curl -sf http://127.0.0.1:9222/json/version`
- composer は `#prompt-textarea`（**contenteditable ProseMirror `<div>`**、textarea ではない）。入力は MCP `type_text`（ネイティブ打鍵）で行い、contenteditable に `fill` は使わない
- 完了検知は **二重シグナル**: `button[data-testid="stop-button"]` 消失 **AND** `button[data-testid="copy-turn-action-button"]` 出現。~300ms ポーリング、**2連続 false** でデバウンス、タイムアウト上限を設ける
- セレクタは **実行時プローブ必須**（`count > 0` を確認してから操作）、ヒットした fallback をログし、**stale 前提では進めず fail-loud**
- 安全: 5問超の送信前に確認 / 資格情報を扱わない（ログイン自動化なし）/ 回答は検証済み事実扱いせず出典明示 / 生成記録は人間レビュー
- 出力: インライン。長文・複数回答時は Markdown 保存（`scratchpad` か `docs/`）しパス提示

## File Structure

```
dotdir/.claude/skills/chatgpt-bridge/
├── SKILL.md                      # ルーター: frontmatter / モード判定 / 5ステップフロー / 安全原則 / バッチ指定 / References
├── references/
│   ├── connection-setup.md       # Chrome136注記 / 起動スクリプト誘導 / 初回ログイン / MCP --browser-url 設定 / ヘルスチェック / どのMCPサーバを使うか
│   ├── chat-targeting.md         # 新規チャット / 既存名検索（enumerateChats）/ 完全・部分一致 / 無一致・複数一致 / 仮想化スクロール
│   └── ask-and-capture.md        # composer入力 / 送信 / 完了検知(isStreaming) / 抽出(getLastAssistantText) / エラー処理
└── assets/
    ├── launch-chrome-debug.sh    # 冪等な remote-debugging Chrome 起動（macOS）
    └── aggregation-report.md     # Multiモード統合レポートのテンプレート
```

参照グラフ: `SKILL.md` → 全 references/assets。`connection-setup.md` → `assets/launch-chrome-debug.sh`。各 reference は独立して読めること。

---

## Task 1: Chrome 起動スクリプト（asset）

最初に作る。唯一の実コードで振る舞いテストが成立する。後続の `connection-setup.md` がこれを参照する。

**Files:**
- Create: `dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh`

**Interfaces:**
- Produces: 実行すると port 9222 で remote-debugging Chrome（profile `$HOME/.cache/chatgpt-bridge-chrome`）を起動。既に up なら何もせず終了 0。標準出力に状態を 1 行出す。

- [ ] **Step 1: スクリプトを作成**

`dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh`:

```bash
#!/usr/bin/env bash
# launch-chrome-debug.sh — chatgpt-bridge skill 用に remote-debugging Chrome を冪等起動する。
# Chrome 136+ はデフォルト profile での remote-debugging を無効化するため、専用 --user-data-dir を使う。
set -euo pipefail

PORT="${CHATGPT_BRIDGE_PORT:-9222}"
PROFILE_DIR="${CHATGPT_BRIDGE_PROFILE:-$HOME/.cache/chatgpt-bridge-chrome}"
CHROME_BIN="${CHATGPT_BRIDGE_CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
HEALTH_URL="http://127.0.0.1:${PORT}/json/version"

# 既に up なら冪等にスキップ
if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
  echo "[chatgpt-bridge] Chrome debug endpoint already up on :${PORT}"
  exit 0
fi

if [ ! -x "$CHROME_BIN" ]; then
  echo "[chatgpt-bridge] ERROR: Chrome binary not found at: $CHROME_BIN" >&2
  echo "[chatgpt-bridge] Set CHATGPT_BRIDGE_CHROME to your Chrome path." >&2
  exit 1
fi

mkdir -p "$PROFILE_DIR"

echo "[chatgpt-bridge] launching Chrome (port ${PORT}, profile ${PROFILE_DIR})"
"$CHROME_BIN" \
  --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check \
  >/dev/null 2>&1 &

# 起動待ち（最大 ~10s）
for _ in $(seq 1 20); do
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    echo "[chatgpt-bridge] ready on :${PORT}"
    echo "[chatgpt-bridge] 初回は開いた Chrome で https://chatgpt.com にログインしてください（profile に永続）。"
    exit 0
  fi
  sleep 0.5
done

echo "[chatgpt-bridge] ERROR: endpoint did not come up within timeout on :${PORT}" >&2
exit 1
```

- [ ] **Step 2: 実行権限を付与**

Run: `chmod +x dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh`
Expected: 終了コード 0（出力なし）

- [ ] **Step 3: 静的解析（shellcheck があれば）**

Run: `command -v shellcheck >/dev/null 2>&1 && shellcheck dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh || echo "shellcheck not installed — skip"`
Expected: 警告なし、または "shellcheck not installed — skip"。警告が出たら修正する。

- [ ] **Step 4: 振る舞いテスト（ポート down → 起動して up）**

Run: `bash dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh && curl -sf http://127.0.0.1:9222/json/version | head -c 80`
Expected: `[chatgpt-bridge] launching Chrome ...` → `[chatgpt-bridge] ready on :9222` と続き、最後に `{"Browser":"Chrome/...` の JSON 断片が出る。
（注: これは実機で Chrome を起動する副作用がある。Chrome 未インストール環境ではこの Step をスキップし、Step 3 の静的解析までで可とする。）

- [ ] **Step 5: 冪等テスト（既に up → スキップ）**

Run: `bash dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh`
Expected: `[chatgpt-bridge] Chrome debug endpoint already up on :9222`（新たな起動をしない）。

- [ ] **Step 6: Commit**

```bash
git add -f dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh
git commit -m "feat: add chatgpt-bridge Chrome debug launch script"
```

---

## Task 2: connection-setup.md（接続セットアップ reference）

**Files:**
- Create: `dotdir/.claude/skills/chatgpt-bridge/references/connection-setup.md`

**Interfaces:**
- Consumes: `assets/launch-chrome-debug.sh`（Task 1）
- Produces: 「ヘルスチェック手順」「MCP サーバ設定 JSON」「初回ログイン手順」。`SKILL.md`（Task 6）の Step1 がここを指す。

- [ ] **Step 1: reference を作成**

`dotdir/.claude/skills/chatgpt-bridge/references/connection-setup.md`:

````markdown
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
````

- [ ] **Step 2: リンク先の実在を検証**

Run: `test -f dotdir/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh && echo OK`
Expected: `OK`（参照している起動スクリプトが存在する）

- [ ] **Step 3: Commit**

```bash
git add -f dotdir/.claude/skills/chatgpt-bridge/references/connection-setup.md
git commit -m "feat: add chatgpt-bridge connection-setup reference"
```

---

## Task 3: chat-targeting.md（チャット選択 reference）

**Files:**
- Create: `dotdir/.claude/skills/chatgpt-bridge/references/chat-targeting.md`

**Interfaces:**
- Produces: 「新規チャット作成」「既存チャットを名前で選択」の手順と JS スニペット。`SKILL.md` Step3 がここを指す。

- [ ] **Step 1: reference を作成**

`dotdir/.claude/skills/chatgpt-bridge/references/chat-targeting.md`:

````markdown
# チャット選択（新規 / 既存名）

質問先チャットを解決する。全セレクタは**実行時にプローブ**（count を確認）し、ヒットした方法をログする。難読化 testid は A/B で変わりうるため fallback を常備。

## 新規チャット

最も堅牢なのは**直接 URL 遷移**:

- MCP: `navigate_page` で `https://chatgpt.com/`（type: "url"）。新規の空チャットになる。

ボタン経由が必要なら（既にチャット画面にいて遷移を避けたい等）:

- 第一候補: `button[data-testid="create-new-chat-button"]`
- fallback: `button:has-text("New chat")` / `[data-testid="new-chat-button"]`

## 既存チャットを名前で選択

サイドバーのチャットを列挙し、タイトルで照合する。`evaluate_script` で実行:

```js
() => {
  return [...document.querySelectorAll('nav a[href^="/c/"]')].map(a => ({
    title: (a.getAttribute('title') || a.textContent || '').trim(),
    href:  a.getAttribute('href'),   // 例 "/c/abc123..."
  })).filter(c => c.title);
}
```

照合ロジック（Claude 側で実施）:

1. **完全一致**を優先（`title === wanted`）。
2. 無ければ**部分一致**（`title.includes(wanted)` / 正規化して比較）。
3. **無一致** → ユーザーに「該当チャットが無い。新規作成しますか？」と確認（勝手に新規化しない）。
4. **複数一致** → 候補（title + href）を提示してユーザーに選ばせる。

選択した chat への遷移（href が分かれば直接遷移が確実）:

```js
(href) => { location.assign(href); return location.pathname; }
```

（MCP では `evaluate_script` に href を args で渡すか、`navigate_page` で `https://chatgpt.com{href}` へ遷移。）

## 仮想化の注意

サイドバーは**仮想化**されており、画面外のチャットは DOM に存在しない。列挙で見つからない場合:

1. サイドバーのスクロールコンテナを `evaluate_script` でスクロール（`el.scrollTop = el.scrollHeight`）して再列挙、または
2. 検索 UI（あれば）でタイトル検索、または
3. 既知の href があれば `https://chatgpt.com/c/{id}` へ直接遷移。

見つからないまま放置せず、上記いずれかを試し、それでも無ければ「無一致」として扱う。
````

- [ ] **Step 2: 構造検証（コードフェンスの対応）**

Run: `awk '/^```/{c++} END{print (c%2==0)?"fences-balanced":"FENCES-UNBALANCED"}' dotdir/.claude/skills/chatgpt-bridge/references/chat-targeting.md`
Expected: `fences-balanced`

- [ ] **Step 3: Commit**

```bash
git add -f dotdir/.claude/skills/chatgpt-bridge/references/chat-targeting.md
git commit -m "feat: add chatgpt-bridge chat-targeting reference"
```

---

## Task 4: ask-and-capture.md（送信&取得 reference）

**Files:**
- Create: `dotdir/.claude/skills/chatgpt-bridge/references/ask-and-capture.md`

**Interfaces:**
- Produces: 「質問入力→送信→完了検知→抽出」の手順と JS スニペット。`SKILL.md` Step3 がここを指す。

- [ ] **Step 1: reference を作成**

`dotdir/.claude/skills/chatgpt-bridge/references/ask-and-capture.md`:

````markdown
# 質問送信と回答取得

1 つのチャット画面で、質問を送り、ストリーミング完了を検知し、最終回答テキストを抽出する。

## 1. 質問を入力

composer は `#prompt-textarea`（**contenteditable ProseMirror div**、textarea ではない）。`fill` は使わず**ネイティブ打鍵**で入力する:

- MCP: `take_snapshot` → `#prompt-textarea` の uid を得る → `click`（focus）→ `type_text`（text=質問文）。
- `type_text` は実キーイベントを発火するので ProseMirror が正しく反応し、`input` イベントで send ボタンが有効化される。

`evaluate_script` で直接入れる場合の代替（ネイティブ打鍵が使えないとき）:

```js
(text) => {
  const el = document.querySelector('#prompt-textarea');
  el.focus();
  document.execCommand('selectAll', false);
  document.execCommand('insertText', false, text);  // PM が期待する beforeinput/input を発火
  return el.innerText.length;
}
```

## 2. 送信

- 第一候補: `button[data-testid="send-button"]` を `click`（テキスト入力で有効化済みのはず）。
- fallback: composer で Enter（MCP `type_text` の submitKey="Enter"、または `press_key` "Enter"）。
- 送信前に send ボタンが**有効**か確認（disabled のままなら `input` 未発火 → 入力やり直し）。

## 3. 完了検知（二重シグナル + デバウンス）

単一シグナルは危険。**stop ボタン消失 AND finished-action 出現**の両方で判定する:

```js
() => {
  if (document.querySelector('button[data-testid="stop-button"]')) return true; // 生成中
  const turns = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = turns[turns.length - 1];
  if (!last) return true;  // まだ assistant ターンが無い → 未完了扱い
  const root = last.closest('article') || last;
  const done = root.querySelector(
    'button[data-testid="copy-turn-action-button"], button[data-testid="good-response-turn-action-button"]'
  );
  return !done;  // finished-action がまだ無ければ生成中
}
```

ポーリング手順（Claude 側）:

1. 送信直後から ~300ms 間隔で上記 `evaluate_script` を呼ぶ。
2. `false`（=完了）を**2 連続**で得たら完了とみなす（トークン間の隙間で誤検知しないため）。
3. **タイムアウト上限**（例 180s）。超えたら「生成が完了しない」とユーザーに報告（勝手に再送しない）。
4. MCP `wait_for`（text 配列の出現待ち）は補助に使えるが、回答本文の語は事前に分からないので主判定は上記ポーリングにする。

## 4. 最終回答を抽出

```js
() => {
  const nodes = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = nodes[nodes.length - 1];
  if (!last) return null;
  const md = last.querySelector('.markdown') || last;  // .markdown = 整形済み本文
  return md.innerText.trim();
}
```

- `null` が返る/空文字 → セレクタ不一致を疑う。`take_snapshot` で assistant ターンの実構造を確認し、fallback（`article:last-of-type` の innerText から "ChatGPT said:" 接頭辞を除去）に切替。
- 切替時はどの fallback を使ったかをユーザーに報告（セレクタ drift の早期発見）。

## エラー処理

- **レート制限 / 利用上限**: 画面に上限メッセージが出たら抽出は中止し、ユーザーに報告（自動リトライ禁止）。
- **生成停止ボタンが消えない**: タイムアウトで打ち切り報告。
- **セレクタ全滅**: `stop-button` も `copy-turn-action-button` も assistant コンテナも見つからない → DOM 構造が変わった可能性。fail-loud（推測で進めない）。`take_snapshot` 結果を添えてユーザーに調査を促す。
````

- [ ] **Step 2: 構造検証（コードフェンスの対応）**

Run: `awk '/^```/{c++} END{print (c%2==0)?"fences-balanced":"FENCES-UNBALANCED"}' dotdir/.claude/skills/chatgpt-bridge/references/ask-and-capture.md`
Expected: `fences-balanced`

- [ ] **Step 3: Commit**

```bash
git add -f dotdir/.claude/skills/chatgpt-bridge/references/ask-and-capture.md
git commit -m "feat: add chatgpt-bridge ask-and-capture reference"
```

---

## Task 5: aggregation-report.md（統合レポート template asset）

**Files:**
- Create: `dotdir/.claude/skills/chatgpt-bridge/assets/aggregation-report.md`

**Interfaces:**
- Produces: Multi モードの出力テンプレート。`SKILL.md` Step4/5 がここを指す。

- [ ] **Step 1: template を作成**

`dotdir/.claude/skills/chatgpt-bridge/assets/aggregation-report.md`:

````markdown
# ChatGPT 集約レポート — {TOPIC}

- **日時**: {YYYY-MM-DD HH:MM}
- **モード**: Multi（{N} チャット / {M} 質問）
- **出典**: 下記各チャットの ChatGPT 回答（ブラウザ UI 経由）

> ⚠️ 以下は ChatGPT の回答であり**検証済みの事実ではない**。重要判断は一次情報で裏取りすること。

## 個別回答

### 1. {chat-name-1}
- **質問**: {question-1}
- **回答（要点）**:
  - {point}
- **回答（全文）**: {full-answer-or-omitted}

### 2. {chat-name-2}
- **質問**: {question-2}
- **回答（要点）**:
  - {point}

## 統合

### 一致点
- {agreement}

### 相違点 / 対立
- {chat-A} は {X}、{chat-B} は {Y}（理由: {...}）

### 推奨 / 結論
- {synthesis-and-recommendation}

### 未解決 / 要追加確認
- {open-question}
````

- [ ] **Step 2: 構造検証（コードフェンスの対応）**

Run: `awk '/^```/{c++} END{print (c%2==0)?"fences-balanced":"FENCES-UNBALANCED"}' dotdir/.claude/skills/chatgpt-bridge/assets/aggregation-report.md`
Expected: `fences-balanced`

- [ ] **Step 3: Commit**

```bash
git add -f dotdir/.claude/skills/chatgpt-bridge/assets/aggregation-report.md
git commit -m "feat: add chatgpt-bridge aggregation report template"
```

---

## Task 6: SKILL.md（ルーター本体）

全 references/assets を束ねる入口。frontmatter の妥当性とリンク健全性を検証する。

**Files:**
- Create: `dotdir/.claude/skills/chatgpt-bridge/SKILL.md`

**Interfaces:**
- Consumes: `references/connection-setup.md`, `references/chat-targeting.md`, `references/ask-and-capture.md`, `assets/launch-chrome-debug.sh`, `assets/aggregation-report.md`（Tasks 1–5）

- [ ] **Step 1: SKILL.md を作成**

`dotdir/.claude/skills/chatgpt-bridge/SKILL.md`:

````markdown
---
name: chatgpt-bridge
description: Chrome 上の ChatGPT（Pro ログイン済み）を Claude Code から駆動し、質問を投げて回答を取得・集約する。新規/既存チャットを名前で選んで質問でき、複数チャットへ振り分けて統合する Multi モードと、単発セカンドオピニオンの Single モードに対応。トリガー：「ChatGPTに聞いて」「ChatGPTで集約」「ブラウザのChatGPT」「ChatGPT Proで質問」「ChatGPTにセカンドオピニオン」「ChatGPTの〇〇チャットに」「ask ChatGPT (browser)」「ChatGPT fan-out」。Do NOT trigger for: codex/agy CLI によるセカンドオピニオン（別ツール）、ChatGPT API 利用、Claude/Gemini 等その他 LLM への質問、ChatGPT の画像生成・ファイルアップロード。
---

# ChatGPT Bridge

Chrome 上の ChatGPT（Pro）を chrome-devtools MCP（remote-debugging attach）で駆動し、質問→回答取得→集約を行うルータースキル。質問先チャットを**新規 or 既存（名前指定）**で選べる。

## モード判定

| 条件 | モード | 出力 |
|---|---|---|
| 質問 1 件 / 対象チャット 1 つ | **Single** | インライン要約 |
| 質問複数 / 対象チャット複数 | **Multi** | 統合レポート（Markdown 保存） |

曖昧なときはユーザーに確認する。

## 5 ステップフロー

### Step 1: 接続ヘルスチェック
`references/connection-setup.md` に従い、:9222 の Chrome 稼働と ChatGPT ログインを確認。未起動なら `assets/launch-chrome-debug.sh` を実行、未ログイン/未設定ならユーザーを誘導（MCP `--browser-url` 設定は要再起動）。

### Step 2: モード判定
質問数・対象チャット数から Single / Multi を決める（上表）。バッチ指定は下記フォーマット参照。

### Step 3: 各 (質問, 対象) を処理
- チャット解決: `references/chat-targeting.md`（新規 / 既存名検索・無一致/複数一致処理）
- 送信&取得: `references/ask-and-capture.md`（ProseMirror 入力 / 二重シグナル完了検知 / 抽出）
- 必ず MCP は **:9222 attach 済みサーバ**（例 `mcp__chrome-cdp__*`）を使う。`take_snapshot` で uid を取り、操作前にセレクタを実行時プローブ。

### Step 4: 集約
- Single: 質問と回答を要約（要点 + 必要なら全文）。
- Multi: `assets/aggregation-report.md` テンプレートで一致点・相違点・推奨を統合。

### Step 5: 出力
- インライン表示。長文・複数回答時は Markdown 保存（`scratchpad` か `docs/`）しパス提示。

## バッチ指定フォーマット（Multi）

ユーザー指示を以下の構造に正規化してから実行:

```
- chat: "法務"      | mode: existing | question: "..."
- chat: "技術検討"  | mode: new      | question: "..."
```

`mode: existing` は名前一致でサイドバー検索、`mode: new` は新規チャット作成。

## 安全原則

- **実アカウント操作**: ユーザーの実 ChatGPT Pro を駆動する。**5 問超の一括送信前に確認**。利用上限・レート制限に配慮し、上限到達時は自動リトライしない。
- **資格情報不保持**: ログイン自動化はしない。回答の可視テキストのみ読む。セッションは専用プロファイルにのみ残る。
- **事実確認**: ChatGPT 回答は検証済み事実として扱わない。集約には出典（どのチャット由来か）を明示し、誤りうる旨を付記。
- **セレクタ脆弱性**: 難読化 testid は変わりうる。実行時プローブ + fallback、見つからなければ **fail-loud**（推測で進めない）。
- **人間レビュー**: 集約レポートを正式利用する前に内容を確認すること。

## References

| ファイル | 内容 |
|---|---|
| [references/connection-setup.md](references/connection-setup.md) | Chrome 起動 / MCP `--browser-url` 設定 / ヘルスチェック / ログイン |
| [references/chat-targeting.md](references/chat-targeting.md) | 新規 / 既存名検索・無一致・複数一致・仮想化 |
| [references/ask-and-capture.md](references/ask-and-capture.md) | 入力 / 送信 / 完了検知 / 抽出 / エラー処理 |
| [assets/launch-chrome-debug.sh](assets/launch-chrome-debug.sh) | remote-debugging Chrome の冪等起動 |
| [assets/aggregation-report.md](assets/aggregation-report.md) | Multi モード統合レポートのテンプレート |
````

- [ ] **Step 2: frontmatter の妥当性検証**

Run:
```bash
python3 -c "
import sys, re
t = open('dotdir/.claude/skills/chatgpt-bridge/SKILL.md', encoding='utf-8').read()
m = re.match(r'^---\n(.*?)\n---\n', t, re.S)
assert m, 'no frontmatter block'
fm = m.group(1)
assert re.search(r'^name:\s*chatgpt-bridge\s*$', fm, re.M), 'name missing/wrong'
assert re.search(r'^description:\s*\S', fm, re.M), 'description missing'
print('frontmatter-ok')
"
```
Expected: `frontmatter-ok`（YAML 構造があり name/description が揃う）

- [ ] **Step 3: 内部リンク先の実在検証**

Run:
```bash
cd dotdir/.claude/skills/chatgpt-bridge && \
for f in references/connection-setup.md references/chat-targeting.md references/ask-and-capture.md assets/launch-chrome-debug.sh assets/aggregation-report.md; do
  test -f "$f" && echo "OK $f" || echo "MISSING $f"
done
```
Expected: 5 行すべて `OK ...`（`MISSING` が無い）

- [ ] **Step 4: Commit**

```bash
git add -f dotdir/.claude/skills/chatgpt-bridge/SKILL.md
git commit -m "feat: add chatgpt-bridge SKILL.md router"
```

---

## Task 7: ライブ E2E 検証（MCP 再設定 + 再起動 + ログイン後）

スキルの振る舞いを実機で証明する。**前提**: Task 6 までで全ファイルが揃い、`connection-setup.md` 手順で (a) デバッグ Chrome 起動・ChatGPT ログイン済み、(b) `chrome-cdp` MCP サーバ追加 + Claude Code 再起動済み。この検証は再起動を伴うため、ビルドと同一セッションでは完結しない場合がある（その場合は再起動後の新セッションで実施）。

**Files:**
- 変更なし（検証のみ）。必要なら結果を `scratchpad` に記録。

- [ ] **Step 1: 接続確認**

Run: `curl -sf http://127.0.0.1:9222/json/version >/dev/null && echo UP || echo DOWN`
Expected: `UP`。`DOWN` なら `bash ~/.claude/skills/chatgpt-bridge/assets/launch-chrome-debug.sh`。

- [ ] **Step 2: MCP attach + ログイン確認**

操作: `chrome-cdp` MCP で `new_page`（または `navigate_page`）`https://chatgpt.com/` → `evaluate_script` で `connection-setup.md` のログイン判定スニペットを実行。
Expected: `{ loggedOut:false, composer:true }`。`composer:false` ならログインをユーザーに促して中断。

- [ ] **Step 3: Single モード — 新規チャットに質問**

操作: `navigate_page` `https://chatgpt.com/` → `take_snapshot` → `#prompt-textarea` を focus → `type_text` で `"2+2 は？一語で答えて"` → `send-button` click → `ask-and-capture.md` の完了検知ポーリング → 抽出スニペット実行。
Expected: 抽出テキストに `4` を含む。完了検知が（ハングや即時誤完了でなく）数秒で `false` 2 連続に到達する。

- [ ] **Step 4: 既存チャット選択の確認**

操作: `chat-targeting.md` の `enumerateChats` を `evaluate_script` で実行。
Expected: `[{title, href}, ...]` が 1 件以上返る（Step 3 で作ったチャットが含まれる）。title の一部でルックアップ → href 一致を確認。0 件なら仮想化スクロール後に再実行。

- [ ] **Step 5: セレクタ drift 記録**

各操作で**実際にヒットしたセレクタ / 使った fallback**を確認し、Global Constraints の値と差異があれば該当 reference を更新する（例: `stop-button` が別 testid なら `ask-and-capture.md` を修正してコミット）。差異なしなら記録のみ。
Expected: drift があれば該当ファイルを修正してコミット。なければ「drift なし」を記録。

- [ ] **Step 6: 検証結果の記録（任意）**

E2E の結果（成功/失敗、ヒットしたセレクタ、所要時間）を `scratchpad` に保存し、ユーザーへ要約報告。スキルが受け入れ基準を満たすことを明示。

---

## Self-Review

**1. Spec coverage（spec の各要件 → タスク対応）:**
- 既存 Chrome 接続（Chrome136 制約対応）→ Task 1（起動スクリプト）+ Task 2（接続 reference）
- ヘルスチェック → Task 2 Step1 + Task 7 Step1-2
- 新規/既存名チャット選択（無一致・複数一致）→ Task 3
- 送信→完了検知→抽出（二重シグナル・fallback）→ Task 4
- Single/Multi 2 モード集約 → Task 5（template）+ Task 6（SKILL.md ルーター）
- インライン + 必要時ファイル出力 → Task 6 Step5
- 安全原則（5問超確認・出典明示・資格情報不保持）→ Task 6（SKILL.md 安全原則節）
- `dotdir/.claude/skills/chatgpt-bridge/` 配置・make link 対象 → 全タスクのパス
- 実装フェーズ要検証（MCP フラグ・現行セレクタ・Chrome136）→ 事前調査で確定済み、値は Global Constraints に転記
- ギャップ: なし。

**2. Placeholder scan:** `{TOPIC}` 等は aggregation-report.md の**テンプレート変数**であり成果物の placeholder ではない（テンプレートとして妥当）。プラン手順内に TBD/TODO/「適切に処理」等の空文言なし。

**3. Type consistency:** JS 関数名・セレクタはタスク間で一貫（`#prompt-textarea`, `button[data-testid="send-button"]`, `button[data-testid="stop-button"]`, `button[data-testid="copy-turn-action-button"]`, `[data-message-author-role="assistant"]`, `.markdown`, `nav a[href^="/c/"]`）。MCP ツール名（`navigate_page`/`new_page`/`take_snapshot`/`type_text`/`click`/`evaluate_script`/`wait_for`）は調査で確認済みの実名。サーバ prefix は `mcp__chrome-cdp__*`（Task 2 で定義 → Task 6/7 で使用）で一致。
