# 設計: `chatgpt-bridge` スキル

- **日付**: 2026-06-30
- **対象**: Claude Code ユーザースキル（`dotdir/.claude/skills/chatgpt-bridge/`）
- **ステータス**: 実装済み（`dotdir/.claude/skills/chatgpt-bridge/` として稼働中。2026-07-06 更新）

## 1. 目的

Chrome 上の ChatGPT（Pro ログイン済みセッション）を Claude Code から駆動し、**質問を投げて回答を取得・集約**する。中核的価値は、既に `codex` / `agy`（Codex CLI / Antigravity CLI）で行っているセカンドオピニオン取得を、**ブラウザの ChatGPT Pro でも可能にする**こと。加えて、**質問先チャットを名前で「新規/既存」選択**できることで、用途別（法務用・技術用・経営用など）のコンテキストを保ったまま継続質問・回答統合ができる。

### 背景（確認した事実）

- ecc プラグインは chrome-devtools MCP を提供（`/Users/kkmclab/.claude/plugins/cache/ecc/ecc/2.0.0/.mcp.json` = `npx -y chrome-devtools-mcp@latest`、デフォルト引数）。**デフォルトでは MCP が専用 Chrome を別プロファイルで起動**するため、ユーザーのログイン済み ChatGPT Pro セッションは自動では使えない。
- **Chrome 136+（2025 年中頃〜）はセキュリティ上、デフォルト user-data-dir での `--remote-debugging-port` を無効化**している（既知の挙動。実装時に対象 Chrome バージョンで再検証する）。そのため「普段の Chrome そのもの」ではなく、**専用 `--user-data-dir` で remote-debugging 起動した Chrome に ChatGPT へ一度ログイン**する形が現実解。同一 Pro アカウントなので Pro 機能はそのまま利用可能。
- 既存スキル `playwright-cli`（ブラウザ自動化）と `medical-ai-compliance`（ルーター + references/assets 構成）が構造の参考。
- 本スキルの最難関は **ストリーミング回答の完了検知と最終テキスト抽出**。`evaluate_script`（DOM 直読み + ポーリング）が最も堅牢で、`take_snapshot` / `wait_for` を補助に使う。

### 決定事項（ユーザー確認済み）

| 論点 | 決定 |
|---|---|
| 主目的（「集約」の意味） | **両方（モード切替）** — 単発セカンドオピニオン + 複数チャット振り分け統合の両対応ルーター |
| 接続方式 | **既存 Chrome に接続** — remote-debugging port 経由（Chrome 136 制約により専用プロファイル） |
| 出力先 | **インライン + 必要時ファイル** — 長文/複数回答時のみ Markdown 保存 |

## 2. スコープ

### 含む

- chrome-devtools MCP を `--browser-url` で remote-debugging 起動済み Chrome に接続する手順（references）
- 専用デバッグプロファイルの冪等起動スクリプト（asset）と初回ログイン誘導
- ヘルスチェック（Chrome 稼働確認 / ChatGPT ログイン確認）
- チャット解決：新規作成 / 既存チャットを名前で検索・選択（無一致・複数一致の解決ロジック）
- 質問送信 → 完了検知 → 最終回答抽出（セレクタ + a11y フォールバック）
- Single / Multi 2 モードの集約（要約 / 統合レポート）
- インライン出力 + Markdown 保存（テンプレート）

### 含まない（YAGNI）

- ChatGPT API 連携（本スキルはあくまでブラウザ UI 駆動。API は別手段）
- 画像生成・ファイルアップロード等 ChatGPT の付随機能（質問→テキスト回答に限定）
- ChatGPT 以外の LLM（Claude/Gemini 等）への汎用化
- ログイン自動化（資格情報の保存・入力は行わない。初回ログインは人間が手動）
- Windows/Linux 専用パス対応（一次対象は macOS。スクリプトは macOS パス前提、注記で他 OS に言及）

## 3. アーキテクチャ

### ルータースキル（2 モード自動判定）

`medical-ai-compliance` と同じく、SKILL.md がルーターとなり入力から動作モードを判定する。

- **Single モード** — 1 質問 → 1 チャット（新規 or 既存名指定）→ 回答取得 → インライン要約
- **Multi モード** — 複数質問を複数の名前付きチャットへ振り分け → 全回答収集 → 統合レポート（一致点・相違点・推奨）→ Markdown 保存
- 判定基準：質問数・対象チャット数。1 件なら Single、複数なら Multi。曖昧時はユーザーに確認。

### 処理フロー

```
起動 → Step1 ヘルスチェック（:9222 で Chrome 稼働? ChatGPT ログイン済み?）
        └ 未起動/未ログイン → セットアップ誘導（launch script 実行 / 初回ログイン）
     → Step2 モード判定（single / multi）
     → Step3 各 (質問, 対象) ごと:
          ├ チャット解決: 新規=「New chat」/ 既存=サイドバーを名前検索しクリック
          │   （無一致→新規作成提案 / 複数一致→候補提示しユーザー選択）
          ├ 質問入力・送信（composer に fill → Enter / 送信ボタン）
          └ 完了検知（生成停止ボタン消失 / Copy ボタン出現を evaluate_script でポーリング）
              → 最終 assistant メッセージ抽出
     → Step4 集約（single=要約 / multi=統合テンプレート）
     → Step5 出力（インライン。長文/複数時は Markdown 保存しパス提示）
```

