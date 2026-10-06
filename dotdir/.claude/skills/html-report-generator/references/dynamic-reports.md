# Dynamic Reports

Use when the reader should **explore the data themselves** — filter, drill
down, switch periods, change a threshold and see the numbers recompute — and
when the data will be **refreshed** without rewriting the report.

This is a different kind of artifact from the static report. The static rules
in [interactivity.md](interactivity.md) ("reports are snapshots", "no live
data") are relaxed here in one controlled way: the data lives in a single
replaceable JSON block, and everything on the page is derived from it in the
browser. The file is still one `.html` that opens from `file://`.

## Which kind of artifact?

| The reader wants to… | Make |
|----------------------|------|
| Read conclusions you already drew | Static report (`assets/base.html`) |
| Tune a value and copy it back to Claude | Playground ([interactive-playgrounds.md](interactive-playgrounds.md)) |
| Slice the data, drill into a group, ask "what if the cut-off were 1.0?" | **Dynamic report** (this file) |
| Many people editing shared state, or data that must update every minute | A real app / dashboard — out of scope |

A dynamic report still states its findings in prose at the top. The controls
let readers check and extend the findings; they don't replace them. A page
that is only filters and charts reads as a tool, not a report.

## Architecture: one state, one direction

```
<script id="report-data">  →  state (filters, threshold, selection)
                                   │
                         derive(rows, state)   ← pure functions, no DOM
                                   │
                         render(view)           ← every chart / table / KPI
```

Rules that keep it from turning into spaghetti:

1. **Data is embedded, never fetched.** `fetch('data.json')` fails from
   `file://` in Chrome. Put the rows in
   `<script id="report-data" type="application/json">` and parse once.
2. **One `state` object** holds every control value. Controls only write to
   `state` and call `update()`. Nothing else mutates `state`.
3. **`derive()` is pure.** It takes rows + state and returns a `view` object
   (filtered rows, aggregates, chart series). No DOM access, so it can be
   checked in the console or a test.
4. **`render(view)` redraws everything** from the view. Charts are created
   once and updated with `chart.data = …; chart.update()`; tables re-render
   their `tbody`. Don't patch individual elements from inside event handlers.
5. **Linked views and drill-down use the same path.** Clicking a bar sets
   `state.group = 'A'` and calls `update()`; the other charts and the table
   follow automatically. Show the active selection as a removable chip so the
   reader knows why the numbers changed.

```html
<script id="report-data" type="application/json">{"meta":{"source":"cohort.csv","updated":"2026-10-06T09:00:00+09:00","n_rows":3},"rows":[{"id":"001","group":"A","age":72,"speed":1.05}]}</script>
```

```js
(function () {
  const DATA = JSON.parse(document.getElementById('report-data').textContent);
  const state = { group: 'all', minAge: 65, cutoff: 1.0 };

  function derive(rows, s) {
    const sel = rows.filter(r =>
      (s.group === 'all' || r.group === s.group) && r.age >= s.minAge);
    const speeds = sel.map(r => r.speed).filter(v => v != null);
    const below = speeds.filter(v => v < s.cutoff).length;
    return {
      rows: sel,
      n: speeds.length,
      mean: mean(speeds),
      belowRate: speeds.length ? below / speeds.length : null,
      byGroup: groupBy(sel, r => r.group, g => mean(g.map(r => r.speed))),
    };
  }

  function update() {
    const view = derive(DATA.rows, state);
    render(view);
    writeHash(state);
  }

  document.querySelectorAll('[data-state]').forEach(el => {
    el.addEventListener('input', () => {
      const key = el.dataset.state;
      state[key] = el.type === 'range' || el.type === 'number' ? Number(el.value) : el.value;
      update();
    });
  });

  Object.assign(state, readHash());
  syncControls(state);   // set each control's value from state (after hash restore)
  update();
})();
```

`render`, `mean`, `groupBy`, `syncControls`, `readHash` and `writeHash` are
short helpers; write them per report. Keep them in the same IIFE as the
rest of the page's JS (see "Adding a sixth behavior" in
[interactivity.md](interactivity.md)).

## Recomputation (what-if)

When a control changes a threshold, a grouping, or an inclusion criterion and
the statistics recompute:

- **Show n next to every number.** "平均 1.02 m/s（n = 48）". When n drops
  below a floor you choose for the analysis (e.g. 20), grey the value and say
  why ("n < 20 のため参考値"). An empty selection shows "該当データなし",
  never `NaN` or a blank chart.
