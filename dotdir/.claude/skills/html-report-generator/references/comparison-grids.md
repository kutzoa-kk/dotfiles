# Comparison Grids

Use when the user wants to **see N distinct options side by side** in one
artifact. The whole point is to make it easy to compare — same screen, same
visual treatment, the differences in stark relief.

Typical triggers:

- "Show me 6 different onboarding screen approaches."
- "Generate 4 versions of this card, varying density and tone."
- "I want to compare 3 layout strategies for this dashboard."
- "Lay out 5 color palette options next to each other."

## Skeleton

```html
<header>
  <h1>Onboarding screen — 6 approaches</h1>
  <p class="lead">Same content, different layouts and tones. Each panel
  notes the tradeoff it's making.</p>
</header>

<div class="compare-grid">
  <article class="compare-item">
    <header>
      <h2>A. Single CTA, hero-led</h2>
      <p class="caption">Tradeoff: high focus, low density. Best when the
      primary action is obvious.</p>
    </header>
    <div class="compare-item__preview"><!-- mockup of option A --></div>
  </article>

  <article class="compare-item">
    <header>
      <h2>B. Two-column with sample</h2>
      <p class="caption">Tradeoff: shows value early, splits attention.</p>
    </header>
    <div class="compare-item__preview"><!-- mockup of option B --></div>
  </article>

  <!-- ...C, D, E, F -->
</div>

<style>
  .compare-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 1.5rem;
  }
  .compare-item {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    overflow: hidden;
    display: flex; flex-direction: column;
  }
  .compare-item > header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--color-border);
  }
  .compare-item h2 { font-size: 1rem; margin: 0 0 0.25rem; }
  .compare-item__preview {
    flex: 1;
    min-height: 280px;
    padding: 1.5rem;
    background: var(--color-surface-2);
  }
</style>
```

## Label every panel with the tradeoff

The single most useful thing you can add is **a one-sentence "tradeoff"
caption under each panel title**. The point of N options is not "here are
N things, pick one" — it's "here are N points in a design space, each
optimizing for something different." Name what each one optimizes for.

```html
<p class="caption">Tradeoff: emphasizes hierarchy at the cost of density.</p>
```

Without this, comparison grids degrade into "same thing six times in
slightly different fonts."

## Grid sizing

| N | Default columns | Why |
|---|-----------------|-----|
| 2 | 2 | side-by-side comparison |
| 3 | 3 (or 1×3 stacked on mobile) | enough to see triangles of tradeoff |
| 4 | 2×2 | two axes worth comparing |
| 6 | 3×2 | most useful for design exploration |
| 8+ | auto-fit, minmax(320px, 1fr) | density mode |

Use `repeat(auto-fit, minmax(380px, 1fr))` so the grid degrades smoothly
across viewports without manual breakpoints.

## Two flavors

### A. Mockup grid

Each panel is a **rendered visual** — HTML/CSS that shows what the option
would actually look like. Use for UI design, layout, and visual decisions.
Keep each mockup focused on what's different; don't fill it with realistic
placeholder content that distracts.

### B. Spec grid

Each panel is a **summary card** — heading, tradeoff, key properties as a
small definition list, maybe a tiny diagram. Use when comparing technical
approaches, data sources, or architectures where a "mockup" would just be
boxes and arrows.

```html
<article class="compare-item">
  <header>
    <h2>Option A: Synchronous REST</h2>
    <p class="caption">Tradeoff: simple to debug, blocks on slow downstream.</p>
  </header>
  <dl class="compare-spec">
    <dt>Latency</dt><dd>p50 80ms, p99 300ms</dd>
    <dt>Failure mode</dt><dd>Caller sees timeout, retries naively</dd>
    <dt>Complexity</dt><dd>Low</dd>
    <dt>Cost</dt><dd>$0.02/1k req</dd>
  </dl>
</article>

<style>
  .compare-spec {
    display: grid;
    grid-template-columns: 8rem 1fr;
    gap: 0.5rem 1rem;
    padding: 1rem 1.5rem;
    margin: 0;
    font-size: 0.875rem;
  }
  .compare-spec dt { color: var(--color-faint); font-weight: 500; }
  .compare-spec dd { margin: 0; }
</style>
```

## Optional: synchronized comparison

For 2-up or 3-up grids, the user often wants to apply the **same input** to
each option simultaneously. Add a single input above the grid and have all
panels re-render when it changes:

```html
<div class="card">
  <label>
    Sample text:
    <input type="text" id="sample" value="The quick brown fox" style="width:60%;">
  </label>
</div>

<div class="compare-grid">
  <article class="compare-item" data-render="serif">…</article>
  <article class="compare-item" data-render="sans">…</article>
  <article class="compare-item" data-render="mono">…</article>
</div>

<script>
const sample = document.getElementById('sample');
sample.addEventListener('input', () => {
  document.querySelectorAll('[data-render]').forEach(el => {
    el.querySelector('.compare-item__preview').textContent = sample.value;
  });
});
</script>
```

## Closing section: recommendation

End the page with a short recommendation — which option you'd pick and why.
The grid lets the user form their own opinion first, then you say yours.
That order matters: putting the recommendation at the top makes the rest
look like rationalization.

```html
<section class="card" style="margin-top: 3rem;">
  <h2>Recommendation</h2>
  <p>Option <strong>C (Two-column with sample)</strong> for the public landing
  page; <strong>A (Single CTA)</strong> for the post-signup welcome screen.
  Reasoning: …</p>
</section>
```

## Common mistakes

- **Identical-looking panels.** If the only difference is a hex code,
  combine them — a comparison grid needs visible difference per panel.
- **No tradeoff caption.** Six unlabeled boxes is just clutter; the
  caption is what makes the grid useful.
- **Bias by ordering.** Put the recommendation at the bottom, not the top.
  Order panels by sequence in the design space (density: low → high; tone:
  formal → casual) so the gradient is visible.
- **Mockup-by-screenshot.** Don't embed PNGs you screenshot from somewhere
  else — render the actual HTML so it's interactive and zoomable.
- **Too many options.** 6 is the sweet spot for design exploration. 12
  becomes wallpaper.

## Worked example prompts (for users)

These are good user-side prompts that produce comparison grids:

- > "I'm not sure what direction to take the onboarding screen. Generate 6
  > distinctly different approaches — vary layout, tone, and density — and
  > lay them out as a single HTML file in a grid so I can compare them side
  > by side. Label each with the tradeoff it's making."

- > "Show me 4 ways to structure the dashboard sidebar. For each, render
  > the actual sidebar HTML and note what kind of user it's optimized for.
  > End with your recommendation."

- > "Generate 3 versions of the pricing table — minimal / mid-density /
  > high-density — using the same plans and features. I want to see which
  > reads best."
