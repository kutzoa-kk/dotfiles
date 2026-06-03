# Components

Copy-paste-ready snippets that pair with `assets/base.html`. The base
scaffold provides:

- Design tokens as CSS variables (`--color-ink`, `--color-bg`, `--color-accent`,
  `--color-series-*`, `--font-sans`, etc.).
- Component classes (`.kpi`, `.card`, `.chart-card`, `.data-table`, `.tabs__*`,
  `.accordion`, `.badge`, `.pip`, `.timeline`, `.architecture`).
- JS wiring for TOC scroll-spy, tabs, sortable / filterable tables, and the
  light / dark toggle.
- Tailwind v4 (browser CDN) scanning utility classes from markup, so common
  shortcuts (`mt-3`, `flex gap-3`, `grid-cols-2`) work inline. Note that
  Tailwind's `@theme` and `@apply` are NOT processed in browser mode — design
  tokens come from the plain `<style>` block in `base.html`, not from `@theme`.

Tailwind utility classes in snippets are convenience only; you can replace
any of them with plain CSS without breaking anything.

For libraries that need a separate CDN script (Plotly, ECharts), add the
`<script>` tag in `<head>` next to the existing Chart.js / Mermaid tags.

---

## KPI cards

Use at the top of dashboards and status reports. 3–6 cards; more than 6 and
readers stop looking.

```html
<div class="grid-kpi">
  <div class="kpi">
    <p class="kpi__label">Active users</p>
    <div class="kpi__value">128,420</div>
    <div class="kpi__delta kpi__delta--up">▲ 12.4% vs 前月</div>
  </div>
  <div class="kpi">
    <p class="kpi__label">Error rate</p>
    <div class="kpi__value">0.42%</div>
    <div class="kpi__delta kpi__delta--down">▼ 0.08pt vs 前月</div>
  </div>
</div>
```

`--down` is red and `--up` is green, but pick the modifier by **whether the
change is good or bad**, not by the arrow direction. Error rate going down is
good — use `kpi__delta--up` (or add a `--flat` variant if neutral).

---

## Chart.js — line / bar / doughnut

Wrap every chart in `chart-card` for consistent framing. The `.chart-wrap`
class sets a fixed 320 px height so the chart doesn't reflow.

```html
<div class="chart-card">
  <div class="chart-card__header">
    <h3 class="chart-card__title">Weekly revenue</h3>
    <span class="chart-card__meta">¥ thousands</span>
  </div>
  <div class="chart-wrap"><canvas id="chart-revenue" aria-label="週次売上推移"></canvas></div>
  <details class="mt-3">
    <summary class="caption cursor-pointer">データを表で見る</summary>
    <table class="data-table mt-3">
      <thead><tr><th>週</th><th class="num">売上</th></tr></thead>
      <tbody>
        <tr><td>W18</td><td class="num">8,420</td></tr>
        <tr><td>W19</td><td class="num">9,103</td></tr>
      </tbody>
    </table>
  </details>
</div>

<script>
window.addEventListener('load', () => {
  const cs = getComputedStyle(document.documentElement);
  const t = n => cs.getPropertyValue(n).trim();
  new Chart(document.getElementById('chart-revenue'), {
    type: 'line',
    data: {
      labels: ['W18','W19','W20','W21','W22'],
      datasets: [{
        label: 'Revenue',
        data: [8420, 9103, 8890, 9550, 10120],
        borderColor: t('--color-series-1'),
        backgroundColor: `color-mix(in oklch, ${t('--color-series-1')}, transparent 80%)`,
        borderWidth: 2, tension: 0.3, pointRadius: 0, fill: true,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } }, y: { beginAtZero: false } },
    },
  });
});
</script>
```

**Bar:** change `type: 'bar'`, drop `tension` / `fill`. For grouped bars, supply
multiple datasets, each using `--color-series-1`, `--color-series-2`, etc.

**Doughnut:** `type: 'doughnut'`, `data.datasets[0].backgroundColor` as an array
of `t('--color-series-1') … t('--color-series-6')`.

---

## Plotly — when Chart.js isn't enough

Add the CDN script in `<head>`:

```html
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js" defer></script>
```

