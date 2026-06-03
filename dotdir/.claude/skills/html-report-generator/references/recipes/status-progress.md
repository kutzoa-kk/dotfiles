# Status / Progress Report Structure

Use for KPI dashboards, project status, weekly / monthly / quarterly business
reviews, OKR check-ins, sprint reviews.

The reader is typically a manager, exec, or cross-team stakeholder who has 90
seconds. They want to know: are we on track, what's the headline number, what
needs attention.

## Canonical section order

```
1. Header               — title, period, owner, status pip
2. Headline             — one-sentence "are we on track" + RAG status
3. KPI cards            — 4–8 metrics with delta vs comparison period
4. Trend charts         — the 2–3 metrics that matter most, over time
5. Highlights & lowlights — short bulleted wins and concerns
6. By-segment view      — tabs across products / teams / regions
7. Risks & blockers     — accordion, severity badges
8. Decisions needed     — explicit asks of the reader
9. Timeline / milestones — what's done, what's next
10. Appendix            — full data table, methodology
```

The combination of KPI cards + 2 trend charts + highlights/lowlights covers
about 80% of the "executive 90 seconds" use case. Everything below that is
for the reader who clicks through to dig deeper.

## RAG status

Display in the header:

```html
<dd>
  <span class="pip pip--success"></span> On track
</dd>
```

| State    | Pip color    | When                                                |
|----------|--------------|-----------------------------------------------------|
| On track | `pip--success` | All key indicators within tolerance               |
| At risk  | `pip--warning` | One or more indicators trending wrong, recoverable|
| Off track| `pip--danger`  | Cannot recover within the period without action   |

Use a single overall RAG plus per-area RAG inside the body if useful. Don't
list five greens and one red and call the report "green" — readers see through
that.

## KPI card conventions

- Pick 4–8 metrics that matter to the audience. More than 8 = dashboard.
- Every card shows the comparison delta. "128k" alone is useless; "128k (▲12% vs 前月)" is informative.
- Color the delta by **whether the change is good**, not by direction. Lower
  error rate → green; lower active-user count → red.
- Format numbers consistently: thousands separators, fixed decimal precision,
  currency symbol on the same side.

## Highlights & lowlights

Two short lists. Three to five items each, no more. Each item is one sentence.

```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
  <div class="card">
    <h3 class="chart-card__title flex items-center gap-2">
      <span class="pip pip--success"></span> Highlights
    </h3>
    <ul>
      <li>新規契約が目標比 +14%。</li>
      <li>p99 レイテンシを 280ms → 195ms に改善。</li>
    </ul>
  </div>
  <div class="card">
    <h3 class="chart-card__title flex items-center gap-2">
      <span class="pip pip--danger"></span> Lowlights
    </h3>
    <ul>
      <li>北米リージョンで継続率が 4pt 低下。</li>
      <li>セキュリティ監査の対応に遅延。</li>
    </ul>
  </div>
</div>
```

## Decisions needed

Explicit asks of the reader. Don't bury them in prose. Use a numbered list.

```html
<ol>
  <li><strong>承認:</strong> Q3 採用予算 +¥3M（人員2名追加）— 5/30 まで。</li>
  <li><strong>判断:</strong> 機能Xのリリース延期是非（責任者: …）。</li>
</ol>
```

If there are no decisions needed, omit the section — don't write "なし".

## Components typically used

| Section            | Components                                  |
|--------------------|---------------------------------------------|
| Headline           | `lead` paragraph + status pip               |
| KPI cards          | `grid` of `kpi`                             |
| Trend charts       | `chart-card` line / bar                     |
| Highlights / lowlights | Two-column compare grid                 |
| By-segment         | `tabs`                                      |
| Risks & blockers   | `accordion` + severity `badge`              |
| Timeline           | `timeline` component                        |
| Appendix           | `data-table` sortable                       |

## Common mistakes

- **"Everything is green"** when one number is concerning. Use per-area RAG
  and surface the concern.
- **No comparison.** Status without context is just data. Always vs target,
  vs prior period, or vs forecast.
- **Buried asks.** Readers scroll once. Put decisions-needed near the top, not
  on page 4.
- **Same chart 10 times for 10 teams.** Use tabs or a single grouped chart.
- **No trendline.** A KPI card without a sparkline next to it is half a story.

## Example skeleton

```html
<header class="pb-6 border-b border-border mb-6">
  <p class="eyebrow">Weekly status · W19 · 2026-05-12</p>
  <h1 class="m-0">Q2 ロードマップ進捗</h1>
  <p class="lead mt-3">全体としては予定どおり。北米セグメントの継続率低下に注意。</p>
  <dl class="flex flex-wrap gap-x-6 gap-y-2 text-muted text-sm mt-4 m-0">
    <span><dt class="inline font-medium text-faint">期間</dt><dd class="inline ml-1">W18 → W19</dd></span>
    <span><dt class="inline font-medium text-faint">ステータス</dt><dd class="inline ml-1"><span class="pip pip--warning"></span> At risk</dd></span>
  </dl>
</header>
```

## Cadence note

The structure scales down cleanly for shorter cadences:

| Cadence  | Sections to keep                                              |
|----------|---------------------------------------------------------------|
| Weekly   | Header → Headline → KPI → Highlights/Lowlights → Decisions    |
| Monthly  | Above + Trend charts + Risks + Timeline                       |
| Quarterly| Full structure                                                |

Don't keep all sections for a weekly report — it pads the doc and dilutes signal.
