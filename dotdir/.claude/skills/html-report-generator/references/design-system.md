# Design System

The visual tokens that every artifact in this skill defaults to. They live
in `assets/base.html` as plain CSS custom properties inside a regular
`<style>` block — not inside Tailwind's `@theme` directive, because the
Tailwind v4 browser CDN does not process `@theme` reliably.

Reach for these tokens before inventing colors or font sizes. If a token is
missing, extend this file rather than hardcoding a value into one report.

If the user's project already has a design system (a CSS file, a Tailwind
config, a brand HTML), use that instead. The tokens below are a sensible
default for "no constraints" cases.

## Color (OKLCH)

OKLCH lets us tune hue, chroma, and lightness independently and stay
perceptually consistent.

```css
:root {
  --color-bg:            oklch(99% 0 0);
  --color-surface:       oklch(100% 0 0);
  --color-surface-2:     oklch(97.5% 0 0);
  --color-border:        oklch(92% 0 0);
  --color-border-strong: oklch(85% 0 0);

  --color-ink:   oklch(18% 0 0);   /* body text                  */
  --color-muted: oklch(45% 0 0);   /* secondary text, axis labels */
  --color-faint: oklch(60% 0 0);   /* captions, metadata          */

  --color-accent:   oklch(55% 0.18 255);
  --color-accent-2: oklch(62% 0.14 195);

  --color-success: oklch(58% 0.15 145);
  --color-warning: oklch(72% 0.16 75);
  --color-danger:  oklch(58% 0.20 25);
  --color-info:    oklch(60% 0.13 245);

  --color-series-1: oklch(55% 0.18 255);
  --color-series-2: oklch(62% 0.14 195);
  --color-series-3: oklch(70% 0.17 75);
  --color-series-4: oklch(58% 0.20 25);
  --color-series-5: oklch(50% 0.17 295);
  --color-series-6: oklch(65% 0.13 145);
}
```

### Dark mode

The base scaffold toggles a `.is-dark` class on `<html>` via JS. Color
tokens get redeclared under that class.

```css
:where(.is-dark) {
  --color-bg:            oklch(14% 0 0);
  --color-surface:       oklch(17% 0 0);
  --color-surface-2:     oklch(20% 0 0);
  --color-border:        oklch(28% 0 0);
  --color-border-strong: oklch(38% 0 0);
  --color-ink:           oklch(96% 0 0);
  --color-muted:         oklch(72% 0 0);
  --color-faint:         oklch(55% 0 0);
  --color-accent:        oklch(72% 0.16 255);
  --color-accent-2:      oklch(75% 0.13 195);
}
```

If the report doesn't need dark mode, delete the toggle button, the JS that
manages it, the redeclaration block, and the `is-dark` references. Less code
beats dead code.

### OKLCH support note

