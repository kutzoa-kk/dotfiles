# Data Analysis Report Structure

Use for EDA, A/B test results, ML experiment write-ups, dataset profiling,
investigation reports.

The reader is usually a teammate or stakeholder who wants to know: what did you
look at, what did you find, do you trust it, what should we do. Lead with the
answer, then show the work.

## Canonical section order

```
1. Header               — title, period, author, status
2. TL;DR                — 3–5 sentences. The answer first.
3. KPI summary          — 3–6 KPI cards. Movement vs comparison period.
4. Methodology          — data sources, period, filters, definitions.
5. Findings             — one section per finding, with chart + caption.
6. Segments / cuts      — tabs across segments (region, cohort, channel...).
7. Caveats              — known data quality issues, confounders, limitations.
8. Recommendations      — concrete next steps, owners, dates.
9. Appendix             — full data tables, query SQL, reproducibility notes.
```

`TL;DR` is non-negotiable. Skim-readers should be able to leave knowing the
answer without scrolling past the first viewport.

## Per-finding structure — 目的 → 手法 → 結果 → 考察 (IMRaD per section)

Each **Findings** section (one per analysis/experiment) should carry the reader
through *why → how → what → so-what* with explicit, labelled blocks. This is the
IMRaD shape applied at the section level, and it is the default for research/EDA/
experiment write-ups (especially Japanese ones):

1. **目的 (Purpose)** — what this analysis tests and *why*, in 1–2 sentences.
   Motivate it from the previous finding when there is a narrative thread.
2. **手法 (Method)** — data source, population, N, the analysis/estimator, and
   the threshold (say so if pre-registered). Terse but reproducible.
3. **結果 (Results)** — the figure/table and numbers. Every chart gets a
   one-sentence caption stating *what the reader should notice*.
4. **考察 (Discussion)** — interpretation, conclusion, and honest limitations
   (never over- or under-state modest/FAIL/confounded results). Hand off to the
   next section when the finding drives it.

Give each of the four a distinct visual treatment (a coloured left-border callout
for 目的/手法/考察, an underlined label for 結果) so that, across many sections,
a reader can skim just the 目的 and 考察 blocks and follow the whole arc — what
each step set out to show and what it actually showed. In multi-increment
investigations this is what makes the through-line legible.

```css
.aim   {border-left:5px solid var(--slate); background:#eef4f8; border-radius:0 8px 8px 0; padding:.9rem 1.2rem}
.method{border-left:5px solid var(--muted); background:#f4f5f6; border-radius:0 8px 8px 0; padding:.9rem 1.2rem}
.rlabel{border-bottom:2px solid var(--border); font-weight:700; letter-spacing:.12em; padding-bottom:.25rem}
.disc  {border-left:5px solid var(--gold);  background:#fbf6ec; border-radius:0 8px 8px 0; padding:.9rem 1.2rem}
/* 各ブロックの <h4> は小さめ・トラッキング広め（.78rem, letter-spacing:.1em）でラベル化 */
```

Skip the four-part labelling only for the overview (TL;DR) and the final synthesis/
recommendation section — those *are* the top-level 目的 and 考察 for the whole report.

## Minimum viable version

Some analyses are short. The shortest acceptable structure:

```
Header → TL;DR → KPI summary → 2–3 findings → Recommendations
```

Skip methodology and appendix only when both: (a) the audience knows the data
already, and (b) the analysis is small enough that reproducing it from scratch
is trivial.

## Components typically used

| Section          | Components                                  |
|------------------|---------------------------------------------|
| TL;DR            | lead paragraph + maybe one inline pip       |
| KPI summary      | `kpi` cards in `grid`                       |
| Methodology      | description list, code block for SQL        |
| Findings         | `chart-card` (Chart.js or Plotly), `card`   |
| Segments         | `tabs` containing charts or small tables    |
| Caveats          | `accordion` of items, severity `badge`s     |
| Recommendations  | ordered list, optionally with timeline      |
| Appendix         | sortable `data-table`, raw CSV link         |

## Chart conventions

- One chart per finding. If a section needs more than two charts, split it.
- Always include a one-sentence caption directly below the chart explaining
  what the reader should notice. Don't make them squint at the line and guess.
- Use `--color-series-1` for the primary metric; reserve other series for
  comparison cohorts or breakdowns.
- Y-axis starts at zero **unless** zoom is needed to show the signal, in which
  case label that fact explicitly.
- Annotate notable events on the chart (deploy date, campaign launch) — a
  vertical line plus a label beats "see context paragraph below".

## Common mistakes

- **Burying the lede.** Don't open with three pages of data cleaning before
  saying what you found.
- **Pie chart with 12 slices.** Use a horizontal bar chart sorted descending.
- **No comparison.** A single number is meaningless. Always show vs previous
  period, vs control, vs target.
- **No caveats.** Every analysis has assumptions or known gaps; calling them
  out builds trust.
- **Confusing absolute vs relative.** "Up 12%" — points? percent? percent of
  base? Be explicit.

## Example skeleton

```html
<section id="tldr" data-toc="TL;DR">
  <h2 class="mt-0 pt-0 border-0">TL;DR</h2>
  <p class="lead">2026年4月のチャーン率は3.4%で、3月比 +0.8pt。原因は無料プラン経由の新規ユーザーが90日後に大量離脱したこと。短期施策2点を推奨。</p>
</section>

<section id="kpi" data-toc="主要指標">
  <h2>主要指標</h2>
  <div class="grid gap-4 my-6" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
    <!-- kpi cards -->
  </div>
</section>

<section id="methodology" data-toc="計測方法">
  <h2>計測方法</h2>
  <ul>
    <li><strong>データ:</strong> events.user_activity（2026-01-01〜2026-04-30）</li>
    <li><strong>定義:</strong> チャーン = 30日間アクティビティなし</li>
    <li><strong>除外:</strong> internal accounts, qa@*</li>
  </ul>
</section>

<section id="findings" data-toc="発見">
  <h2>発見</h2>
  <h3>1. 無料プラン経由のユーザーで離脱集中</h3>
  <div class="chart-card">…</div>
  <p>無料プラン経由ユーザーの90日継続率は18%。有料経由は74%で、差は56pt。</p>
</section>
```

## When to also include "for ML experiments"

If this is an ML experiment, add these:

- **Hypothesis** at the top, written before training (link git commit).
- **Train / val / holdout split policy** in Methodology.
- **Multiple comparison correction** disclosed (Bonferroni / BH-FDR).
- **Total runs** including failed and discarded — full reporting, no cherry-picking.
- **Deviation log** if anything diverged from the pre-registered plan.

These line up with the SDD ML reporting rules (R8 anti-sycophancy, R10 full
reporting). See `sdd-report-generator` skill if the project uses that framework.
