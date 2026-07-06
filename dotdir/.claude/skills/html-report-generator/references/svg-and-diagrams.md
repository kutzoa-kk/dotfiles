# SVG & Diagrams

In HTML reports, **SVG is your first-class diagram tool**, not an afterthought.
For most diagrams you'd reach for Excalidraw, Lucidchart, or a screenshot,
inline SVG is:

- searchable (text is text, not pixels),
- diff-able (PR reviews can see what changed),
- styleable (uses the same CSS tokens as the rest of the report),
- accessible (`<title>` becomes a tooltip and screen-reader label),
- responsive (scales without losing quality).

## Picking your diagram tool

| Need | Use |
|------|-----|
| Flowchart, sequence, ERD, state, gantt | **Mermaid** (in `<pre class="mermaid">`) |
| Custom illustration — system block diagram, data flow with shape variety | **Inline SVG**, hand-written |
| Architecture with many similar components | Mermaid |
| Something that needs to match brand visual identity | Inline SVG with the design tokens |
| Already exists as a polished diagram (figma export, draw.io) | **External `.svg`** referenced via `<img src="…">` |
| One-off chart that doesn't fit Chart.js's categories | Inline SVG drawn from data |

Mermaid wins for technical diagrams because the text source is the diagram —
no editor lock-in, no binary artifact. Hand-rolled SVG wins when you need
visual control Mermaid can't give (custom shapes, annotations, layered
groups).

## Inline SVG basics

Use the same design tokens by passing them via CSS variables on the wrapping
`.architecture` block, or by using `currentColor` and inheriting from the
parent text color.

```html
<figure class="architecture" aria-labelledby="fig1">
  <figcaption id="fig1" class="caption">Request lifecycle</figcaption>
  <svg viewBox="0 0 600 200" role="img" aria-label="Request lifecycle">
    <title>Request lifecycle</title>

    <!-- Use design tokens via CSS variables. -->
    <style>
      .node-bg     { fill: var(--color-surface-2); stroke: var(--color-border-strong); stroke-width: 1; }
      .node-text   { fill: var(--color-ink); font-family: var(--font-sans); font-size: 13px; }
      .edge        { stroke: var(--color-muted); stroke-width: 1.5; fill: none; marker-end: url(#arrow); }
      .edge-label  { fill: var(--color-faint); font-family: var(--font-sans); font-size: 11px; }
      .accent      { fill: var(--color-accent); }
    </style>

    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
              markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--color-muted)"/>
      </marker>
    </defs>

    <!-- Nodes -->
    <g>
      <rect class="node-bg" x="20"  y="70" width="100" height="60" rx="6"/>
      <text class="node-text" x="70"  y="105" text-anchor="middle">Client</text>
    </g>
    <g>
      <rect class="node-bg" x="250" y="70" width="100" height="60" rx="6"/>
      <text class="node-text" x="300" y="105" text-anchor="middle">API</text>
    </g>
    <g>
      <rect class="node-bg" x="480" y="70" width="100" height="60" rx="6"/>
      <text class="node-text" x="530" y="105" text-anchor="middle">DB</text>
    </g>

    <!-- Edges -->
    <path class="edge" d="M120 100 L250 100"/>
    <text class="edge-label" x="185" y="92" text-anchor="middle">POST /items</text>

    <path class="edge" d="M350 100 L480 100"/>
    <text class="edge-label" x="415" y="92" text-anchor="middle">INSERT</text>
  </svg>
</figure>
```

`viewBox` controls the coordinate system; the SVG scales to its container's
width by default. Set `width: 100%; max-width: 600px;` on the SVG (or its
parent) for responsive layout.

## Accessibility

Every meaningful SVG needs:

- `role="img"` — tells assistive tech this is an image, not abstract markup.
- `aria-label` or `aria-labelledby` — short description.
- A `<title>` element as the first child — tooltip + screen-reader text.
- Optional `<desc>` for longer descriptions.

For decorative SVG (a divider, a flourish) use `aria-hidden="true"` so
screen readers skip it.

## Annotations

The advantage SVG has over rendered images is that you can layer
annotations directly on top of the diagram, color-coded and labeled.

```html
<svg viewBox="0 0 600 240">
  <!-- diagram -->

  <!-- annotation: highlight a node + callout -->
  <rect x="246" y="66" width="108" height="68" rx="8"
        fill="none" stroke="var(--color-danger)" stroke-width="2"
        stroke-dasharray="4 3"/>
  <text x="300" y="155" text-anchor="middle"
        fill="var(--color-danger)" font-size="11" font-weight="600">
    F-001 bottleneck
  </text>
</svg>
```

In a code review HTML, you can wire each annotation to a finding via
`<a href="#F-001">` around the group.

## Patterns

### Block diagram with grouped components

```html
<svg viewBox="0 0 800 320">
  <!-- group A: client tier -->
  <g aria-label="Client tier">
    <rect x="10" y="10" width="220" height="300" rx="8"
          fill="var(--color-surface-2)" stroke="var(--color-border)"/>
    <text x="20" y="35" font-size="12" font-weight="600"
          fill="var(--color-muted)">Client tier</text>
    <!-- nodes inside group A -->
  </g>
  <!-- group B: server tier -->
  <g aria-label="Server tier">
    <rect x="250" y="10" width="540" height="300" rx="8"
          fill="var(--color-surface)" stroke="var(--color-border)"/>
    <text x="260" y="35" font-size="12" font-weight="600"
          fill="var(--color-muted)">Server tier</text>
    <!-- nodes inside group B -->
  </g>
</svg>
```

