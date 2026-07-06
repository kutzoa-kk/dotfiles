# プラグイン・重複系統の仕分け表（B-2 / B-3）

作成: 2026-07-06 · 前提: `/context` 実測済み · 方針: **rules/ecc のファイルは改変しない**（ユーザー指定）
状態: **判断の記録のみ。実装（無効化・削除）は未実施。**

## 0. 実測サマリー（/context, Fable 5 セッション）

| 区分 | 実測 | 所見 |
|---|---|---|
| Memory files | 16.7k tokens / 21ファイル | うち rules/ecc が約13.9k（web 7 + common 10 + README） |
| Skills | 9.8k tokens / **617個** | 大半が `< 20 tokens` = **説明文が脱落し名前のみ**。自作22個と一部だけ説明文が生存 |
| Custom agents | 10.3k tokens / **120体** | octo 系（personas/droids/principles/skills）で約5.5k、ecc 系で約4.4k |
| MCP tools | 0 tokens（オンデマンド）/ 124ツール | 遅延ロードが機能。常駐圧迫なし。ただし選択肢の重複は残る |
| 合計常駐（会話以外） | 約50k tokens | Fable 1M では5%、200k モデルでは25%相当 |

**実測が変えた評価**: ENV-003（説明文予算）は「疑い」から**「脱落が現に起きている」に確定**。
ecc/octo の数百スキルは名前しか見えておらず自動発動不能 → **無効化しても失うものがほぼない**。
削減の主対象はトークンよりも「発動枠と選択肢の混雑」および 200k モデルセッションでの常駐比率。

## 1. 重複系統の「正」決定（B-3）

| 役割 | 正（残す） | 無効化・削除候補 | 理由 |
|---|---|---|---|
| ブラウザ自動化 | **claude-in-chrome**（Anthropic 公式拡張）+ 自作 playwright-cli スキル（テスト用） | `chrome-cdp`（~/.claude.json 直登録）/ chrome-devtools-mcp プラグイン / ecc 内蔵 chrome-devtools / ecc 内蔵 playwright | 公式拡張はユーザーの Chrome ログインを使え、**chatgpt-bridge スキルの前提**。テスト自動化は CLI ベースの自作スキルで常駐ゼロ。ecc 内蔵2系統の個別無効化可否は ecc 設定の調査が必要（不可なら容認） |
| コードレビュー | **組み込み /code-review**（ultra 対応） | code-review プラグイン / code-simplifier プラグイン（→ 組み込み /simplify） | 組み込みが最新・保守不要。ecc の言語別レビュアーは ecc 本体に付随（本体判断に従属） |
| 深掘り調査 | **組み込み deep-research** | —（ARS:deep-research は ARS パイプライン内部用で共存可） | ecc:deep-research / octo:research はプラグイン本体の判断に従属 |
| スキル作成 | **skill-creator プラグイン** | example-skills（skill-creator 重複含む） | ecc:skill-create は ecc 付随で共存可 |
| hook 生成 | **自作 auto-format-hook / lint-config-guard** | hookify プラグイン | 自作が環境に最適化済み。ecc:hookify は ecc 付随 |
| CLAUDE.md 生成 | **自作 claude-md-generator** | claude-md-management プラグイン | 自作がポインタ型方針に合致 |
| MCP 二重登録 | **プラグイン版 serena** | dotdir/.claude/.mcp.json の serena / Context7 定義（ファイルごと去就決定） | .mcp.json は稼働側に未リンクで実質休眠（ENV-008） |

## 2. プラグイン仕分け（B-2）— 有効約30 + 孤立11

### 残す（14）

| プラグイン | 理由 |
|---|---|
| ecc | 中核。GateGuard 等を手当てしつつ運用実績あり。ただし §4 の縮小余地を将来検討 |
| superpowers | 設計文化（docs/superpowers）の基盤。使用実績あり |
| codex | CLAUDE.md 記載のセカンドオピニオン経路 |
| academic-research-skills (ARS) | 医学研究の中核 |
| security-guidance | 本日も SRI 指摘で機能。軽量 |
| commit-commands | 軽量・実用 |
| frontend-design | html-report 系と相補。軽量 |
| skill-creator | スキル作成の「正」 |
| serena | LSP ベースのコード操作（プラグイン版を正） |
| explanatory-output-style | 現在使用中 |
| pyright-lsp | Python 常用のため |
| toolcall-recover | 出力崩壊復旧の実績あり（稼働側のみ→ git 取り込みを検討） |
| linear | Linear 運用があるなら残す（**要確認**寄りの残す） |
| claude-code-setup | 軽量。迷えば無効化でも影響小 |
| deploy-on-aws / aws-serverless | **AWS 使用継続（ユーザー確認 2026-07-06）** |

### 無効化確定（11）

- 重複解消（§1 連動）: chrome-devtools-mcp / code-review / code-simplifier / hookify / claude-md-management / example-skills / ralph-loop（組み込み /loop・ecc:loop と重複）/ feature-dev（superpowers の設計フローと重複）
- 使用終了（**ユーザー確認 2026-07-06**）: **octo**（常駐 agents 約5.5k + スキル約100個を解放）/ data-engineering / astronomer-data（Airflow 不使用）

### 要確認（残り2）

| プラグイン | 確認ポイント |
|---|---|
| typescript-lsp / swift-lsp | 各言語の常用度 |

### アンインストール推奨（11 = 孤立）

enabledPlugins 未記載のままインストールだけ残っているもの: claude-code-workflows 系7個（code-refactoring, error-debugging, context-management, machine-learning-ops, code-documentation, debugging-toolkit, agent-orchestration）+ document-skills + slack + そのほか棚卸しで検出の2個。使う意思が生じたら再インストールで足りる。

### 直登録 MCP（~/.claude.json）

| サーバ | 判断 |
|---|---|
| chrome-cdp | 削除候補（§1 ブラウザ一本化） |
| knowledge-store | 残す（使用実績あり） |
| claude_ai_Google_Drive | 要確認（gog CLI と重複気味） |

## 3. 見込み効果

- Custom agents: 10.3k → **約4.5k**（octo 無効化が確定したため実現見込み。半減超）
- Skills: 617個 → **約350個以下**（説明文の生存率が上がり、自作22個の発動信頼性が回復）
- 常駐 Memory: rules/ecc 非改変のため据え置き（§4 の移設案を採れば −13.9k）
- 選択肢の混雑解消: ブラウザ5系統→1、レビュー5→1 ほか

## 4. rules/ecc の扱い（決定: 案X 現状容認）

**ユーザー決定（2026-07-06）: 案X 現状容認で確定。** 移動・改変は ecc プラグインに対して破壊的（ecc がこの配置を前提に参照している可能性がある）ため行わない。

- 負担は実測 約13.9k tokens（Fable 1M で1.4%、200k モデルで7%相当）を許容する
- 「web ルールの無差別適用」ノイズは既知の制約として受け入れる
- ecc プラグインの将来更新で配置慣行が変わった場合にのみ再検討

## 5. 実装時の手順メモ（別セッションで可・モデル不問）

1. 無効化: `/plugin` から対象を disable（または settings.json の enabledPlugins 編集 → link 反映）
2. 孤立11個: `claude plugin uninstall` 相当の操作で削除
3. chrome-cdp: `~/.claude.json` の mcpServers から削除
4. .mcp.json: 去就決定後に削除 or 正規位置へ
5. 各ステップ後に `/context` を再計測し、本表の「見込み効果」と突き合わせる
6. 1週間運用して不便が出たものだけ個別に復帰（すべて可逆）
