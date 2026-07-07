# Opus 4.8 Fable 級化基盤（コスト階段型四層基盤）設計書

- **日付**: 2026-07-07
- **ステータス**: 設計承認済み・実装前
- **作成**: Claude Fable 5（ブレインストーミングセッションでユーザー承認済み）

## 背景と目的

Fable 5（Mythos 級）はいずれ利用できなくなる。その後のメインモデル Opus 4.8 で Fable 級の実行品質を得るため、モデルの知能差をハーネス（Agent・Skill・Workflow・外注連携）で埋める基盤を構築する。

再現対象は次の2能力（ユーザー選定）:

1. **深い推論・一発の正答率** → 多段検証ループ・敵対的レビュー・ベストオブN で補う
2. **曖昧な指示の意図汲み取り** → 解釈宣言の定型フロー・判断パターンの蒸留知識で補う

## 制約と方針（確定事項）

| 項目 | 決定 |
|------|------|
| 適用範囲 | 全領域共通の汎用基盤（コード・研究・文書・調査） |
| 中核制約 | 週次トークン不足 → Codex CLI・agy CLI へ検証を外注し Claude トークンを温存 |
| 発動方式 | 外注検証は自動、Claude 並列（サブエージェント・Workflow）は明示呼び出し。例外: 重要タスク（不可逆・本番・論文の数値）の完了前検証のみ L2 を準自動起動 |
| 外注配分 | 両 CLI ともクォータ余裕あり。Codex＝コード実装・レビュー、agy＝調査・長文・仕様整合 |
| Fable の仕込み | 基盤の設計・構築自体を Fable 在任中に実施（特に判断パターン蒸留は Fable にしか書けない） |

## アーキテクチャ：コスト階段型の四層

同じ品質構造を、タスクの重要度に応じたコストで選べる階段構造。Claude の能力活用が本体で、外注はその中の一段。

| 層 | 実行主体 | 発動 | Claude トークン | 役割 |
|----|---------|------|----------------|------|
| L0 蒸留知識 | Claude ソロ | 常時 | ほぼゼロ | intent-gate（解釈宣言）＋判断パターン集 |
| L1 外注検証 | Codex・agy | 自動 | 裁定分のみ | セカンドオピニオン・完了時レビュー |
| L2 専門 Agent | Claude サブエージェント | 準自動（重要タスク） | 中 | 敵対的検証者 |
| L3 並列 Workflow | Claude 多重並列 | 明示のみ | 高 | ベストオブN・審査員パネル |

**Fable との対応**: 深い推論 → L1（常時の多段検証）＋ L2/L3（重要時の並列推論）。意図汲み取り → L0。

**役割分担の原則**: Opus 4.8 ＝統率者・裁定者（考える範囲を最小化）。Codex ＝コード実装・レビューの外注先。agy（Gemini 3.1 Pro High 指定）＝調査・長文読解・仕様整合の外注先。Claude サブエージェント＝外注では品質が届かない検証・並列推論。

## ファイル配置

```
dotfiles/
├── .bin/
│   └── llm-worker.sh                # 新規：Codex/agy 統一ヘッドレスラッパー
├── dotdir/.claude/                  # → $HOME/.claude/ へ merge リンク
│   ├── CLAUDE.md                    # 追記：intent-gate ルール + @decision-patterns.md 参照
│   ├── decision-patterns.md         # 新規：Fable 蒸留の判断パターン集（常駐、100行上限）
│   ├── agents/
│   │   ├── （既存3体そのまま）
│   │   └── adversarial-verifier.md  # 新規：L2 敵対的検証 Agent
│   ├── workflows/
│   │   ├── （既存3本そのまま）
│   │   └── deep-reason.js           # 新規：L3 ベストオブN Workflow
│   └── skills/
│       └── second-opinion/
│           └── SKILL.md             # 新規：L1 外注セカンドオピニオン
└── （codex プラグイン stop-review-gate：設定有効化のみ、構築なし）
```

## 標準データフロー

