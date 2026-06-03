# Long-form Reports

When the deliverable is a document a human is meant to read top to bottom —
3+ sections, a table of contents, multiple visualizations — `assets/base.html`
is the starting point. It includes the layout, TOC scroll-spy, KPI cards,
charts, sortable tables, tabs, accordion, timeline, Mermaid block, and a
light/dark toggle, all wired up.

## Pick a recipe (or don't)

The four most common long-form shapes have canonical structures in
`recipes/`. They are starting points — borrow what fits, don't force-fit.

| Shape | When | File |
|-------|------|------|
| Data analysis | EDA, A/B test, ML experiment, investigation | [recipes/data-analysis.md](recipes/data-analysis.md) |
| System development | Architecture overview, design doc, RFC, post-mortem | [recipes/system-development.md](recipes/system-development.md) |
| Status / progress | KPI dashboard, weekly / monthly / quarterly review | [recipes/status-progress.md](recipes/status-progress.md) |
| Audit / review | Security audit, code review, compliance findings | [recipes/audit-review.md](recipes/audit-review.md) |

If your report doesn't fit any of these — say, a research synthesis, a
post-mortem with an analysis component, an in-depth explainer — pick the
closest one and adapt, or just write the sections that make sense for the
content.

## Universal long-form patterns

Across all four, these are the bits that matter:

### Header carries the answer

The first viewport should contain:
- the report's title,
- the one-sentence answer / status / decision,
- the metadata (author, period, status pip).

If the reader stops there, they should still leave knowing the headline.

### TOC works at any length

`assets/base.html` builds the TOC at runtime from `<section data-toc="…">`.
Adding or removing a section auto-updates the sidebar. The scroll-spy
highlights the active section so readers know where they are in a long page.

For documents over ~10 sections, group related sections under a heading in
the TOC (the script as written supports one level; extending to two is a
~10-line change).

### Anchor every section

`<section id="...">` lets readers deep-link. Use stable, descriptive IDs
(`summary`, `findings`, `risks`) — these end up in shared URLs.

### Caption every chart

A chart without a one-sentence caption is decoration. Right below the
`chart-wrap`, write the thing you want the reader to notice. Don't rely on
them squinting at the line.

### Empty states are explicit

If a section has nothing to show, say so:

```html
<div class="card" style="text-align:center;color:var(--color-muted);">
  <p style="margin:0;">該当データなし</p>
</div>
```

Silently omitting a section makes readers wonder if you forgot.

### Print stylesheet works

The base scaffold hides the sidebar, removes link underlines, and sets
font to 11pt under `@media print`. Long-form reports are often exported to
PDF — preview-test before claiming done.

## Skip the scaffold when the report is short

If the deliverable is a 1-screen status, a single comparison, or a 200-word
explainer, the scaffold's TOC and section structure is overhead. Just write
the HTML, pulling tokens from `design-system.md` and a single card pattern
from `assets/components/`.

A 2 KB HTML file is fine. Not every report needs a sidebar.
