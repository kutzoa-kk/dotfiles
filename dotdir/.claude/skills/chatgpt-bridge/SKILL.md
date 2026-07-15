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
- 送信前に `references/ask-and-capture.md` §0 でモード選択。**既定は GPT-5.6**（指定が無ければ GPT-5.6 を選択、既に GPT-5.6 なら操作なし）。ユーザーがモードを明示（例「Pro拡張で」「最高で」）した場合はそれを優先。重いモード（Pro 拡張）は完了検知タイムアウトを 600s+ に延長。
- 送信&取得: `references/ask-and-capture.md`（ProseMirror 入力 / 二重シグナル完了検知 / 抽出）
- 送信対象が 5 件を超える場合は、ループ実行前にユーザーへ確認する。
- 必ず MCP は **:9222 attach 済みサーバ**（例 `mcp__chrome-cdp__*`）を使う。操作対象の指定は `take_snapshot` の uid（click/type_text 用）、CSS セレクタの存在確認は `evaluate_script` で実行時プローブ（count>0）。

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