```html
<div class="chart-card">
  <div class="chart-card__header">
    <h3 class="chart-card__title">Latency heatmap</h3>
    <span class="chart-card__meta">hover for cell value</span>
  </div>
  <div id="plotly-heatmap" class="h-[360px]" aria-label="Latency heatmap"></div>
</div>

<script>
window.addEventListener('load', () => {
  const cs = getComputedStyle(document.documentElement);
  const t = n => cs.getPropertyValue(n).trim();
  Plotly.newPlot('plotly-heatmap', [{
    z: [[0.12,0.18,0.22],[0.10,0.14,0.19],[0.08,0.11,0.15]],
    x: ['p50','p95','p99'], y: ['Mon','Tue','Wed'],
    type: 'heatmap',
    colorscale: [[0, t('--color-surface-2')], [1, t('--color-series-1')]],
    showscale: true,
  }], {
    margin: { l: 60, r: 20, t: 10, b: 40 },
    font: { family: t('--font-sans'), color: t('--color-muted'), size: 12 },
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
  }, { displayModeBar: false, responsive: true });
});
</script>
```

---

## Sortable / filterable / searchable table

Already wired by base.html. Wrap the table in `[data-sortable-table]`, mark
each header with `data-sort="string|number|date"`, and you're done.

```html
<div class="my-6" data-sortable-table>
  <div class="table-toolbar no-print">
    <input type="search" placeholder="検索…" data-table-search>
    <select data-table-filter="status">
      <option value="">すべて</option>
      <option value="passed">passed</option>
      <option value="failed">failed</option>
    </select>
  </div>
  <table class="data-table">
    <thead>
      <tr>
        <th data-sort="string">Test <span class="sort-indicator">↕</span></th>
        <th data-sort="string">Status <span class="sort-indicator">↕</span></th>
        <th data-sort="number" class="num">Duration ms <span class="sort-indicator">↕</span></th>
      </tr>
    </thead>
    <tbody>
      <tr><td>auth/login</td><td><span class="badge badge--success">passed</span></td><td class="num">142</td></tr>
      <tr><td>auth/logout</td><td><span class="badge badge--critical">failed</span></td><td class="num">820</td></tr>
    </tbody>
  </table>
</div>
```

For more than ~300 rows, paginate or link to the raw CSV. Don't dump 5,000 rows
into HTML.

---

## Tabs

Already wired by base.html. Wrap the group in `[data-tabs]`, give each trigger
an `aria-controls` pointing at its panel.

```html
<div class="my-6" data-tabs>
  <ul class="tabs__list" role="tablist">
    <li role="presentation"><button class="tabs__trigger" role="tab" aria-selected="true"  aria-controls="t-overview" id="tt-overview">Overview</button></li>
    <li role="presentation"><button class="tabs__trigger" role="tab" aria-selected="false" aria-controls="t-detail"   id="tt-detail">Detail</button></li>
  </ul>
  <div class="tabs__panel" id="t-overview" role="tabpanel" aria-labelledby="tt-overview" aria-hidden="false">…</div>
  <div class="tabs__panel" id="t-detail"   role="tabpanel" aria-labelledby="tt-detail"   aria-hidden="true">…</div>
</div>
```

---

## Accordion

Pure HTML. Each item is independent and the page would be too long if
everything were expanded.

```html
<div class="accordion">
  <details>
    <summary>R-01 データ品質に依存する仮説 <span class="badge badge--high">High</span></summary>
    <div class="accordion__body"><p>背景 / 現状 / アクション / 期限 / 担当。</p></div>
  </details>
  <details open>
    <summary>R-02 ロールバック手順 <span class="badge badge--medium">Medium</span></summary>
    <div class="accordion__body"><p>本文。</p></div>
  </details>
</div>
```

---

## Severity / status badge

```html
<span class="badge badge--critical">Critical</span>
<span class="badge badge--high">High</span>
<span class="badge badge--medium">Medium</span>
<span class="badge badge--low">Low</span>
<span class="badge badge--success">Resolved</span>
```

Inline status pip — smaller, no border:

```html
<span class="pip pip--success"></span> Healthy
<span class="pip pip--warning"></span> Degraded
<span class="pip pip--danger"></span> Down
```

---

## Timeline