1. 依頼受領 → **L0** 常時作動：decision-patterns を踏まえ、曖昧なら解釈・前提・成功基準を宣言してから着手
2. 実行中、設計判断の分岐点や難所 → **L1** `/second-opinion`（Codex・agy 並列、Claude は裁定のみ）
3. コード変更したターンの完了時 → **L1** codex 停止ゲートが自動レビュー（Claude トークン消費なし）
4. 重要・不可逆・高難度タスク → **L2** adversarial-verifier を準自動起動。最重要は **L3** deep-reason を明示起動

## コンポーネント詳細

### L0-1: decision-patterns.md（新規、常駐）

Fable が過去セッションの記憶とこの環境の文脈から蒸留する「依頼の型 → 正しい解釈・動き方」の対応表。`japanese-style-guide.md` と同じ育成型ファイル運用（ユーザーの修正・指摘のたびに1行追記）。

構成3部:

1. **依頼の型と解釈** — 例:「確認して」＝読み取り専用の点検と報告（修正しない）／「〜したい」（構想）＝ brainstorming から開始（いきなり実装しない）
2. **このユーザーの固有文脈** — 医学研究者＋開発者の2領域、トークン効率への高い意識（コスト影響を常に明示）、監査可能性の重視、シンプル第一の設計哲学
3. **危険な誤解釈パターン** — 分析依頼を修正依頼と取り違える、確認質問で作業を止める、スコープの勝手な拡大など

制約: **100行上限**（常駐コスト一定化。超過時は古い・自明のパターンを削除）。

### L0-2: intent-gate ルール（CLAUDE.md 追記、4行程度）

```markdown
## Intent Gate（曖昧な依頼の解釈宣言）
- 依頼が曖昧（複数解釈可・成功基準不明・影響範囲不明）なら、着手前に解釈・前提・成功基準を1〜3行で宣言する
- 解釈の分岐が結果を大きく変えるときは AskUserQuestion で確認（推測で大きな作業を進めない）
- 判断の際は @decision-patterns.md のパターンを参照する
```

### L1-1: llm-worker.sh（.bin/ に新規）

全部品が使う統一ラッパー。呼び出し側は worker 名とプロンプトだけ渡す。

```bash
llm-worker.sh <codex|agy|both> [--role reviewer|researcher] [--timeout 300] [--cd dir]
# プロンプトは stdin から。結果は stdout（先頭に worker 名・実行時間のヘッダー）
```

- **codex** → `codex exec --sandbox read-only`（レビュー・調査はデフォルト読み取り専用）
- **agy** → `agy --print --model "Gemini 3.1 Pro (High)"`
- **both** → 並列実行。片方障害時は残りで続行し障害を出力に明記（相互フォールバック）
- `--role` はプロンプト前置きテンプレートの切り替え（reviewer＝反証重視の検証者指示、researcher＝出典明示の調査者指示）
- 実行ログを `~/.claude/logs/llm-worker/` に保存（監査可能性）

### L1-2: /second-opinion スキル（新規）

- **明示起動**: `/second-opinion <対象>`
- **自動起動**: スキル description のトリガー定義で「設計判断の分岐点・自信の持てない技術判断・不可逆操作の前」に Claude が自発的に呼ぶ
- 動作: ①質問＋コンテキスト＋判断基準をプロンプト整形 → ②`llm-worker.sh both` で並列外注 → ③Claude が**裁定のみ**（一致点・相違点・採用判断を3〜5行で報告）

### L1-3: 停止時レビューゲート（既存機能の有効化のみ）

openai-codex プラグインの stop-review-gate（Stop hook、実装済み）を `codex:setup` で有効化。コード変更したターンの完了時に Codex が変更を自動レビューし、問題があれば BLOCK → Claude が対処してから完了。

### L2: adversarial-verifier.md（Agent 定義、新規）

既存3体と同じ規格（frontmatter ＋ 役割・観点・原則・出力形式、1.5K 程度）。