Mermaid (v11) does NOT accept OKLCH in `themeVariables`. The base scaffold
passes hex equivalents for Mermaid only. For everything else (CSS, Chart.js
via `getPropertyValue`, Plotly's color scales) OKLCH is fine.

## Typography

```css
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text",
               "Hiragino Sans", "Noto Sans JP", "Segoe UI",
               Helvetica, Arial, sans-serif;
  --font-mono: "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
}
```

Sizing scale (set on `:root` via the base styles, with `h1` using a fluid
clamp):

| Use | Size |
|-----|------|
| Display heading (`h1`) | `clamp(2rem, 1.5rem + 1.6vw, 2.75rem)` |
| Section heading (`h2`) | 1.625rem |
| Subsection (`h3`) | 1.25rem |
| Lead paragraph (`.lead`) | 1.125rem |
| Body | 1rem |
| Caption (`.caption`) | 0.8125rem |
| Eyebrow (`.eyebrow`) | 0.75rem (uppercase, tracked) |

- Headlines: `letter-spacing: -0.02em; line-height: 1.2`.
- Body: `line-height: 1.65` — generous, especially helpful for mixed JA / EN.
- Long-form columns: cap with `max-width: 880px` (already on `main`).

## Spacing

A modular scale based on 4 px. Use named numbers in your head, not arbitrary
values.

| Token | Value |
|-------|-------|
| `space-1` | 0.25rem (4) |
| `space-2` | 0.5rem (8) |
| `space-3` | 0.75rem (12) |
| `space-4` | 1rem (16) |
| `space-5` | 1.5rem (24) |
| `space-6` | 2rem (32) |
| `space-7` | 3rem (48) |
| `space-8` | 4rem (64) |
| section gap | `clamp(3rem, 4rem + 2vw, 6rem)` (between `h2` sections) |

Inside a section, use 1rem / 1.5rem / 2rem rhythm. Avoid uniform padding
everywhere — that's how reports start to look like default templates.

## Radii, borders, shadows

| Token | Value |
|-------|-------|
| small radius | 4px (form inputs, code chips) |
| card radius | 8px (KPI, chart-card, accordion) |
| pill | 999px (badges) |

- Borders are always 1 px hairlines via `border: 1px solid var(--color-border)`.
  Depth comes from layering surfaces (`--color-bg` < `--color-surface` <
  `--color-surface-2`), not thick borders.
- Shadows are barely there. The theme-toggle pill uses a faint `box-shadow`;
  everything else skips shadows.

## Motion

```css
--duration-fast:   120ms;
--duration-normal: 220ms;
--duration-slow:   400ms;
--ease-out:        cubic-bezier(0.2, 0.7, 0.2, 1);
```

The base scaffold respects `prefers-reduced-motion` automatically. Always
animate `transform`, `opacity`, `color`, `background-color`. Avoid animating
`width`, `height`, `top`, `left`, `padding`, `margin` — they trigger layout.

## Iconography

No icon library by default. Inline SVG sized `w/h: 1em` with
`fill="currentColor"` or `stroke="currentColor"` (see
[svg-and-diagrams.md](svg-and-diagrams.md)). For status pips, the
`.pip.pip--success / --warning / --danger / --info` classes are pre-defined.

## Print

The base scaffold's `@media print` block:
- whites out backgrounds,
- hides the TOC and theme toggle,
- removes link underlines,
- prevents sections, cards, and tables from breaking across pages,
- sets body font to 11pt.

A4 and US Letter both work because the main column is bounded by
`max-width: 880px`, not viewport units.

## Accessibility floor

- WCAG AA contrast against `--color-bg` (the OKLCH values above do — keep
  the `--color-ink` / `--color-bg` pairing if you change colors).
- `:focus-visible` outline is `2px solid var(--color-accent)` with 2 px offset.
- Every `<canvas>` chart gets an `aria-label` describing the chart, plus a
  `<details>` containing the data as a `<table>` (screen-reader fallback).
- TOC anchors use `:target` styling so deep links land on a clearly
  highlighted section.

## "Modern minimal" — what it actually means

Not "strip everything until generic." It means:

- High information density without crowding — generous leading and section gaps.
- Hierarchy is obvious at a glance: display > h2 > h3 > body > caption are
  clearly different sizes.
- Color is reserved. Most of the page is neutrals; accents and status colors
  do real work.
- Borders are 1 px hairlines. Shadows barely visible.
- Gradients only when purposeful (chart fills, occasional emphasis).
- Layering provides depth: `--color-bg` behind `--color-surface` behind cards.
- One font family. Mono only inside `<code>`.

Sanity-check against well-designed product release notes (Linear changelog,
Stripe post-mortems). If the report doesn't look at home next to those, dial
back the chrome.

## Project-specific overrides

If the project being reported on already has a design system, prefer it over
this one. Concretely:

1. Look for `tokens.css`, `theme.css`, `tailwind.config.{js,ts}`, a Figma
   spec, or a brand HTML in the repo.
2. Port those colors and fonts into the report's `<style>` block instead of
   the defaults here.
3. Keep the structural classes (`.kpi`, `.card`, `.chart-card`, etc.) — they
   only depend on the CSS variables, so swapping the variable values is
   enough to retheme.

A report that looks like it belongs to the project beats one that looks like
a clean default.

## Adding new tokens

Resist. The current palette covers 95% of cases. Before adding a token:

1. Is there an existing token that's close enough?
2. Is this needed in more than one report? If only one, use an arbitrary
   value inline (`color: oklch(60% 0.10 180)`) instead.
3. If genuinely reusable, add to this file and document its intended use
   ("axis label color", "danger highlight background"). Tokens without intent
   accumulate and the palette decays.