```html
<ol class="timeline">
  <li>
    <p class="timeline__date">2026-05-12 09:14 JST</p>
    <p class="timeline__title">アラート発火</p>
    <p>p99レイテンシが閾値超過。</p>
  </li>
  <li>
    <p class="timeline__date">2026-05-12 09:21 JST</p>
    <p class="timeline__title">原因特定</p>
    <p>新規デプロイのconnection pool設定ミス。</p>
  </li>
  <li>
    <p class="timeline__date">2026-05-12 09:33 JST</p>
    <p class="timeline__title">ロールバック完了</p>
    <p>全リージョンで指標が正常範囲に復帰。</p>
  </li>
</ol>
```

---

## Mermaid diagram

```html
<div class="architecture">
  <pre class="mermaid">
sequenceDiagram
  autonumber
  participant U as User
  participant W as Web
  participant A as API
  participant D as DB
  U->>W: Click "Save"
  W->>A: POST /items
  A->>D: INSERT
  D-->>A: id=42
  A-->>W: 201 Created
  W-->>U: Success toast
  </pre>
</div>
```

Mermaid is already initialized by base.html with theme-matched colors. Use it
for flowcharts, sequence diagrams, ER diagrams, state diagrams, and gantt charts.

---

## Code block with title

```html
<figure class="card p-0 overflow-hidden">
  <figcaption class="caption px-4 py-3 border-b border-border bg-surface-2">
    src/auth/handler.ts
  </figcaption>
  <pre class="border-0 rounded-none m-0"><code>export async function handle(req: Request) {
  // ...
}</code></pre>
</figure>
```

For syntax highlighting, add highlight.js or Shiki via CDN if it matters
enough. Most reports don't need it.

---

## Two-column compare grid

```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
  <div class="card">
    <h3 class="chart-card__title">Before</h3>
    <p>状態の説明。</p>
  </div>
  <div class="card">
    <h3 class="chart-card__title">After</h3>
    <p>状態の説明。</p>
  </div>
</div>
```

---

## Callout / aside

Use sparingly — one or two per report. Stacking callouts loses signal.

```html
<aside class="card border-l-[3px] border-l-accent">
  <p class="font-medium m-0">💡 推奨</p>
  <p class="mt-2 mb-0">この変更はベースラインの計測完了後に適用すること。</p>
</aside>
```

For warning / danger callouts, swap `border-l-accent` for `border-l-warning`
or `border-l-danger`.

---

## Empty state

When a section legitimately has nothing to show, say so explicitly:

```html
<div class="card" style="text-align:center;color:var(--color-muted);">
  <p style="margin:0;">該当データなし</p>
  <p class="caption" style="margin-top:0.5rem;">期間内に該当するイベントはありませんでした。</p>
</div>
```

Don't silently omit the section — readers wonder if you forgot.

---

## Copy-as-prompt button

For any artifact where the user makes choices and wants to hand the result
back to Claude. See [references/interactive-playgrounds.md](../../references/interactive-playgrounds.md)
for the full pattern.

```html
<button type="button" class="copy-btn" data-copy-source="config">
  Copy as prompt
</button>

<style>
  .copy-btn {
    padding: 0.5rem 1rem;
    background: var(--color-accent);
    color: white;
    border: 0;
    border-radius: 6px;
    font: inherit;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 120ms ease;
  }
  .copy-btn:hover { opacity: 0.9; }
  .copy-btn[data-state="copied"] { background: var(--color-success); }
</style>

<script>
document.querySelectorAll('.copy-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const text = typeof window[btn.dataset.copySource] === 'function'
      ? window[btn.dataset.copySource]()
      : (btn.dataset.copyText || '');
    await navigator.clipboard.writeText(text);
    const original = btn.textContent;
    btn.dataset.state = 'copied';
    btn.textContent = 'Copied ✓';
    setTimeout(() => {
      btn.dataset.state = '';
      btn.textContent = original;
    }, 1200);
  });
});
</script>
```

Wire it by either:
- `data-copy-text="..."` for a static string, or
- `data-copy-source="config"` plus a global function `window.config = () => "..."`
  that returns the current state.

---

## Slider with live readout