- **専務**: 成果物・結論・計画を「壊す」こと。正しさの確認ではなく反証の探索
- **検証観点**: 前提の裏取り（コード・ログで事実確認）／見落とした分岐・エッジケース／「動くはず」と「動いた」の区別（検証証拠の有無）／都合の良い解釈
- **出力**: 判定 `REFUTED`（反証成立）or `SURVIVED`（反証失敗＝合格）＋重大度順の指摘リスト（根拠 `file:line` 付き）
- **読み取り専用**。修正はしない
- **発動**: 重要タスク（不可逆・本番・論文の数値）の完了前に準自動起動（運用原則に1行追加）。deep-reason の検証ステージからも `agentType` 指定で再利用

### L3: deep-reason.js（Workflow、新規）

Fable の「一発の深い推論」を並列構造で再現する、ここぞの一撃。

```
Solve   : 3視点（原理原則／リスク・失敗モード／実利・最短経路）の
          Claude サブエージェントが同一問題を独立に解く（並列）
Verify  : 各解へ adversarial-verifier を当て反証試行（pipeline、待ち合わせなし）
Judge   : 審査員1体が生存解＋反証結果を見て最終解を統合
```

- 引数: `{ question, perspectives?, n? }`（視点はタスクに合わせ差し替え可能）
- 呼び出し: 「deep-reason で考えて」で Workflow ツール起動。スキルラッパーは作らない（YAGNI）
- **コスト**: 1回＝ agent 7体分（数万〜十数万トークン）。明示呼び出し限定の理由

## エラー処理

- **llm-worker**: タイムアウト（既定300秒）・片方障害時は残った worker の結果で続行し障害を明記。両方障害なら「外注不可」を宣言して Claude 単独へフォールバック — 検証なしで黙って進めない
- **裁定権**: 外注回答の品質が低い場合、Claude 裁定で「両者とも不採用」を許容。外注は参考意見であり最終判断は常に Claude（誤った外部意見への盲従を防ぐ）
- **deep-reason**: エージェントが落ちた場合は除外して続行。生存解が1つでも Judge は実行
- **stop-review-gate**: codex 障害時の挙動はプラグイン側の仕様に従う（ゲートが開く方向、作業をブロックしない）

## 検証計画（実装時に必ず実施）

1. llm-worker: codex / agy / both の3モードをスモークテスト（タイムアウト動作含む）
2. adversarial-verifier: 意図的に欠陥を仕込んだ成果物で `REFUTED` が返るか確認
3. deep-reason: 小さい問題でフロー完走を確認（トークン節約のため最小構成）
4. intent-gate: 新セッションで曖昧な依頼を投げ、解釈宣言が出るか確認
5. /second-opinion: 実際の判断問題を1つ流し、裁定形式（一致点・相違点・採用判断）を確認

## 段階導入順（各段が独立して価値を持つ）

1. **L0** decision-patterns ＋ intent-gate — Fable 蒸留は締切があるため最優先。コストゼロで即効
2. llm-worker ＋ 停止ゲート有効化 — L1 の土台
3. /second-opinion — L1 完成
4. adversarial-verifier — L2
5. deep-reason — L3
6. CLAUDE.md 運用原則追記＋全体検証

## 既存資産との関係

- **既存 Agent 3体**（env-auditor / jp-doc-reviewer / research-methodologist）と**既存 Workflow 3本**（env-audit / doc-review-panel / sdd-experiment-sweep）は L2/L3 の先行例としてそのまま共存
- **superpowers スキル群**（brainstorming / systematic-debugging / verification-before-completion 等）は L0 のプロセス規律として本基盤の前提
- **codex プラグイン**の stop-review-gate / adversarial-review は L1 部品として活用（重複構築しない）
- **chatgpt-bridge** はブラウザ経由で重いため本基盤では使わない（llm-worker のヘッドレス CLI が主）

## 運用ルール

- 週次トークン残量が少ないときは L2/L3 の起動前に警告する
- decision-patterns は育成型: ユーザーの修正・指摘のたびに追記、100行上限で剪定
