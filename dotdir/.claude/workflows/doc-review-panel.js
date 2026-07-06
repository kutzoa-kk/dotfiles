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

// Workflow ランタイムは args を JSON 文字列で渡す場合があるため両対応にする
const A = typeof args === 'string' ? JSON.parse(args) : (args ?? {})
const file = A.file
if (!file) throw new Error('args.file に対象ファイルの絶対パスを渡してください')

const ALL_LENSES = [
  { key: 'logic', focus: '論理構成 — 主張と根拠の対応、飛躍、循環論法、結論の過大な一般化' },
  { key: 'evidence', focus: '事実と引用 — 数値の内部一貫性、出典の実在、引用内容と本文の一致' },
  { key: 'language', focus: '日本語品質 — 不要な英語混入、文体の不統一、冗長表現、わかりにくい文' },
  { key: 'methodology', focus: '研究方法論 — 統計手法と主張の整合、多重比較、選択バイアス、因果の言い過ぎ' },
]
const lenses = A.lenses?.length
  ? ALL_LENSES.filter(l => A.lenses.includes(l.key))
  : ALL_LENSES

const results = await pipeline(
  lenses,
  l => agent(`目的: ${file} を「${l.focus}」の観点のみでレビューする。
手順: 対象ファイルを Read で読む。${l.key === 'language' && A.styleGuide ? `先に ${A.styleGuide} を読み、禁止→推奨対応表に照らすこと。` : ''}観点内の問題だけを所見化する。
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
