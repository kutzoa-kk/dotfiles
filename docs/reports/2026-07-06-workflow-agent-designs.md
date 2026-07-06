# Workflow / Agent 設計書（P2: C-1〜C-6）

作成: 2026-07-06 · 状態: **設計のみ。実装（ファイル配置・リンク生成）は未実施。**
前提: プラグイン仕分け表（同日付）の「正」決定に基づく。octo 無効化確定後の環境を想定。

設計原則（調査レポートより）:
- 並列化は探索型の高価値タスク限定（マルチエージェントはチャット比約15倍のトークン）
- サブエージェント指示は4要素必須: **目的 / 出力形式 / 使うツール・手順 / タスク境界**
- 読み取り専用にできるものは読み取り専用にする（監査系はすべて該当）
- 重複を増やさない: 汎用リサーチは既存 deep-research を使い、新設は「この環境の資産を束ねるもの」のみ

---

## C-1: ディレクトリ整備（実装手順、モデル不問）

1. `dotdir/.claude/agents/.gitkeep` と `dotdir/.claude/workflows/.gitkeep` を作成
2. `make link` を再実行し、破損リンク `~/.claude/{agents, workflows}` が実体を指すことを確認
   （`~/.claude/commands` リンクは削除する — commands はスキルへ統合済みの機能のため新設しない）
3. 検証: `ls -la ~/.claude/agents ~/.claude/workflows` でリンク先実在を確認
4. 注意: `.bin/link.sh` が agents/workflows を対象に含まない場合のみ link.sh に追記（現状の破損リンクは「対象だが実体なし」の可能性が高い）

---

## C-2: named Workflow 第1弾 — `env-audit`

- 目的: 環境の定期監査（月1ルーチン）。4観点を並列スキャンし、所見を重大度順の1レポートに集約する
- 配置: `dotdir/.claude/workflows/env-audit.js`（リンク経由で `~/.claude/workflows/`）
- 起動: `Workflow({ name: 'env-audit', args: { date: '2026-08-01' } })` — 日付は呼び出し側が渡す（Workflow 内で `Date` は使用不可）
- 全エージェント読み取り専用・effort low（機械的スキャンのため）

### スクリプト草案