```html
<label class="slider-row">
  <span class="caption">Duration</span>
  <input type="range" min="0" max="2000" step="50" value="280"
         data-bind="duration">
  <output data-output="duration">280</output>
  <span class="caption">ms</span>
</label>

<style>
  .slider-row {
    display: grid;
    grid-template-columns: 6rem 1fr 4rem auto;
    gap: 0.75rem;
    align-items: center;
    padding: 0.5rem 0;
  }
  .slider-row input[type="range"] { width: 100%; accent-color: var(--color-accent); }
  .slider-row output { font-family: var(--font-mono); font-size: 0.85rem; text-align: right; }
</style>

<script>
document.querySelectorAll('[data-bind]').forEach(input => {
  const update = () => {
    const out = document.querySelector(`[data-output="${input.dataset.bind}"]`);
    if (out) out.textContent = input.value;
  };
  input.addEventListener('input', update);
  update();
});
</script>
```

---

## Draggable card column

For triage / bucketing UIs. See [references/editing-interfaces.md](../../references/editing-interfaces.md)
for the full draggable-board pattern.

```html
<div class="board-column" data-column="now">
  <header><h2>Now</h2></header>
  <ul class="board-list">
    <li class="board-card" draggable="true" data-id="TKT-101">
      <strong>TKT-101</strong>
      <p>Fix login redirect loop.</p>
    </li>
  </ul>
</div>

<style>
  .board-column {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 0.75rem;
    min-height: 200px;
  }
  .board-column.is-drop-target {
    border-color: var(--color-accent);
    background: color-mix(in oklch, var(--color-accent), transparent 92%);
  }
  .board-list { list-style: none; padding: 0; margin: 0; min-height: 100px; }
  .board-card {
    background: var(--color-surface-2);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    cursor: grab;
  }
  .board-card.is-dragging { opacity: 0.4; }
</style>
```

JS for drag-drop is in `references/editing-interfaces.md` (it's ~20 lines
and depends on how many columns you have).

---

## Diff row (code review)

```html
<table class="diff-table">
  <tr class="diff-row diff-row--ctx"><td class="diff-line">40</td><td class="diff-code">if (queue.length &gt;= MAX) {</td><td class="diff-note"></td></tr>
  <tr class="diff-row diff-row--add"><td class="diff-line">41</td><td class="diff-code">  queue.shift();</td><td class="diff-note"><span class="badge badge--critical">Silent drop</span></td></tr>
  <tr class="diff-row diff-row--ctx"><td class="diff-line">42</td><td class="diff-code">}</td><td class="diff-note"></td></tr>
</table>

<style>
  .diff-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    overflow: hidden;
  }
  .diff-row td { padding: 0.25rem 0.75rem; vertical-align: top; }
  .diff-line  { color: var(--color-faint); user-select: none; width: 3rem; text-align: right; }
  .diff-code  { white-space: pre; }
  .diff-note  { width: 28%; font-family: var(--font-sans); font-size: 0.8rem; }
  .diff-row--add { background: color-mix(in oklch, var(--color-success), transparent 92%); }
  .diff-row--del { background: color-mix(in oklch, var(--color-danger),  transparent 92%); }
  .diff-row--add .diff-code::before { content: "+ "; color: var(--color-success); }
  .diff-row--del .diff-code::before { content: "− "; color: var(--color-danger);  }
  .diff-row--ctx .diff-code::before { content: "  "; }
</style>
```

See [references/code-review.md](../../references/code-review.md) for full
PR-review report structure.

---

## Inline SVG icon (one-off)

```html
<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
  <path d="M3 8l3 3 7-7" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

Inline SVGs inherit `currentColor` so they pick up the surrounding text color.
For full diagrams see [references/svg-and-diagrams.md](../../references/svg-and-diagrams.md).

---

## Sparkline

A tiny inline chart for one-line indicators.

```html
<p>
  CPU usage <strong>62%</strong>
  <svg width="80" height="20" viewBox="0 0 80 20"
       style="vertical-align: middle;" aria-label="CPU sparkline">
    <polyline points="0,15 10,12 20,10 30,8 40,6 50,9 60,5 70,4 80,6"
              fill="none" stroke="var(--color-series-1)" stroke-width="1.5"/>
  </svg>
  trending down
</p>
```
