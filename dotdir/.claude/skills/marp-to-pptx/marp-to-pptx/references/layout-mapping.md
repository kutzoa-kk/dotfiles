# Rector Layout -> PPTX Mapping Reference

Marp Rector の HTML/CSS パターンから PPTX 要素への対応表。
convert.js が自動検出できない複雑なレイアウトを手動で変換する際の参照用。

## Color Palette

| Rector Class | Hex (no #) | PPTX Usage |
|---|---|---|
| `text-navy` / `bg-navy` | `1B4565` | Headers, emphasis, CTA |
| `text-teal` / `bg-teal` | `3E9BA4` | Accents, icons, borders |
| `bg-bg-secondary` | `F5F5F5` | Card backgrounds |
| `text-text-secondary` | `4A4A4A` | Body text |
| `text-text-muted` | `6B6B6B` | Captions |

## Typography Scale

| Rector Class | PPTX fontSize (pt) | Usage |
|---|---|---|
| `text-em-3xl` | 48 | Hero titles, statistics |
| `text-em-2xl` | 32 | Slide titles |
| `text-em-xl` | 24 | Subtitles, section headers |
| `text-em-lg` | 20 | Body text |
| `text-em-base` | 16 | Captions, labels |

## Layout Detection Rules

| Layout | Detection Pattern | HTML Clue |
|---|---|---|
| hero-title | Centered + `text-em-3xl` | `flex items-center justify-center` + `h1.text-em-3xl` |
| title-bg | Navy overlay | `bg-navy opacity-60` |
| split-title | 2-col with navy | `grid-cols-2` + `bg-navy` first cell |
| section-break | Teal left border | `border-l-4 border-teal` |
| chapter-title | Bottom-aligned number | `justify-end` + `text-em-3xl.text-teal` |
| text-only | Centered text block | `max-w-3xl mx-auto` |
| bullet-list | Teal bullet markers | Bullet spans in `flex items-start` |
| quote | Blockquote | `<blockquote>` |
| big-number | Large teal number | `text-em-3xl text-teal font-bold` (no grid) |
| two-column | 2-column grid | `grid-cols-2` |
| three-column | 3-column grid | `grid-cols-3` |
| feature-cards | 3-col with cards | `grid-cols-3` + `rounded-lg bg-bg-secondary` |
| grid-2x2 | 2x2 grid | `grid-cols-2 grid-rows-2` |
| closing | Thank you | Comment includes "thank" / "closing" |

## PPTX Element Positions (inches, 16:9 = 10 x 5.625)

### Hero Title / Closing
```
Title:    x=0.5  y=1.69  w=9.0  h=1.2  (centered)
Subtitle: x=0.5  y=3.09  w=9.0  h=0.8  (centered)
```

### Section Break
```
Teal bar: x=0.5  y=1.69  w=0.06 h=1.5
Label:    x=0.9  y=1.69  w=6.0  h=0.5
Title:    x=0.9  y=2.29  w=6.0  h=0.8
```

### Two Column
```
Left title:  x=0.5   y=0.5   w=4.25  h=0.8
Left body:   x=0.5   y=1.5   w=4.25  h=3.625
Right card:  x=5.25  y=0.5   w=4.25  h=4.625  (bg: F5F5F5)
Right text:  x=5.55  y=0.8   w=3.65  h=...
```

### Three Column / Feature Cards
```
Card width:  (10 - 1.0 - 0.8) / 3 = 2.73 each
Card gap:    0.4
Card Y:      1.7 (below title)
Card height: 5.625 - 1.7 - 0.5 = 3.425
```

### 2x2 Grid
```
Cell width:  (10 - 1.0 - 0.4) / 2 = 4.3
Cell height: (5.625 - 1.5 - 0.5 - 0.4) / 2 = 1.6125
Cell gap:    0.4
```

## Manual Conversion Tips

### Image Handling
```javascript
// Local file
slide.addImage({ path: "image.png", x: 5.25, y: 0.5, w: 4.25, h: 4.0,
  sizing: { type: "contain", w: 4.25, h: 4.0 } });

// From URL
slide.addImage({ path: "https://example.com/img.jpg", x: 1, y: 1, w: 5, h: 3 });
```

### Comparison Layout (Before/After)
```javascript
// Left: Before
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.25, h: 3.8, fill: { color: "FEF2F2" }, rectRadius: 0.1,
});
// Right: After
slide.addShape(pres.shapes.RECTANGLE, {
  x: 5.25, y: 1.2, w: 4.25, h: 3.8, fill: { color: "F0FDF4" }, rectRadius: 0.1,
});
```

### Timeline (Horizontal)
```javascript
// Timeline line
slide.addShape(pres.shapes.LINE, {
  x: 1, y: 2.5, w: 8, h: 0, line: { color: "3E9BA4", width: 2 },
});
// Timeline dots (per step)
slide.addShape(pres.shapes.OVAL, {
  x: stepX - 0.15, y: 2.35, w: 0.3, h: 0.3, fill: { color: "3E9BA4" },
});
```

## PptxGenJS Critical Rules

1. **No `#` in hex colors**: `"1B4565"` not `"#1B4565"`
2. **No opacity in hex**: Use `opacity: 0.1` property, not 8-char color
3. **Use `bullet: true`**: Never unicode bullet (double bullets)
4. **Use `breakLine: true`**: Between text array items
5. **Fresh option objects**: PptxGenJS mutates - use factory functions
6. **Use `paraSpaceAfter`**: Not `lineSpacing` with bullets