- **Label recomputed results as exploratory.** Moving a cut-off until a
  difference appears is exactly how chance findings get reported. Put the
  pre-specified setting first, mark it as the default (and the reset target),
  and add a one-line note near the controls:
  "既定値は事前の仮説で定めた条件です。条件を変えた結果は探索的な参考値です。"
- **Keep computations transparent.** Means, medians, proportions, quantiles,
  simple differences: compute in JS and say how in a caption. Anything needing
  a model fit (regression, CI from a mixed model, survival curves) should be
  precomputed in Python/R per setting and embedded as a lookup table keyed by
  the control values — don't re-implement statistics in the browser.
- **Bounded controls.** Sliders get `min`/`max`/`step` that match plausible
  values, with an `<output>` readout. Free-text numbers invite typos.

## Data refresh

The data block is the only part of the file that changes between versions:

```bash
python scripts/inject_data.py report.html new-data.csv
python scripts/inject_data.py report.html new-data.json --out report-2026-11.html
```

`inject_data.py` replaces the contents of `<script id="report-data">` with
`{"meta": {source, updated, n_rows}, "rows": [...]}`. CSV cells become numbers
where they look numeric (leading-zero IDs like `007` stay strings); empty cells
become `null`, so `derive()` must skip nulls rather than treat them as 0.

For this to work, the report must:

- Read **only** from `DATA.rows` — no numbers hard-coded in prose or KPI
  markup. Text that states a finding either derives its numbers too, or says
  which data version it was written against ("本文の数値は 2026-10-06 版のデータに基づく").
- Show `DATA.meta.updated` and `DATA.meta.n_rows` in the header, so a reader
  can tell which version they're looking at.
- Derive category lists (filter options, chart labels) from the data, not
  from a hand-written list, so a new group appears automatically.

Live polling (`setInterval` + `fetch`) is out of scope: it needs a server and
breaks the single-file share. If the user truly needs that, say so and
suggest a real dashboard.

## Shareable view state

Write `state` to `location.hash` (`#group=A&cutoff=1.1`) on every update and
read it on load. Then a link reproduces the exact view the sender saw — useful
when someone says "look at group A above 75".

Keep the two-way loop from the rest of this skill: a **"今の条件と結果をコピー"**
button that copies `{state, n, key numbers}` as Markdown or JSON, so the reader
can paste it back to Claude.

## Size and performance

| Rows embedded | Approach |
|---------------|----------|
| up to ~20k | Raw rows, plain array methods. Fine on every `input` event. |
| ~20k–200k | Raw rows, but debounce slider input (~100 ms) and render tables paginated (50 rows). |
| more | Pre-aggregate in Python to the granularity the controls need and embed that instead. Link the raw CSV. |

Keep the file under ~5 MB. Personal or identifying data never goes in the
embedded block — de-identify or aggregate before injecting; the whole dataset
is readable by anyone who opens the file.

## Verifying

Static checks from SKILL.md still apply. In addition:

1. **Headless run.** Open the file with Playwright (or the `playwright-cli`
   skill), change at least two controls, and assert the n readout and one
   aggregate match a value computed independently (pandas / a one-liner).
   Assert on `derive()` output or `Chart.getChart(id).data`, not on a
   screenshot: Chart.js animates from zero, so a screenshot taken right after
   load shows bars at a fraction of their height.
2. **Empty selection.** Pick a filter combination that matches nothing and
   confirm "該当データなし" appears and the console has no errors.
3. **Refresh path.** Run `inject_data.py` with a modified dataset, reload,
   and confirm the header's 更新日時 / 件数 and the numbers changed.
4. **Hash round-trip.** Load the page with a hash and confirm the controls and
   numbers reflect it.

## Common mistakes

- **Numbers in prose that silently go stale** after a data refresh. Either
  derive them or pin them to a dated data version.
- **Charts recreated on every input.** Chart.js leaks canvases and flickers;
  create once, then `update()`.
- **Category lists hard-coded** in `<select>` options — a new site or group in
  the next dataset never shows up.
- **Filters that interact invisibly.** If three filters are active, show three
  chips with a "すべて解除" link.
- **`null` treated as 0** in means and counts.
- **Data values interpolated into `innerHTML`.** A free-text cell containing
  `<img onerror=…>` runs as markup. Build rows with `textContent`, or escape
  `& < > " '` before templating.
- **No default view.** On first load the page should show the pre-specified
  analysis, not an empty "choose filters" screen.
