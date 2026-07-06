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

// Workflow ランタイムは args を JSON 文字列で渡す場合があるため両対応にする
const A = typeof args === 'string' ? JSON.parse(args) : (args ?? {})
const root = A.projectRoot
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
