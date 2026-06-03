# A Web of Linked HTML Files

Most of this skill assumes one self-contained `.html` file. That's the right default. But for
work that unfolds over a session or more — exploring a design space, speccing a system,
planning a build, curating research — the better unit is often *several* linked HTML files
instead of one giant document, or (worse) a single Markdown plan.

This is the shift described in *Using Claude Code: The Unreasonable Effectiveness of HTML*:
moving away from "a single Markdown plan" toward "a web of HTML files" — separate documents for
exploration, mockups, implementation plans, and design systems, cross-referenced and reopened
across sessions.

## When a web beats a single file

Reach for multiple linked files when:

- **The work has distinct phases or facets** that each deserve room — *explore options*,
  *mock the UI*, *write the plan*, *define the design system*. Cramming all four into one
  scroll buries each.
- **It will live across sessions.** A folder of HTML files is durable, visual working memory.
  In a later session Claude can `Read` `plan.html` to recover exactly what was decided, and you
  can reopen `exploration.html` to remember *why*.
- **Different readers want different docs.** A reviewer opens `pr.html`; a PM opens `plan.html`;
  you keep `exploration.html` for yourself.
- **One artifact references another.** The plan points at "approach 3" — which lives, fully
  rendered, in the exploration doc.

Stay with a single file when the thing fits comfortably in one scrollable page (a report, a
one-off explainer, a quick scratchpad). Over-splitting a small artifact just adds navigation
friction. The unit of work decides — not a rule.

## Structure: a hub plus spokes

Put everything in one folder named after the work, with an `index.html` hub that links out:

```text
notification-system/
├── index.html            # hub: what this is, status, links to each doc
├── exploration.html      # N approaches compared side by side
├── mockup.html           # interactive UI mockup
├── plan.html             # phased implementation plan
├── design-system.html    # tokens + components (the shared visual language)
└── shared.css            # one stylesheet every page links
```

The hub is a table of contents you can actually see — a short paragraph of context plus a card
per document with a one-line description and current status. It's the page you (and Claude) open
first in any later session.

## Make the files feel like one product

Multiple files must not look like multiple authors. Two things hold them together.

**1. One shared stylesheet.** This is the case where leaving the single-file rule behind pays
off (see SKILL.md). Put the design tokens and base component styles in `shared.css` and link it
from every page:

```html
<link rel="stylesheet" href="shared.css">
```

Pull the tokens from `references/design-system.md` so the palette, type scale, and surfaces
match the rest of your output. One source of truth means restyling every page is a one-file
edit.

**2. A consistent top nav, repeated on every page.** Plain HTML has no includes, so copy the
same nav markup into each file's header and mark the current page:

```html
<nav class="doc-nav" aria-label="Document navigation">
  <a href="index.html">Overview</a>
  <a href="exploration.html">Approaches</a>
  <a href="mockup.html">Mockup</a>
  <a href="plan.html" aria-current="page">Plan</a>
  <a href="design-system.html">Design system</a>
</nav>
```

`aria-current="page"` both helps screen readers and gives you a hook to style the active link.
If the nav grows or changes often, a tiny shared `nav.js` that builds the same markup from a
list keeps the files in sync — but for a handful of pages, copy-paste is simpler and has no
load-order gotchas.

## Linking conventions

- **Relative paths only.** `href="plan.html"`, never an absolute filesystem path. The folder
  must work when zipped, moved, or served from S3 / GitHub Pages.
- **Deep-link across docs.** Give sections stable `id`s and link straight to them:
  `<a href="exploration.html#approach-3">the chosen approach</a>`. This is the payoff of the web
  — the plan can point at the exact option it builds on.
- **Link back to the hub** from every page so navigation is never a dead end.

## A worked shape: planning a feature build

A common, high-value web — the artifacts Claude produces while helping you decide *what* to
build, before writing product code:

| File | Holds | Borrow from |
|------|-------|-------------|
| `index.html` | One-paragraph framing, status, links | — |
| `exploration.html` | 3–6 approaches in a grid, trade-offs, a recommendation | `references/comparison-grids.md` |
| `mockup.html` | Clickable UI mock, states, maybe a slider to tune it | `references/interactive-playgrounds.md` |
| `plan.html` | Phases, file-by-file changes, risks, open questions | `references/recipes/system-development.md` |
| `design-system.html` | Tokens, components, do/don't | `references/design-system.md` |

Generate the spokes the task needs — not all five by reflex. A pure planning request may only
want `exploration.html` + `plan.html`. Let the work decide which spokes exist.

## Persisting and resuming

Because the folder is durable context, treat it that way:

- **Name files for their role**, not the date (`plan.html`, not `doc-2026-06-02.html`), so links
  stay stable as the work evolves.
- **Keep `index.html` current.** When a doc's status changes (explored → chosen → built), update
  its card. The hub is the one place that tells you where things stand.
- **Reopen, don't recreate.** In a later session, `Read` the relevant file to recover decisions
  instead of asking the user to re-explain. The web *is* the memory.

## Common mistakes

- **Splitting a one-page artifact.** If it fits in one scroll, keep it one file. The web is for
  work with real facets, not for chopping a report into pieces.
- **Inconsistent styling across pages** — the tell-tale sign of files built ad hoc. Link one
  `shared.css`; don't redefine tokens per page.
- **Broken relative links** because a file was generated in the wrong directory. Verify links
  resolve within the folder before reporting done.
- **A hub that rots.** An `index.html` whose statuses and links no longer match reality is worse
  than none — readers trust it and get misled.