### ファイル構成（lean / YAGNI）

```
chatgpt-bridge/
├── SKILL.md                      # ルーター: モード判定・フロー・安全原則・バッチ指定法
├── references/
│   ├── connection-setup.md       # 専用プロファイルで remote-debug 起動 / MCP --browser-url /
│   │                             #   初回ログイン / Chrome 136 注記 / ヘルスチェック手順
│   ├── chat-targeting.md         # 新規 vs 既存名検索 / サイドバー探索 / 無一致・複数一致の解決
│   └── ask-and-capture.md        # 送信 / 完了検知ロジック / 回答抽出セレクタ + フォールバック /
│                                 #   エラー処理（生成中・レート制限・タイムアウト）
└── assets/
    ├── launch-chrome-debug.sh    # 冪等な起動スクリプト（既に :9222 稼働なら再利用、macOS パス）
    └── aggregation-report.md     # Multi モードの統合レポート出力テンプレート
```

### コンポーネント境界

| ユニット | 役割 | 依存 |
|---|---|---|
| `connection-setup.md` | Chrome 起動・MCP 接続・ヘルスチェックの手順を提供 | launch-chrome-debug.sh, chrome-devtools MCP |
| `chat-targeting.md` | チャット解決（新規/既存名）を提供 | take_snapshot / evaluate_script / click |
| `ask-and-capture.md` | 送信・完了検知・抽出を提供 | fill / evaluate_script / wait_for |
| `launch-chrome-debug.sh` | デバッグ Chrome の冪等起動 | macOS Chrome バイナリ |
| `aggregation-report.md` | Multi 出力の整形テンプレート | （なし） |
| `SKILL.md` | モード判定とフロー統率、上記への誘導 | 全 references/assets |

## 4. 接続設計（案 A: chrome-devtools MCP + 専用デバッグプロファイル）

### セットアップ（初回のみ / references に記載）

```bash
# 1. 専用プロファイルで remote-debugging Chrome を起動（launch-chrome-debug.sh が冪等実行）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.cache/chatgpt-bridge-chrome"

# 2. (初回) その Chrome 窓で chatgpt.com に手動ログイン。以降プロファイルに永続。

# 3. chrome-devtools MCP を起動済み Chrome に接続:
#    npx chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
```

### 接続方式の MCP 設定

- 既存 ecc の `chrome-devtools` MCP はデフォルト引数（専用 Chrome 起動）なので、本スキル用に **`--browser-url` 付き MCP サーバ設定を別途追加**する必要がある。dotfiles 管理下（`dotdir/.claude/settings.json` の `mcpServers` もしくはプロジェクト `.mcp.json`）に追記する案を references に記載。MCP 設定変更は Claude Code 再起動が必要（初回セットアップの一部）。
- 代替: playwright-cli の CDP 接続（案 B）。MCP 再起動不要だが回答抽出がやや煩雑。references に「フォールバック」として簡潔に併記。

## 5. 安全・運用原則（SKILL.md に明記）

- **実アカウント操作**：ユーザーの実 ChatGPT Pro を駆動する。大量送信（目安: 5 問超）前に確認。利用制限・レート制限に配慮。
- **資格情報不保持**：回答の可視テキストのみ読む。ログイン自動化は行わない。セッションは専用プロファイルにのみ残る（ローカル管理対象であることを注記）。
- **事実確認**：ChatGPT 回答を検証済み事実として扱わない。集約レポートには出典（どのチャット由来か）を明示し、誤りうる旨を付記。
- **DOM 脆弱性**：chatgpt.com のセレクタは経年変化する。構造ベース（最後の assistant ターン）抽出と a11y snapshot をフォールバックに用意。セレクタ変化検知時はユーザーに通知。

## 6. 実装フェーズで要検証（プランへ引き継ぐ）

1. chrome-devtools-mcp の `--browser-url` 正確なフラグ名・挙動（インストール版で確認）
2. 現行 chatgpt.com の DOM セレクタ群：
   - composer（入力欄）/ 送信ボタン
   - 生成中インジケータ / 生成停止ボタン / 完了後の Copy・Regenerate ボタン
   - assistant メッセージコンテナ（`[data-message-author-role="assistant"]` 等の現行値）
   - サイドバーのチャット一覧・チャットタイトル要素
3. 対象環境の Chrome バージョンと remote-debugging 制約（136+ の挙動）
4. MCP 設定追加方法（dotfiles のどのファイルに `--browser-url` サーバを置くか）と再起動フロー

> これらは brainstorming では確定せず、writing-plans 以降でサブエージェントによる live 検証を行う。

## 7. 受け入れ基準

- [ ] ヘルスチェックで Chrome 未起動/未ログインを検知し、セットアップ誘導できる
- [ ] 「新規チャットに質問」が動作し回答を取得できる
- [ ] 「既存チャットを名前で指定して質問」が動作し、無一致・複数一致を適切に処理できる
- [ ] ストリーミング完了を検知し最終回答テキストを正確に抽出できる
- [ ] Single モードでインライン要約、Multi モードで統合レポート（Markdown 保存）を出力できる
- [ ] 安全原則（大量送信前確認・出典明示・資格情報不保持）が SKILL.md に明記されている
- [ ] スキルが `dotdir/.claude/skills/chatgpt-bridge/` に配置され、`make link` 対象になる