### Mini-chart inline with text

Tiny sparkline-style SVG inline next to a number reads better than a chart card
for one-line indicators.

```html
<p>
  CPU usage <strong>62%</strong>
  <svg width="80" height="20" viewBox="0 0 80 20" aria-label="CPU sparkline">
    <polyline points="0,15 10,12 20,10 30,8 40,6 50,9 60,5 70,4 80,6"
              fill="none" stroke="var(--color-series-1)" stroke-width="1.5"/>
  </svg>
  trending down
</p>
```

### Timeline / process strip

```html
<svg viewBox="0 0 800 80" role="img" aria-label="Deployment phases">
  <line x1="40" y1="40" x2="760" y2="40"
        stroke="var(--color-border)" stroke-width="2"/>
  <g font-family="var(--font-sans)" font-size="11"
     fill="var(--color-ink)" text-anchor="middle">
    <circle cx="80"  cy="40" r="8" fill="var(--color-success)"/>
    <text   x="80"  y="66">Plan</text>
    <circle cx="280" cy="40" r="8" fill="var(--color-success)"/>
    <text   x="280" y="66">Build</text>
    <circle cx="480" cy="40" r="8" fill="var(--color-warning)"/>
    <text   x="480" y="66">Test</text>
    <circle cx="680" cy="40" r="8" fill="var(--color-faint)"/>
    <text   x="680" y="66">Deploy</text>
  </g>
</svg>
```

## Click-to-zoom lightbox for large diagrams

A wide `flowchart LR` with several subgraphs renders fine in Mermaid but gets
scaled down to fit the ~880px content column — at which point 13px node labels
become unreadable. Don't shrink the diagram or split it reflexively; give the
reader a zoom affordance. `assets/base.html` ships this wired up:

- Clicking any `svg` inside `.architecture` opens a fullscreen lightbox.
- Wheel zooms around the cursor, drag pans, `Esc` / backdrop click closes,
  and +/−/fit buttons cover keyboard-free use.
- `cursor: zoom-in` on the diagram plus a caption note ("図はクリックで拡大")
  make the affordance discoverable — an invisible zoom is a missing zoom.

Implementation notes (the full snippet lives in `assets/base.html`; copy the
`.diagram-lightbox` CSS block and the "Diagram zoom lightbox" script block):

- **Clone the rendered SVG** into the lightbox at its `viewBox` natural size.
  Mermaid sets an inline `max-width` on its output — undo it on the clone
  (`clone.style.maxWidth = 'none'`), never on the original.
- **Fit-to-viewport initial scale**: `min((vw−64)/w, (vh−96)/h)` centers the
  whole diagram first; the reader zooms in from there.
- **Zoom around the cursor** with `transform-origin: 0 0` and the fixed-point
  update `t' = c − (c − t)·(s'/s)` — zooming toward the corner instead of the
  cursor is the most common way to get this wrong.
- The wheel listener must be **non-passive** (`{ passive: false }`) or
  `preventDefault()` silently fails and the page scrolls behind the overlay.
- Use **pointer capture** for panning so fast drags don't drop, and treat a
  motionless pointerup on the backdrop as "close".
- Dialog a11y: `role="dialog"` + `aria-modal`, focus the close button on
  open, restore focus to the opener on close, lock body scroll while open.

The same pattern applies to hand-written inline SVG — the delegation targets
`.architecture svg`, not Mermaid specifically.

## External SVG vs inline

| Inline | External `<img src=".svg">` |
|--------|-----------------------------|
| Animates with CSS / JS | Static |
| Inherits page styles via `currentColor` and `var(--…)` | Independent styling |
| Searchable / diff-able | Opaque to git diff |
| Adds to HTML size | Caches separately |

Default to inline for diagrams under ~50 nodes. Use external for large
hand-authored illustrations (where inline would pollute the HTML) or for
brand assets that have their own design system.

## Common mistakes

- **PNG screenshots of diagrams that could be SVG.** You lose searchability,
  scalability, theme-matching, and diff-ability. If the source is Mermaid /
  Excalidraw / draw.io, export as SVG.
- **No `<title>` element.** Diagrams without titles are invisible to screen
  readers and have no tooltip.
- **Hard-coded colors.** Use `currentColor` or `var(--color-…)` so the
  diagram adapts to light / dark mode and brand changes.
- **Over-precise coordinates.** Round to whole pixels. Sub-pixel coordinates
  cause blurry rendering in some browsers.
- **Tiny font sizes.** 9 px in SVG is barely legible. Don't go below 11 px.
- **No padding inside `viewBox`.** Leave ~10–20 units of breathing room on
  every side so content doesn't crowd the edges.

## Mermaid quick reference

Already covered by base.html's init. Most useful diagram types:

```text
flowchart LR        — left-to-right boxes-and-arrows
sequenceDiagram     — actor lifelines, message arrows
erDiagram           — entities and relationships
stateDiagram-v2     — state machines (lifecycle, status)
gantt               — task schedules (only when dates matter)
classDiagram        — class hierarchies (rarely useful in reports)
```

Stick to one diagram type per concept. If a single diagram needs to be
both a flowchart and a sequence diagram, split it into two.

Mermaid does NOT support OKLCH in `themeVariables` (as of v11) — use hex
equivalents. The base scaffold does this already.
