# Interactivity Reference

The base template ships with five JS-driven behaviors. They all live in one
`<script>` block at the bottom of `<body>`. This file explains how each one
works so you can adapt or extend them without breaking the others.

## 1. Theme toggle (auto → light → dark → auto)

The toggle cycles through three states stored in `localStorage`:

- `auto`: follow OS preference via `prefers-color-scheme`.
- `light`: force light, regardless of OS.
- `dark`: force dark, regardless of OS.

Implementation summary:

```js
const root = document.documentElement;
const apply = mode => {
  root.dataset.theme = mode;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  root.classList.toggle('is-dark', mode === 'dark' || (mode === 'auto' && prefersDark));
};
apply(localStorage.getItem('theme') || 'auto');
```

Color tokens are redeclared under `:where(.is-dark)` in the regular `<style>`
block of `base.html`. So flipping the class flips the entire palette.

When a report has no need for dark mode, delete:
- the `<button class="theme-toggle">` element
- the theme-toggle IIFE
- the `:where(.is-dark) { ... }` block

## 2. TOC build + scrollspy

The TOC is built at runtime from `<section data-toc="ラベル">` elements. Adding
or removing a section automatically updates the TOC — no manual sync needed.

```js
const sections = document.querySelectorAll('section[data-toc]');
sections.forEach(s => /* create <a href="#id">label</a> */);

const obs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) markLinkActive(e.target);
  });
}, { rootMargin: '-40% 0px -55% 0px', threshold: 0 });
```

`rootMargin: '-40% 0px -55% 0px'` shrinks the viewport for the spy so a section
is considered "active" only when it occupies the middle 5% strip of the screen.
This eliminates the flicker that happens when sections are short and a long
scroll passes through several quickly.

If a report has nested headings you want in the TOC (sub-items), add a
secondary `<ul>` inside the section's `<li>`. The current implementation only
handles one level; extending to two levels takes ~10 lines.

## 3. Tabs

Multiple `[data-tabs]` instances per page work independently. Each instance:
- has a `<ul class="tabs__list" role="tablist">` with `<button role="tab">`s
- each tab button has `aria-controls="<panel-id>"`
- each panel has matching `id`, `role="tabpanel"`, `aria-labelledby="<button-id>"`

Initial visible panel is whichever button has `aria-selected="true"`. Only one
per group.

The handler toggles `aria-selected` and `aria-hidden` — that's the whole
behavior. CSS keys off those attributes for styling.

Keyboard accessibility: the buttons already get focus via Tab; left/right
arrow support is a 10-line addition if needed:

```js
group.addEventListener('keydown', e => {
  const tabs = [...group.querySelectorAll('[role="tab"]')];
  const i = tabs.indexOf(document.activeElement);
  if (i < 0) return;
  if (e.key === 'ArrowRight') tabs[(i + 1) % tabs.length].focus();
  if (e.key === 'ArrowLeft')  tabs[(i - 1 + tabs.length) % tabs.length].focus();
});
```

## 4. Sortable / filterable / searchable table

Each `[data-sortable-table]` wraps:
- an optional toolbar with `<input data-table-search>` and one or more
  `<select data-table-filter="key">` elements
- a `<table class="data-table">` with `<th data-sort="string|number|date">` on
  each sortable column

The table caches the original row list at startup. Sort re-orders that array
and re-appends to `tbody`. Search and filter set `display: none` on rows that
don't match — no removal, so re-applying is cheap.

For datasets large enough that searching 5,000 rows feels slow:
- paginate (cap visible rows to ~50, add prev / next buttons)
- or replace with a virtualized library — but that's nearly always overkill
  for a static report; if the data is that big, link to the CSV.

The filter keys are loose `includes` matches against the row's full text. For
precise column-scoped filters, switch the parser to read a specific `<td>`:

```js
filters.forEach(f => f.addEventListener('change', () => {
  const colIdx = parseInt(f.dataset.col, 10);
  const want = f.value.toLowerCase();
  rows.forEach(r => {
    const cellText = r.children[colIdx].textContent.toLowerCase();
    r.style.display = !want || cellText.includes(want) ? '' : 'none';
  });
}));
```

## 5. Chart.js theme + Mermaid init

Both libraries get their defaults overridden so they pull from the CSS theme
tokens. This is the critical step that prevents the "looks like Chart.js, not
like our design system" smell.

```js
const cs = getComputedStyle(document.documentElement);
const t = name => cs.getPropertyValue(name).trim();
Chart.defaults.font.family = t('--font-sans');
Chart.defaults.color       = t('--color-muted');
Chart.defaults.borderColor = t('--color-border');
```

For each chart you create, use the `--color-series-N` tokens explicitly:

```js
borderColor: t('--color-series-1'),
backgroundColor: `color-mix(in oklch, ${t('--color-series-1')}, transparent 80%)`,
```

Avoid letting Chart.js pick its default colors — they don't harmonize with the
rest of the page.

When the theme toggle flips light/dark, existing charts won't refresh their
colors automatically (Chart.js caches them). If you need live theme switching
on charts, listen for the toggle and call `chart.update()` after re-reading
the CSS variables. For most reports this is overkill; readers either look in
light or dark, not both within one session.

Mermaid is initialized once with theme variables that approximate the design
system. Note that **Mermaid (v11) does not yet parse OKLCH** — its color helper
throws `Unsupported color format`. So we pass hex equivalents:

```js
const isDark = document.documentElement.classList.contains('is-dark');
mermaid.initialize({
  startOnLoad: true,
  theme: 'base',
  themeVariables: isDark ? {
    primaryColor: '#262626', primaryTextColor: '#f5f5f5',
    primaryBorderColor: '#4d4d4d', lineColor: '#a3a3a3',
    fontFamily: getComputedStyle(document.documentElement).getPropertyValue('--font-sans'),
  } : {
    primaryColor: '#f5f5f5', primaryTextColor: '#1a1a1a',
    primaryBorderColor: '#cccccc', lineColor: '#666666',
    fontFamily: getComputedStyle(document.documentElement).getPropertyValue('--font-sans'),
  },
});
```

If the OKLCH-based tokens drift far from these hex values, resample the
neutrals (the rest of the page uses OKLCH so they don't need updating). Watch
the console — `Unsupported color format: "oklch(...)"` from Mermaid is the
telltale sign.

Same caveat — re-rendering Mermaid on theme flip is possible but rarely worth
the JS. Document this in the report intro if the audience is likely to flip.

## Adding a sixth behavior

If you need another interactive piece (live filter that drives a chart, sticky
header on long tables, copy-button on code blocks), put it in the same
`<script>` block as a self-contained IIFE so the existing five keep working:

```js
(function () {
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.querySelector(btn.dataset.copy);
      if (target) navigator.clipboard.writeText(target.textContent);
    });
  });
})();
```

Avoid pulling in a framework just to add interactivity. Vanilla JS is fine at
this scale and keeps the file genuinely self-contained.

## What NOT to wire up

- **Live data refresh.** Reports are snapshots. If the user wants live data,
  they need a real dashboard, not an HTML file.
- **Auth-gated content.** Don't hide sections behind a login. If something is
  sensitive, omit it from the file entirely.
- **Server calls.** No `fetch()` to an API. The file should open from `file://`
  without errors.
- **Heavy state.** No router, no global store. If your report needs that, it
  has outgrown this skill — make a real app.
