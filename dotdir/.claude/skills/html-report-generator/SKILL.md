---
name: html-report-generator
description: |
  Reach for this when you're about to write something a human will actually read — a report,
  a spec, a plan, a PR explainer, a status update, a comparison of N options, a throwaway
  parameter-tuning playground, a research synthesis — and would otherwise default to Markdown.
  HTML carries richer information (real tables, charts, SVG, interaction, color, layout) and
  is what people will actually open and read. Trigger on phrases like "make a report", "HTML
  artifact", "HTML file", "ダッシュボード", "可視化したい", "this would be nice as HTML", "I want
  to share this", "compare these options side by side", "let me tweak this", "review this PR",
  "explain this code", or whenever a deliverable would benefit from being interactive,
  visually structured, or shareable as a single URL. Skip for raw data dumps, README files,
  plain text logs, machine-parsed output, or one-line answers.
---

# HTML Report Generator

This skill is a **set of recipes and quality bars** for making interactive HTML artifacts. It
is not a mandatory template — `make a HTML file` to Claude is often enough. What this skill
adds: a coherent visual system, a tested base scaffold, and patterns for the use cases where
people most often get stuck (long reports, comparison grids, code reviews, editing UIs).

**Why HTML, and why mid-task — not just at the end:** HTML carries information Markdown can't
(real tables, SVG diagrams, syntax-highlit code, color-coded status, interactive controls,
spatial layout), and it stays readable at 100+ lines where Markdown of the same length collapses
into a wall of text. It's also a medium for staying *in the loop* with Claude *during* the work —
a spec you click through, six approaches in a grid, a PR with inline annotations, a plan with a
mockup beside it. These keep you engaged with what Claude is doing instead of rubber-stamping
prose. So reach for it while exploring, planning, and reviewing — not only when someone asks for
"the final report."

> "I'm a little bit afraid that people will read this article and turn it into a /html
> skill or something. While there might be some value in that, I want to emphasize that
> you don't need to do much to get Claude to do this."
> — Thariq, Claude Code team, *Using Claude Code: The Unreasonable Effectiveness of HTML*

Take this seriously. If the task is "make a quick HTML scratchpad", just do it. Reach for
the references and base scaffold when you need consistency across multiple artifacts, a
polished deliverable, or a pattern you haven't built before.

## When this skill helps most

| Situation | Where to look |
|-----------|---------------|
| Long-form report, spec, plan, or research synthesis | `references/long-form-reports.md` (canonical structures) |
| Side-by-side comparison of N options or variants | `references/comparison-grids.md` |
| PR review, code explainer, diff with annotations | `references/code-review.md` |
| Interactive parameter / prompt / animation tuner | `references/interactive-playgrounds.md` |
| Throwaway editor with "export when done" | `references/editing-interfaces.md` |
| Architecture / flow / data diagram | `references/svg-and-diagrams.md` |
| Raster cover, hero banner, eyecatch, or conceptual illustration | the **`codex-image-gen`** skill (generates via Codex CLI, no API key) |
| Visual system, color, typography, spacing | `references/design-system.md` |
| TOC, tabs, sortable tables, theme toggle JS | `references/interactivity.md` |
| Planning/spec work spanning exploration, mockups, and a plan, kept across sessions | `references/linked-artifacts.md` (a web of linked HTML files) |

The four canonical long-form report shapes (data-analysis, system-development,
status-progress, audit-review) live under `references/recipes/` and act as templates you
can borrow from when they fit. Don't force a request into one of them if it doesn't.

## Workflow

1. **Decide whether you actually need this skill.** A quick scratchpad, a single-chart
   answer, a one-page explainer — just write the HTML. Use the skill when:
   - The artifact will be shared, referenced, or read by multiple people.
   - It needs consistent design quality.
   - It uses an unfamiliar pattern (drag-drop editor, comparison grid, etc.).

2. **Gather real context from your tools before writing.** HTML's edge in Claude Code is that
   the model has the context to *fill* it — so fill it with real data, not lorem ipsum. Pull
   `git log` / `git diff` for a status report or PR explainer; read the actual changed files
   for a code review; query MCP servers (Linear / Jira / Slack / GitHub) for the real tickets,
   threads, and issues; load the real dataset for an analysis. A report wired to real numbers,
   commit hashes, and ticket IDs is worth ten templated ones. If the data genuinely isn't
   reachable, say so and stub it explicitly — never fabricate plausible-looking values.

3. **Pick a starting point.**
   - For long-form reports: copy `assets/base.html`. It already has TOC scroll-spy, KPI
     cards, charts, sortable tables, tabs, accordion, timeline, Mermaid, and a light/dark
     toggle wired up. Delete what you don't need.
   - For an interactive playground / editor / comparison grid: read the relevant reference
     and the matching snippets in `assets/components/`. The base scaffold is often
     overkill for these.
   - For a single explainer with a diagram: just write the HTML, pulling the design
     tokens from `references/design-system.md`.

4. **Match the project's existing visual language if there is one.**
   The default palette in `assets/base.html` is a deliberate modern-minimal direction, but
   if the project already has a design system (a CSS file, a Tailwind config, a Figma
   spec, a brand HTML), use that instead. Ask the user where to find it before inventing
   colors. The skill's tokens are a starting point, not a brand.

