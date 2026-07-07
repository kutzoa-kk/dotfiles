export const meta = {
  name: 'deep-reason',
  description: '難問をN視点の独立推論で解き、敵対的検証と審査で統合する（args: { question, perspectives?, model? }）',
  phases: [
    { title: 'Solve', detail: '視点別の独立推論（並列）' },
    { title: 'Verify', detail: 'adversarial-verifier による反証試行' },
    { title: 'Judge', detail: '生存解の比較・統合' },
  ],
}

const SOLUTION = {
  type: 'object',
  required: ['answer', 'reasoning', 'confidence'],
  properties: {
    answer: { type: 'string' },
    reasoning: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
}
const VERDICT = {
  type: 'object',
  required: ['verdict', 'issues'],
  properties: {
    verdict: { type: 'string', enum: ['REFUTED', 'SURVIVED'] },
    issues: { type: 'array', items: { type: 'string' } },
  },
}

// Workflow ランタイムは args を JSON 文字列で渡す場合があるため両対応にする
const A = typeof args === 'string' ? JSON.parse(args) : (args ?? {})
const question = A.question
if (!question) throw new Error('args.question に問いを渡してください')

const DEFAULT_PERSPECTIVES = [
  { key: 'principles', stance: '原理原則から考える。前提を疑い、第一原理から組み立てる' },
  { key: 'risk', stance: 'リスクと失敗モードから考える。この判断が間違うとしたらどこか、最悪ケースは何かを起点にする' },
  { key: 'pragmatist', stance: '実利と最短経路から考える。制約の中で最も費用対効果が高い現実解を探す' },
]
const perspectives = A.perspectives?.length
  ? A.perspectives.map((p, i) => ({ key: `custom${i + 1}`, stance: p }))
  : DEFAULT_PERSPECTIVES

// 検証・低予算時は args.model = 'haiku' 等で軽量化できる。省略時はセッションモデル継承
const modelOpt = A.model ? { model: A.model } : {}

const solved = await pipeline(
  perspectives,
  p => agent(`問い: ${question}

あなたの思考様式: ${p.stance}。この様式に忠実に、独立して問いに答えよ。
必要なら Read/Grep/Bash で事実を調べてよい（ファイル変更は禁止）。
出力: answer（結論）/ reasoning（根拠の要約、5行以内）/ confidence（high|medium|low）。`,
    { label: `solve:${p.key}`, phase: 'Solve', schema: SOLUTION, ...modelOpt })
    .catch(() => null),
  (sol, p) => {
    if (!sol) return null
    const verifyPrompt = `役割: 敵対的検証者。次の解答を反証せよ。
問い: ${question}
解答: ${sol.answer}
根拠: ${sol.reasoning}
手順: 前提の誤り・見落とした分岐・根拠の飛躍を探す。必要なら Read/Grep/Bash で事実を裏取りする。
出力: verdict（REFUTED=結論を変えうる欠陥あり / SURVIVED=反証失敗）と issues（発見した問題。なければ空配列）。`
    const verifyOpts = { label: `verify:${p.key}`, phase: 'Verify', schema: VERDICT, ...modelOpt }
    return agent(verifyPrompt, { ...verifyOpts, agentType: 'adversarial-verifier' })
      .catch(e => {
        log(`verify:${p.key}: adversarial-verifier で実行できないため汎用エージェントへフォールバック（${String(e).slice(0, 80)}）`)
        return agent(verifyPrompt, verifyOpts)
      })
      .catch(() => null)
      .then(v => v && { perspective: p.key, solution: sol, verdict: v })
  },
)

const candidates = solved.filter(Boolean).filter(c => c.verdict)
if (!candidates.length) throw new Error('全視点の推論または検証が失敗しました')

const survived = candidates.filter(c => c.verdict.verdict === 'SURVIVED')
const pool = survived.length ? survived : candidates // 全滅時は反証内容ごと審査に回す

const final = await agent(`役割: 審査員。次の問いに対する複数の独立解を比較し、最終解を統合せよ。
問い: ${question}

候補:
${pool.map(c => `--- 視点 ${c.perspective}（検証: ${c.verdict.verdict}${c.verdict.issues.length ? '、指摘: ' + c.verdict.issues.join(' / ') : ''}）
結論: ${c.solution.answer}
根拠: ${c.solution.reasoning}`).join('\n')}

手順: 一致点は採用。相違点は根拠の強さで裁定する。検証の指摘は最終解へ反映する。
出力: 最終解（結論 → 根拠 → 残る不確実性、の順で簡潔に）。`,
  { label: 'judge', phase: 'Judge', ...modelOpt })

log(`視点 ${perspectives.length} 件中、反証を生き残った解 ${survived.length} 件から統合`)
return { question, survivors: survived.map(c => c.perspective), final }
