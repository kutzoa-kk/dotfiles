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

const COMMON = `対象: /Users/kkmclab/dotfiles（git 実体）と /Users/kkmclab/.claude（稼働環境）。
環境知識: merge リンク構造（実体は dotdir/.claude/）。settings.json は外部ツール orca が hooks を注入し得る。
settings.json の所有モデル（docs/settings-ownership.md）: git=種／稼働=ライブ。稼働側にのみ存在するキー（model・enabledPlugins・extraKnownMarketplaces・orca 注入 hooks 等）は設計どおりでありドリフトではない。報告するのは「恒久設定が make settings-pull で種へ吸い上げられていない疑い」がある場合のみ。
プラグインの数え方: installed（キャッシュ存在）と enabled（settings.json の enabledPlugins が true）を区別し、常駐カウントは enabled のみ。ecc の SKILL.md 数は言語ミラー（es/tr 等）を除いた distinct 数で数える。
制約: 読み取り専用 — いかなるファイルも変更・削除しないこと。
出力: 所見リスト。evidence には必ずパスと数値（行数・個数・サイズ）を含める。該当なしなら findings: [] を返す。`

// Workflow ランタイムは args を JSON 文字列で渡す場合があるため両対応にする
const A = typeof args === 'string' ? JSON.parse(args) : (args ?? {})

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
return { date: A.date ?? 'unset', total: all.length, findings: all }