```javascript
export const meta = {
  name: 'env-audit',
  description: 'Claude 環境（dotfiles + ~/.claude）の定期監査 — 表面積・重複・残置物・ドリフトを並列点検',
  phases: [
    { title: 'Scan', detail: '4観点の並列スキャン（読み取り専用）' },
    { title: 'Report', detail: '所見の集約と重大度順の整列' },
  ],
}

const FINDINGS = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'severity', 'title', 'evidence', 'recommendation'],
        properties: {
          id: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
          title: { type: 'string' },
          evidence: { type: 'string' },
          recommendation: { type: 'string' },
        },
      },
    },
  },
}

const COMMON = `対象: /Users/kkmclab/dotfiles(git 実体）と /Users/kkmclab/.claude（稼働環境）。
環境知識: merge リンク構造（実体は dotdir/.claude/）。settings.json は外部ツール orca が hooks を注入し得る。
制約: 読み取り専用 — いかなるファイルも変更・削除しないこと。
出力: 所見リスト。evidence には必ずパスと数値（行数・個数・サイズ）を含める。該当なしなら findings: [] を返す。`

phase('Scan')
const scans = await parallel([
  () => agent(`${COMMON}
目的: スキル/エージェント表面積の点検（説明文予算の消費状況）。
手順: (1) ~/.claude/plugins/installed_plugins.json の有効プラグイン数を数える。(2) dotdir/.claude/skills/*/SKILL.md の frontmatter description 合計文字数を測る。(3) プラグイン由来スキル総数を概算し、常駐予算との比を出す。
境界: プラグインの中身の評価はしない（数の把握のみ）。id は SF-連番。`,
    { label: 'scan:surface', phase: 'Scan', schema: FINDINGS, effort: 'low' }),
  () => agent(`${COMMON}
目的: 同一役割ツールの重複検出。
手順: MCP 登録3箇所（~/.claude.json の mcpServers / 有効プラグイン内 MCP / dotdir/.claude/.mcp.json）を横断し、同役割（ブラウザ自動化・レビュー・調査・スキル作成等）の並存を列挙する。
境界: どれを残すかの決定はしない（事実列挙まで）。id は DUP-連番。`,
    { label: 'scan:duplication', phase: 'Scan', schema: FINDINGS, effort: 'low' }),
  () => agent(`${COMMON}
目的: 残置物の検出。
手順: (1) ~/.claude/plugins/cache/ の temp_* と *.bak を列挙。(2) ~/.claude 直下の破損シンボリックリンクを検出。(3) dotdir/.claude/skills/ 配下で SKILL.md を持たないディレクトリを列挙。(4) キャッシュ合計サイズを測る。
境界: 削除しない。id は CRUFT-連番。`,
    { label: 'scan:cruft', phase: 'Scan', schema: FINDINGS, effort: 'low' }),
  () => agent(`${COMMON}
目的: git↔稼働ドリフトの検出。
手順: (1) dotdir/.claude/settings.json と ~/.claude/settings.json の差分（hooks / enabledPlugins / その他キー）。(2) dotdir/.claude/CLAUDE.md の @import 参照先が dotdir 基準で実在するか確認。(3) dotfiles リポジトリの未 push コミット数。
境界: 修正しない。id は DRIFT-連番。`,
    { label: 'scan:drift', phase: 'Scan', schema: FINDINGS, effort: 'low' }),
])

phase('Report')
const all = scans.filter(Boolean).flatMap(r => r.findings)
const order = { critical: 0, high: 1, medium: 2, low: 3 }
all.sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9))
log(`所見 ${all.length} 件（critical ${all.filter(f => f.severity === 'critical').length} / high ${all.filter(f => f.severity === 'high').length}）`)
return { date: args?.date ?? 'unset', total: all.length, findings: all }
```

設計メモ:
- `parallel`（バリア）は正当 — Report 段は全スキャン結果の統合・整列を必要とするため
- 結果の Markdown レポート化はメインループが return 値を受けて行う（`docs/reports/env-audit-<date>.md` へ保存）。Workflow 内にファイル書き込み API はない
- 月1ルーチン化（D-5）はこの Workflow の定期起動をスケジュール登録するだけでよい

---

## C-3: named Workflow 第2弾 — `doc-review-panel`

- 目的: 文書（論文・レポート・設計書）の多観点並列レビュー + 所見ごとの敵対的検証。偽陽性を検証段で殺し、生き残った所見だけを返す
- 配置: `dotdir/.claude/workflows/doc-review-panel.js`
- 起動: `Workflow({ name: 'doc-review-panel', args: { file: '<絶対パス>', lenses: ['logic','language'], styleGuide: '~/.claude/japanese-style-guide.md' } })`（lenses / styleGuide は省略可）
- Anthropic 公式の「観点別レビュアー並列起動」パターンの応用。ARS・japanese-output-review・medical-ai-compliance は観点プロンプトの参照元として接続（レビュー観点に手動で織り込む）

### スクリプト草案

```javascript
export const meta = {
  name: 'doc-review-panel',
  description: '文書の多観点並列レビュー + 敵対的検証（args: { file, lenses?, styleGuide? }）',
  phases: [
    { title: 'Review', detail: '観点別レビュアーの並列展開' },
    { title: 'Verify', detail: '所見ごとの反証テスト（迷ったら棄却）' },
  ],
}

const FINDINGS = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['location', 'severity', 'claim', 'suggestion'],
        properties: {
          location: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
          claim: { type: 'string' },
          suggestion: { type: 'string' },
        },
      },
    },
  },
}
const VERDICT = {
  type: 'object',
  required: ['refuted', 'reason'],
  properties: { refuted: { type: 'boolean' }, reason: { type: 'string' } },
}

const file = args?.file
if (!file) throw new Error('args.file に対象ファイルの絶対パスを渡してください')

const ALL_LENSES = [
  { key: 'logic', focus: '論理構成 — 主張と根拠の対応、飛躍、循環論法、結論の過大な一般化' },
  { key: 'evidence', focus: '事実と引用 — 数値の内部一貫性、出典の実在、引用内容と本文の一致' },
  { key: 'language', focus: '日本語品質 — 不要な英語混入、文体の不統一、冗長表現、わかりにくい文' },
  { key: 'methodology', focus: '研究方法論 — 統計手法と主張の整合、多重比較、選択バイアス、因果の言い過ぎ' },
]
const lenses = args?.lenses?.length
  ? ALL_LENSES.filter(l => args.lenses.includes(l.key))
  : ALL_LENSES

const results = await pipeline(
  lenses,
  l => agent(`目的: ${file} を「${l.focus}」の観点のみでレビューする。
手順: 対象ファイルを Read で読む。${l.key === 'language' && args?.styleGuide ? `先に ${args.styleGuide} を読み、禁止→推奨対応表に照らすこと。` : ''}観点内の問題だけを所見化する。
出力: 所見ごとに location（節・行）/ severity / claim（何がなぜ問題か）/ suggestion（具体的な修正案）。確信のない指摘は含めない。問題なしなら findings: []。
境界: 他観点への越境禁止。ファイルの変更禁止。`,
    { label: `review:${l.key}`, phase: 'Review', schema: FINDINGS }),
  (review, l) => parallel((review?.findings ?? []).map(f => () =>
    agent(`役割: 懐疑的検証者。次のレビュー指摘を反証せよ。
指摘: 「${f.claim}」（対象: ${file} の ${f.location}）
手順: 原文の該当箇所と前後を読み、指摘が誤読・文脈の見落とし・些末な好みに過ぎないかを判定する。
出力: refuted（true=指摘は不成立）と reason。**迷った場合は refuted: true**（偽陽性を通さない）。`,
      { label: `verify:${l.key}`, phase: 'Verify', schema: VERDICT })
      .then(v => ({ ...f, lens: l.key, verdict: v }))))
)

const confirmed = results.filter(Boolean).flat().filter(Boolean)
  .filter(f => f.verdict && !f.verdict.refuted)
const order = { critical: 0, high: 1, medium: 2, low: 3 }
confirmed.sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9))
log(`確定所見 ${confirmed.length} 件（検証で棄却された偽陽性を除く）`)
return { file, lenses: lenses.map(l => l.key), confirmed }
```

設計メモ:
- `pipeline` を採用 — logic 観点の検証は language 観点のレビュー完了を待たない（バリアなし）
- 医療文書には `lenses` へ将来 `compliance` 観点（medical-ai-compliance の判定基準を focus 文に織り込む）を追加拡張できる
- 検証段の「迷ったら棄却」は敵対的検証の定石（調査レポート・設計原則参照）

---

## C-4: named Workflow 第3弾 — `sdd-experiment-sweep`

- 目的: SDD ML プロジェクトの実験群を横断監査し、ゲート違反・リーク兆候・整合性を1つの比較ビューに集約。自作スキル最大勢力（sdd-* 7個）の「1実験ずつ手動」を「全実験を一括」に変える
- 配置: `dotdir/.claude/workflows/sdd-experiment-sweep.js`
- 起動: `Workflow({ name: 'sdd-experiment-sweep', args: { projectRoot: '<プロジェクト絶対パス>' } })`

### スクリプト草案

```javascript
export const meta = {
  name: 'sdd-experiment-sweep',
  description: 'SDD ML プロジェクトの実験横断監査（args: { projectRoot }）',
  phases: [
    { title: 'Discover', detail: '実験の列挙' },
    { title: 'Audit', detail: '実験ごとの整合性・リーク監査（並列）' },
    { title: 'Compare', detail: '横断集約' },
  ],
}

const EXPS = {
  type: 'object',
  required: ['experiments'],
  properties: { experiments: { type: 'array', items: { type: 'string' } } },
}
const AUDIT = {
  type: 'object',
  required: ['experiment', 'passed', 'violations', 'summary'],
  properties: {
    experiment: { type: 'string' },
    passed: { type: 'boolean' },
    violations: {
      type: 'array',
      items: {
        type: 'object',
        required: ['rule', 'detail', 'evidence'],
        properties: {
          rule: { type: 'string' },
          detail: { type: 'string' },
          evidence: { type: 'string' },
        },
      },
    },
    summary: { type: 'string' },
  },
}

const root = args?.projectRoot
if (!root) throw new Error('args.projectRoot に SDD プロジェクトの絶対パスを渡してください')

phase('Discover')
const found = await agent(`目的: ${root} の SDD ML 実験を列挙する。
手順: docs/experiments/*.md、実験設定（configs/ / exp/）、MLflow の run 記録（mlruns/ か mlflow.db）を突き合わせ、実験単位（run_name またはディレクトリ名）を特定する。
出力: 実験識別子の配列のみ。見つからなければ空配列。
境界: 読み取り専用。`,
  { label: 'discover', phase: 'Discover', schema: EXPS, effort: 'low' })

if (!found.experiments.length) {
  log('実験が見つかりませんでした')
  return { projectRoot: root, audited: 0, results: [] }
}
log(`実験 ${found.experiments.length} 件を検出`)

const audits = await pipeline(
  found.experiments,
  exp => agent(`目的: SDD 実験「${exp}」の監査（プロジェクト: ${root}）。
観点（SDD プライムルール準拠）: (1) 削除 run の痕跡 (2) hold-out 使用回数の上限超過 (3) CV ゲート通過前の hold-out 参照 (4) 仮説の事前登録（00_HYPOTHESES.md）と実施順の整合 (5) 仕様ドキュメントと実装のドリフト (6) 特徴量リーク兆候（feature_availability と split 整合）。
出力: 違反ごとに rule / detail / evidence（ファイルパス必須）。違反なしなら passed: true, violations: []。
境界: 読み取り専用。この実験以外に踏み込まない（1実験=1エージェント）。`,
    { label: `audit:${exp}`, phase: 'Audit', schema: AUDIT })
)

phase('Compare')
const ok = audits.filter(Boolean)
const failed = ok.filter(a => !a.passed)
log(`監査完了 ${ok.length}/${found.experiments.length} — 違反あり ${failed.length} 件`)
return { projectRoot: root, audited: ok.length, failedCount: failed.length, results: ok }
```

設計メモ:
- 監査観点は sdd-experiment-audit（5チェック）+ sdd-pre-train-guard（リーク）の要点を指示文へ直接埋め込む方式。サブエージェントにスキル発動を期待しない（発動は非決定的なため — 調査結果の教訓）
- 比較マトリクスの整形・sdd-report-generator への接続はメインループが return 値を受けて行う

---

## C-5: 自作 Agent 定義草案（3体）

配置: `dotdir/.claude/agents/<name>.md`。frontmatter は実装時に公式 docs（code.claude.com/docs/en/sub-agents）の最新仕様を確認して微調整すること。

### 1. env-auditor.md — 環境監査ワーカー（env-audit から `agentType` 指定で利用可）

```markdown
---
name: env-auditor
description: dotfiles/.claude 環境の監査専任。merge リンク構造・settings ドリフト・スキル/プラグイン表面積・残置物を読み取り専用で点検する。環境の点検・棚卸し・監査の依頼で使用。
tools: Read, Grep, Glob, Bash
model: sonnet
---

あなたは kkmclab の dotfiles 環境の監査専任エージェントです。

## 環境の固有知識（前提として常に正しいと仮定してよい事実）
- 実体は /Users/kkmclab/dotfiles/dotdir/.claude/、稼働は ~/.claude/（ファイル/ディレクトリ単位の merge リンク。.bin/link.sh 参照）
- ~/.claude/settings.json には外部ツール orca が hooks を注入することがある（git 版との差分は「ドリフト」として報告し、削除はしない）
- ecc プラグインが GateGuard 等のフックを持ち込む。RTK が Bash コマンドを書き換える
- 自作スキルは dotdir/.claude/skills/、プラグインは ~/.claude/plugins/

## 原則
1. 読み取り専用。ファイルの作成・変更・削除は一切しない（Bash も ls/find/du/diff 等の照会に限る）
2. すべての所見に証拠（パス・行数・個数・サイズ）を付ける
3. 事実と推測を明確に区別する
4. 修理方法は「推奨」として書き、実行はしない

## 出力形式
所見リスト（id / severity: critical|high|medium|low / title / evidence / recommendation）。
依頼側がスキーマを指定した場合はそれに従う。
```

### 2. jp-doc-reviewer.md — 日本語文書レビュアー（doc-review-panel の language 観点と単発レビューの両方で使用）

```markdown
---
name: jp-doc-reviewer
description: 日本語文書の品質レビュー専任。japanese-style-guide.md の禁止→推奨対応表に照らし、英語混入・文体不統一・禁止表現・わかりにくさを点検する。日本語の文書・出力の品質チェック依頼で使用。
tools: Read, Grep, Glob
model: sonnet
---

あなたは日本語文書の品質レビュー専任エージェントです。

## 手順
1. 最初に必ず ~/.claude/japanese-style-guide.md を読む（禁止→推奨対応表が判定基準）
2. 対象文書を読み、次の5観点で点検する:
   (1) 不要な英語混入 — コード識別子・確立した技術用語・固有名詞以外の英語
   (2) 文体の乱れ — です/ます体からの逸脱、文体の混在
   (3) 記録済み禁止表現 — 対応表に載っている表現の再出現
   (4) わかりにくい表現 — 直訳調、二重否定、過度な省略、長すぎる文
   (5) 崩壊出力 — ツール呼び出しマークアップ等の混入
3. 各指摘に、対応表に基づく言い換え案を付ける

## 原則
- 確信のない指摘はしない（好みの押し付けと区別する）
- 対応表にない新種の問題は「新規パターン候補」として区別して報告する（対応表への追記判断は依頼側が行う）
- ファイルは変更しない

## 出力形式
所見リスト（location / 観点 / 問題箇所の引用 / 言い換え案）。新規パターン候補は別リスト。
```

### 3. research-methodologist.md — 研究方法論の敵対的検証者（doc-review-panel の methodology 観点、SDD 系の相談役）

```markdown
---
name: research-methodologist
description: 統計・研究方法論の敵対的検証専任。主張と解析手法の整合、多重比較、リーク、選択バイアス、因果推論の妥当性を検証する。医学研究・ML 実験の方法論チェックで使用。
tools: Read, Grep, Glob, Bash
model: inherit
---

あなたは研究方法論の敵対的検証者です。役割は「この解析・主張のどこが崩れうるか」を探すことであり、擁護ではありません。

## 検証観点
1. 主張と手法の整合 — 使われた統計手法がその主張を支持できる設計か
2. 多重比較 — 検定数に対する補正（Bonferroni / BH-FDR）の有無と妥当性
3. データリーク — 前処理・特徴量生成・分割の順序、fold 外情報の混入
4. 選択バイアス — 除外基準、欠測の扱い、生存者バイアス
5. 因果の言い過ぎ — 観察データからの因果的表現、交絡の未考慮
6. 効果量と臨床的意義 — p 値のみの主張、信頼区間の無視

## 原則
- 反証を試みて崩れなかった主張だけを「妥当」と認める
- 指摘には必ず「なぜ問題か」と「どう直すか（具体的な代替手法）」を付ける
- 医学系では確立訳語を使う（用量反応関係・プレフレイル等。japanese-style-guide.md 準拠）
- ファイルは変更しない

## 出力形式
検証結果リスト（対象の主張 / 判定: 妥当・要修正・不成立 / 根拠 / 修正案）。
```

設計メモ:
- モデル割り当て — 機械点検の env-auditor と定型レビューの jp-doc-reviewer は sonnet 固定（コスト効率）。判断の質が結果を左右する research-methodologist のみ `inherit`（Fable セッションから呼べば Fable で動く）
- ecc 28種との重複なし（環境固有知識・スタイルガイド運用・敵対的方法論検証は既存エージェントにない役割）

---

## C-6: CLAUDE.md への運用原則追記案（4行）

「## 行動原則 > 進め方」の節へ追記:

```markdown
- 並列サブエージェントは探索型の高価値タスク限定（トークン約15倍。単純タスクは1体・ツール呼び出し3〜10回）
- サブエージェント指示は4要素必須：目的 / 出力形式 / 使うツール / タスク境界
- 書き込みは「1ファイル=1エージェント」。競合するなら worktree 分離
- 5分未満で終わる作業は委譲しない
```

---

## 実装チェックリスト（別セッション実行用）

- [ ] C-1: dotdir/.claude/{agents, workflows} 作成 → make link → リンク検証（~/.claude/commands リンクは削除）
- [ ] C-5: Agent 3体の .md を配置（frontmatter 仕様を公式 docs で最終確認）
- [ ] C-2: env-audit.js を配置 → `Workflow({ name: 'env-audit', args: { date: '<今日>' } })` で試走 → 出力を docs/reports/env-audit-<date>.md へ整形保存
- [ ] C-3: doc-review-panel.js を配置 → 既存文書1本（例: 本設計書）で試走し、観点の越境・偽陽性棄却の挙動を確認
- [ ] C-4: sdd-experiment-sweep.js を配置 → 実在の SDD プロジェクトで試走
- [ ] C-6: CLAUDE.md へ4行追記（63行 → 67行。200行上限に対し余裕）
- [ ] 試走後: 各 Workflow の journal を確認し、指示文の曖昧さ・スキーマ不足を1回改訂（評価駆動の反復）