5. **Output.** Write the final HTML to the path the user asked for, or `report.html` in
   the current directory if unspecified. For multi-file artifacts (HTML + external SVG /
   image), put them in a folder named after the report.

6. **Verify it works.** Open the file or grep it: the sections you put in the TOC exist
   in the body, the `<canvas>` elements are wired to chart init code, no broken `<script>`
   tags. Don't claim success without confirming.

## What "single self-contained file" means (and when to break it)

Default: one `.html` file with all custom CSS in one `<style>` block, all custom JS in one
`<script>` block at the end of `<body>`, and vendor libraries (Chart.js, Plotly, Mermaid,
Tailwind v4 browser) via CDN.

**Break the single-file rule when:**
- The user wants a polished SVG illustration — author it as a separate `.svg` and
  reference it; don't base64-embed unless the user asks.
- The report wants a raster cover, hero banner, or conceptual illustration (texture or
  photographic feel, not line art) — generate it with the **`codex-image-gen`** skill and
  reference it as an external file. Keep text out of the image and overlay real HTML type on top.
- The artifact embeds many large screenshots — link to them, don't inline base64.
- The user wants to share via S3 / GitHub Pages — multi-file is fine as long as relative
  paths work.

**Tailwind CSS v4 note (verified empirically):** the browser build at
`@tailwindcss/browser@4` scans utility classes from the markup, but **does NOT process
inline `@theme` / `@layer` / `@apply` directives**. So `assets/base.html` uses a hybrid:
Tailwind utility classes for layout where convenient, plain CSS variables (in a normal
`<style>` block) for theme tokens, and hand-written component classes. Don't rely on
`<style type="text/tailwindcss">` in browser-CDN reports — it gets silently dropped.

## A web of HTML files — when one file isn't the unit

For a quick artifact, one file is right. But for work that unfolds over a session or more —
exploring a design space, speccing a system, planning a build — the better unit is often
*several* linked HTML files: an `index.html` hub that links out to `exploration.html`,
`mockup.html`, `plan.html`, `design-system.html`. Each stays focused and readable, and you (and
Claude, in later sessions) can reopen and cross-reference them instead of scrolling one giant
document. This is the shift the source article calls moving from "a single Markdown plan" to "a
web of HTML files." See `references/linked-artifacts.md` for the folder structure, the shared
stylesheet + nav that keep the pages feeling like one product, linking conventions, and when it
pays off versus a single file.

## Design quality bars

Every artifact should demonstrate at least four of:

1. Clear hierarchy through scale contrast (display, h2, body, caption are obviously different).
2. Intentional rhythm in spacing — not uniform padding everywhere.
3. Depth through surface layering — `bg` < `surface` < `surface-2`.
4. Typography with deliberate leading and tracking. System stack is fine.
5. Color used semantically — accent for emphasis, status colors for status, neutrals carry
   most of the page.
6. Designed hover, focus, and active states. Keyboard users see focus rings.
7. Data viz that uses the design-system palette and font, not whatever the chart library
   gives by default.
8. Motion that clarifies (TOC highlight, tab transition) — never bouncing decoration.

**Banned:** centered hero with decorative gradient blob, three identical cards in a row
with no hierarchy, "click here" buttons, generic footer with social icons, default Chart.js
or Bootstrap aesthetics.

## Two-way interaction — the part most reports miss

HTML's biggest advantage over Markdown is that **the reader can act on the artifact and
hand the result back**. When the use case allows, add:

- Sliders, knobs, color pickers, drag-drop cards — the user adjusts something.
- A **"Copy as prompt / JSON / Markdown" button** — the result of their adjustment turns
  back into text they paste into Claude.

See `references/interactive-playgrounds.md` and `references/editing-interfaces.md` for
patterns. Even a "static" report often benefits from a copy button on key values.

## Common mistakes

- **Dumping the entire dataset into a 5000-row HTML table.** Paginate, virtualize, or
  link to the raw CSV.
- **Default Chart.js / Mermaid colors.** Read the tokens from CSS and pass them in. The
  base scaffold already does this.
- **Adding a dark mode toggle by reflex.** Only when the artifact is meant to be viewed
  in low-light conditions (ops dashboard) or contains a lot of bright color.
- **`<div class="container"><div class="row"><div class="col">` Bootstrap noise.** Use
  CSS Grid / flex directly with semantic elements.
- **Forgetting `lang="ja"` on `<html>`** for Japanese reports. The font stack falls back
  poorly without it.
- **Silently omitting an empty section.** Say "該当データなし" explicitly. Readers wonder
  if you forgot.

## Verifying

Before reporting completion:

1. The file is `.html` and the size is sensible (status report ~30–80 KB, chart-heavy
   analysis ~80–250 KB).
2. Grep the file for the section anchors you put in the TOC and confirm they exist in
   the body.
3. If interactivity matters, spot-check that `<canvas>` / `<table>` markup is actually
   wired to the JS init code at the bottom of the file.
4. Print preview test if the user is going to PDF it: confirm `@media print` styles
   don't break (sidebar hidden, content reflows).

## Optional scaffolder

`scripts/scaffold.py` generates a starter HTML from a YAML / JSON spec describing report
type, title, and section list. Useful for repetitive structured cases (weekly status
reports drop, audit findings drop). For one-offs, copy `assets/base.html` directly.

```bash
python scripts/scaffold.py --type data-analysis --title "Q2 churn investigation" --out report.html
```
