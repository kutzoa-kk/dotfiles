# Layout Patterns Reference

40レイアウトパターンの詳細リファレンス。

## Table of Contents

1. [Title Slides (1-5)](#title-slides-1-5)
2. [Single Column (6-12)](#single-column-6-12)
3. [Two Column (13-22)](#two-column-13-22)
4. [Three Column (23-28)](#three-column-23-28)
5. [Grid (29-34)](#grid-29-34)
6. [Chart (35-38)](#chart-35-38)
7. [Closing (39-40)](#closing-39-40)

---

## Title Slides (1-5)

### Pattern 1: Hero Title

フルスクリーンタイトル。プレゼン冒頭に最適。

```html
<!-- _class: title-hero -->
<div class="flex flex-col justify-center items-center h-full text-center">
  <h1 class="text-em-3xl text-navy mb-4">Main Title</h1>
  <p class="text-em-xl text-secondary">Subtitle or tagline</p>
</div>
```

### Pattern 2: Title with Background

背景画像付きタイトル。

```html
<!-- _class: title-bg -->
<div class="relative h-full">
  <div class="absolute inset-0 bg-navy opacity-60"></div>
  <div class="relative z-10 flex flex-col justify-center items-center h-full text-center text-white">
    <h1 class="text-em-3xl mb-4">Title Over Image</h1>
    <p class="text-em-lg">Subtitle</p>
  </div>
</div>
```

### Pattern 3: Split Title

左右分割タイトル。

```html
<!-- _class: title-split -->
<div class="grid grid-cols-2 h-full">
  <div class="bg-navy flex items-center justify-center p-12">
    <h1 class="text-em-2xl text-white">Title</h1>
  </div>
  <div class="flex items-center justify-center p-12">
    <p class="text-em-lg text-secondary">Description</p>
  </div>
</div>
```

### Pattern 4: Section Break

セクション区切り。

```html
<!-- _class: section-break -->
<div class="flex items-center h-full">
  <div class="border-l-4 border-teal pl-8">
    <p class="text-em-base text-muted mb-2">Section 01</p>
    <h2 class="text-em-2xl text-navy">Section Title</h2>
  </div>
</div>
```

### Pattern 5: Chapter Title

チャプタータイトル。

```html
<!-- _class: chapter -->
<div class="flex flex-col justify-end h-full pb-16">
  <span class="text-em-3xl text-teal font-bold mb-4">01</span>
  <h2 class="text-em-2xl text-navy">Chapter Title</h2>
</div>
```

---

## Single Column (6-12)

### Pattern 6: Text Only

テキストのみ。説明スライドに。

```html
<!-- _class: text-only -->
<div class="max-w-3xl mx-auto py-12">
  <h2 class="text-em-2xl text-navy mb-6">Heading</h2>
  <p class="text-em-lg text-secondary leading-relaxed">
    Body text content here. Keep it concise and focused on one key message.
  </p>
</div>
```

### Pattern 7: Bullet List

箇条書きリスト。

```html
<!-- _class: bullet-list -->
<div class="max-w-3xl mx-auto py-12">
  <h2 class="text-em-2xl text-navy mb-8">Key Points</h2>
  <ul class="space-y-4 text-em-lg">
    <li class="flex items-start">
      <span class="text-teal mr-4">●</span>
      <span>First point with explanation</span>
    </li>
    <li class="flex items-start">
      <span class="text-teal mr-4">●</span>
      <span>Second point with explanation</span>
    </li>
    <li class="flex items-start">
      <span class="text-teal mr-4">●</span>
      <span>Third point with explanation</span>
    </li>
  </ul>
</div>
```

### Pattern 8: Quote

引用。インパクトのある言葉に。

```html
<!-- _class: quote -->
<div class="flex items-center justify-center h-full">
  <blockquote class="max-w-2xl text-center">
    <p class="text-em-xl text-navy italic mb-6">
      "Quote text goes here. Make it memorable and impactful."
    </p>
    <cite class="text-em-base text-muted">— Author Name, Title</cite>
  </blockquote>
</div>
```

### Pattern 9: Big Number

数字の強調。統計・実績に。

```html
<!-- _class: big-number -->
<div class="flex flex-col items-center justify-center h-full text-center">
  <span class="text-em-3xl text-teal font-bold">85%</span>
  <p class="text-em-xl text-navy mt-4">Metric Description</p>
  <p class="text-em-base text-muted mt-2">Additional context</p>
</div>
```

### Pattern 10: Numbered List

番号付きリスト。手順説明に。

```html
<!-- _class: numbered-list -->
<div class="max-w-3xl mx-auto py-12">
  <h2 class="text-em-2xl text-navy mb-8">Steps</h2>
  <ol class="space-y-6">
    <li class="flex items-start">
      <span class="text-em-xl text-teal font-bold mr-6 w-8">1</span>
      <div>
        <h3 class="text-em-lg text-navy font-semibold">Step Title</h3>
        <p class="text-em-base text-secondary">Description</p>
      </div>
    </li>
    <!-- Repeat for each step -->
  </ol>
</div>
```

### Pattern 11: Definition

用語定義。コンセプト説明に。

```html
<!-- _class: definition -->
<div class="flex items-center justify-center h-full">
  <div class="max-w-2xl">
    <h2 class="text-em-3xl text-navy mb-4">Term</h2>
    <p class="text-em-lg text-secondary border-l-4 border-teal pl-6">
      Definition or explanation of the term.
    </p>
  </div>
</div>
```

### Pattern 12: Timeline Vertical

縦タイムライン。

```html
<!-- _class: timeline-vertical -->
<div class="max-w-2xl mx-auto py-8">
  <div class="relative border-l-2 border-teal pl-8 space-y-8">
    <div class="relative">
      <span class="absolute -left-10 w-4 h-4 bg-teal rounded-full"></span>
      <span class="text-em-base text-muted">2020</span>
      <h3 class="text-em-lg text-navy">Event Title</h3>
    </div>
    <!-- Repeat for each event -->
  </div>
</div>
```

---

## Two Column (13-22)

### Pattern 13: Equal Columns

均等2カラム。

```html
<!-- _class: two-col-equal -->
<div class="grid grid-cols-2 gap-12 h-full items-center p-12">
  <div>
    <h3 class="text-em-xl text-navy mb-4">Left Title</h3>
    <p class="text-em-lg text-secondary">Left content</p>
  </div>
  <div>
    <h3 class="text-em-xl text-navy mb-4">Right Title</h3>
    <p class="text-em-lg text-secondary">Right content</p>
  </div>
</div>
```

### Pattern 14: Image Left

左画像・右テキスト。

```html
<!-- _class: img-left -->
<div class="grid grid-cols-2 gap-8 h-full items-center">
  <div class="bg-secondary rounded-lg h-full flex items-center justify-center">
    <img src="image.png" alt="Description" class="max-h-full object-contain">
  </div>
  <div class="p-8">
    <h2 class="text-em-2xl text-navy mb-4">Title</h2>
    <p class="text-em-lg text-secondary">Description text</p>
  </div>
</div>
```

### Pattern 15: Image Right

左テキスト・右画像。

```html
<!-- _class: img-right -->
<div class="grid grid-cols-2 gap-8 h-full items-center">
  <div class="p-8">
    <h2 class="text-em-2xl text-navy mb-4">Title</h2>
    <p class="text-em-lg text-secondary">Description text</p>
  </div>
  <div class="bg-secondary rounded-lg h-full flex items-center justify-center">
    <img src="image.png" alt="Description" class="max-h-full object-contain">
  </div>
</div>
```

### Pattern 16: Wide Left (2:1)

左側大きめ（2:1比率）。

```html
<!-- _class: wide-left -->
<div class="grid grid-cols-3 gap-8 h-full items-center">
  <div class="col-span-2 p-8">
    <h2 class="text-em-2xl text-navy mb-4">Main Content</h2>
    <p class="text-em-lg text-secondary">Detailed explanation</p>
  </div>
  <div class="bg-secondary rounded-lg p-6">
    <p class="text-em-base">Side note or image</p>
  </div>
</div>
```

### Pattern 17: Wide Right (1:2)

右側大きめ（1:2比率）。

```html
<!-- _class: wide-right -->
<div class="grid grid-cols-3 gap-8 h-full items-center">
  <div class="bg-secondary rounded-lg p-6">
    <p class="text-em-base">Side note</p>
  </div>
  <div class="col-span-2 p-8">
    <h2 class="text-em-2xl text-navy mb-4">Main Content</h2>
    <p class="text-em-lg text-secondary">Detailed explanation</p>
  </div>
</div>
```

### Pattern 18: Comparison

比較レイアウト。Before/After、A vs Bに。

```html
<!-- _class: comparison -->
<div class="grid grid-cols-2 gap-8 h-full p-8">
  <div class="bg-secondary rounded-lg p-8 flex flex-col">
    <span class="text-em-base text-teal font-semibold mb-4">Before</span>
    <h3 class="text-em-xl text-navy mb-4">Title A</h3>
    <ul class="space-y-2 text-em-base text-secondary">
      <li>• Point 1</li>
      <li>• Point 2</li>
    </ul>
  </div>
  <div class="bg-navy rounded-lg p-8 flex flex-col text-white">
    <span class="text-em-base text-teal font-semibold mb-4">After</span>
    <h3 class="text-em-xl mb-4">Title B</h3>
    <ul class="space-y-2 text-em-base opacity-90">
      <li>• Point 1</li>
      <li>• Point 2</li>
    </ul>
  </div>
</div>
```

### Pattern 19: Stats Two Column

2カラム統計。

```html
<!-- _class: stats-two -->
<div class="grid grid-cols-2 gap-12 h-full items-center p-12">
  <div class="text-center">
    <span class="text-em-3xl text-teal font-bold block">42%</span>
    <p class="text-em-lg text-navy mt-2">Metric One</p>
  </div>
  <div class="text-center">
    <span class="text-em-3xl text-navy font-bold block">3.5x</span>
    <p class="text-em-lg text-secondary mt-2">Metric Two</p>
  </div>
</div>
```

### Pattern 20: Code + Explanation

コード＋説明。技術スライドに。

```html
<!-- _class: code-explain -->
<div class="grid grid-cols-2 gap-8 h-full items-center">
  <div class="bg-gray-900 rounded-lg p-6 text-white font-mono text-em-base overflow-auto">
    <pre><code>// Code here
const example = "value";</code></pre>
  </div>
  <div class="p-8">
    <h3 class="text-em-xl text-navy mb-4">Explanation</h3>
    <p class="text-em-lg text-secondary">What this code does...</p>
  </div>
</div>
```

### Pattern 21: Pros and Cons

メリット・デメリット。

```html
<!-- _class: pros-cons -->
<div class="grid grid-cols-2 gap-8 h-full p-8">
  <div>
    <h3 class="text-em-xl text-teal mb-6 flex items-center">
      <span class="mr-2">✓</span> Pros
    </h3>
    <ul class="space-y-3 text-em-lg text-secondary">
      <li>• Advantage 1</li>
      <li>• Advantage 2</li>
    </ul>
  </div>
  <div>
    <h3 class="text-em-xl text-navy mb-6 flex items-center">
      <span class="mr-2">✗</span> Cons
    </h3>
    <ul class="space-y-3 text-em-lg text-secondary">
      <li>• Disadvantage 1</li>
      <li>• Disadvantage 2</li>
    </ul>
  </div>
</div>
```

### Pattern 22: Timeline Horizontal

横タイムライン。

```html
<!-- _class: timeline-horizontal -->
<div class="h-full flex flex-col justify-center p-12">
  <h2 class="text-em-2xl text-navy mb-12 text-center">Timeline</h2>
  <div class="flex justify-between items-start">
    <div class="text-center flex-1">
      <div class="w-4 h-4 bg-teal rounded-full mx-auto mb-4"></div>
      <span class="text-em-base text-muted">2021</span>
      <p class="text-em-lg text-navy">Event</p>
    </div>
    <!-- Repeat -->
  </div>
  <div class="h-0.5 bg-teal -mt-16 mx-8"></div>
</div>
```

---

## Three Column (23-28)

### Pattern 23: Equal Three

均等3カラム。

```html
<!-- _class: three-col-equal -->
<div class="grid grid-cols-3 gap-8 h-full items-center p-8">
  <div class="text-center">
    <h3 class="text-em-xl text-navy mb-4">Column 1</h3>
    <p class="text-em-base text-secondary">Content</p>
  </div>
  <div class="text-center">
    <h3 class="text-em-xl text-navy mb-4">Column 2</h3>
    <p class="text-em-base text-secondary">Content</p>
  </div>
  <div class="text-center">
    <h3 class="text-em-xl text-navy mb-4">Column 3</h3>
    <p class="text-em-base text-secondary">Content</p>
  </div>
</div>
```

### Pattern 24: Feature Cards

機能カード。

```html
<!-- _class: feature-cards -->
<div class="grid grid-cols-3 gap-6 h-full items-center p-8">
  <div class="bg-secondary rounded-lg p-6 text-center">
    <span class="text-em-2xl text-teal mb-4 block">🚀</span>
    <h3 class="text-em-lg text-navy mb-2">Feature 1</h3>
    <p class="text-em-base text-secondary">Description</p>
  </div>
  <!-- Repeat for 2 more -->
</div>
```

### Pattern 25: Stats Three

3カラム統計。

```html
<!-- _class: stats-three -->
<div class="grid grid-cols-3 gap-8 h-full items-center p-8">
  <div class="text-center">
    <span class="text-em-3xl text-teal font-bold">100+</span>
    <p class="text-em-lg text-navy mt-2">Customers</p>
  </div>
  <div class="text-center">
    <span class="text-em-3xl text-navy font-bold">50M</span>
    <p class="text-em-lg text-secondary mt-2">Users</p>
  </div>
  <div class="text-center">
    <span class="text-em-3xl text-teal font-bold">99.9%</span>
    <p class="text-em-lg text-navy mt-2">Uptime</p>
  </div>
</div>
```

### Pattern 26: Process Steps

プロセスステップ。

```html
<!-- _class: process-steps -->
<div class="h-full flex flex-col justify-center p-8">
  <h2 class="text-em-2xl text-navy mb-8 text-center">Process</h2>
  <div class="grid grid-cols-3 gap-4">
    <div class="text-center">
      <div class="w-12 h-12 bg-teal text-white rounded-full flex items-center justify-center mx-auto text-em-xl font-bold">1</div>
      <h3 class="text-em-lg text-navy mt-4">Step 1</h3>
      <p class="text-em-base text-secondary">Description</p>
    </div>
    <!-- Repeat for steps 2, 3 -->
  </div>
</div>
```

### Pattern 27: Team/Person

チーム紹介。

```html
<!-- _class: team -->
<div class="grid grid-cols-3 gap-8 h-full items-center p-8">
  <div class="text-center">
    <div class="w-24 h-24 bg-secondary rounded-full mx-auto mb-4"></div>
    <h3 class="text-em-lg text-navy">Name</h3>
    <p class="text-em-base text-teal">Role</p>
  </div>
  <!-- Repeat -->
</div>
```

### Pattern 28: Icon List Three

3カラムアイコンリスト。

```html
<!-- _class: icon-list-three -->
<div class="grid grid-cols-3 gap-6 h-full items-start p-8 pt-16">
  <div>
    <span class="text-em-2xl text-teal block mb-4">📊</span>
    <h3 class="text-em-lg text-navy mb-2">Title</h3>
    <ul class="text-em-base text-secondary space-y-1">
      <li>• Item 1</li>
      <li>• Item 2</li>
    </ul>
  </div>
  <!-- Repeat -->
</div>
```

---

## Grid (29-34)

### Pattern 29: 2x2 Grid

2x2グリッド。

```html
<!-- _class: grid-2x2 -->
<div class="grid grid-cols-2 grid-rows-2 gap-6 h-full p-8">
  <div class="bg-secondary rounded-lg p-6">
    <h3 class="text-em-lg text-navy mb-2">Cell 1</h3>
    <p class="text-em-base text-secondary">Content</p>
  </div>
  <div class="bg-secondary rounded-lg p-6">
    <h3 class="text-em-lg text-navy mb-2">Cell 2</h3>
    <p class="text-em-base text-secondary">Content</p>
  </div>
  <div class="bg-secondary rounded-lg p-6">
    <h3 class="text-em-lg text-navy mb-2">Cell 3</h3>
    <p class="text-em-base text-secondary">Content</p>
  </div>
  <div class="bg-secondary rounded-lg p-6">
    <h3 class="text-em-lg text-navy mb-2">Cell 4</h3>
    <p class="text-em-base text-secondary">Content</p>
  </div>
</div>
```

### Pattern 30: 3x2 Grid

3x2グリッド。

```html
<!-- _class: grid-3x2 -->
<div class="grid grid-cols-3 grid-rows-2 gap-4 h-full p-6">
  <!-- 6 cells -->
</div>
```

### Pattern 31: Image Gallery 4

4枚画像ギャラリー。

```html
<!-- _class: gallery-4 -->
<div class="grid grid-cols-2 grid-rows-2 gap-4 h-full p-8">
  <div class="bg-secondary rounded-lg overflow-hidden">
    <img src="1.png" class="w-full h-full object-cover">
  </div>
  <!-- Repeat 3 more -->
</div>
```

### Pattern 32: Image Gallery 6

6枚画像ギャラリー。

```html
<!-- _class: gallery-6 -->
<div class="grid grid-cols-3 grid-rows-2 gap-4 h-full p-6">
  <!-- 6 images -->
</div>
```

### Pattern 33: Matrix

マトリクス表。

```html
<!-- _class: matrix -->
<div class="h-full p-8">
  <table class="w-full h-full border-collapse">
    <thead>
      <tr class="bg-navy text-white">
        <th class="p-4 text-em-base"></th>
        <th class="p-4 text-em-base">Option A</th>
        <th class="p-4 text-em-base">Option B</th>
      </tr>
    </thead>
    <tbody>
      <tr class="border-b">
        <td class="p-4 text-em-base text-navy font-semibold">Criteria 1</td>
        <td class="p-4 text-em-base text-secondary text-center">✓</td>
        <td class="p-4 text-em-base text-secondary text-center">✗</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Pattern 34: SWOT

SWOT分析。

```html
<!-- _class: swot -->
<div class="grid grid-cols-2 grid-rows-2 gap-4 h-full p-6">
  <div class="bg-teal bg-opacity-20 rounded-lg p-4">
    <h3 class="text-em-lg text-teal mb-2">Strengths</h3>
    <ul class="text-em-base"><!-- items --></ul>
  </div>
  <div class="bg-navy bg-opacity-20 rounded-lg p-4">
    <h3 class="text-em-lg text-navy mb-2">Weaknesses</h3>
    <ul class="text-em-base"><!-- items --></ul>
  </div>
  <div class="bg-secondary rounded-lg p-4">
    <h3 class="text-em-lg text-navy mb-2">Opportunities</h3>
    <ul class="text-em-base"><!-- items --></ul>
  </div>
  <div class="bg-gray-200 rounded-lg p-4">
    <h3 class="text-em-lg text-navy mb-2">Threats</h3>
    <ul class="text-em-base"><!-- items --></ul>
  </div>
</div>
```

---

## Chart (35-38)

### Pattern 35: Bar Chart Placeholder

棒グラフ用。

```html
<!-- _class: chart-bar -->
<div class="h-full p-8">
  <h2 class="text-em-2xl text-navy mb-8">Chart Title</h2>
  <div class="flex items-end justify-around h-64 border-b border-l border-gray-300">
    <div class="flex flex-col items-center">
      <div class="w-16 bg-teal rounded-t" style="height: 60%"></div>
      <span class="text-em-base text-secondary mt-2">A</span>
    </div>
    <div class="flex flex-col items-center">
      <div class="w-16 bg-navy rounded-t" style="height: 80%"></div>
      <span class="text-em-base text-secondary mt-2">B</span>
    </div>
    <div class="flex flex-col items-center">
      <div class="w-16 bg-teal rounded-t" style="height: 45%"></div>
      <span class="text-em-base text-secondary mt-2">C</span>
    </div>
  </div>
</div>
```

### Pattern 36: Pie Chart Placeholder

円グラフ用（プレースホルダー）。

```html
<!-- _class: chart-pie -->
<div class="h-full flex items-center justify-center p-8">
  <div class="flex items-center gap-12">
    <div class="w-64 h-64 rounded-full bg-gradient-to-r from-teal to-navy"></div>
    <div class="space-y-4">
      <div class="flex items-center">
        <span class="w-4 h-4 bg-teal rounded mr-3"></span>
        <span class="text-em-base">Category A - 60%</span>
      </div>
      <div class="flex items-center">
        <span class="w-4 h-4 bg-navy rounded mr-3"></span>
        <span class="text-em-base">Category B - 40%</span>
      </div>
    </div>
  </div>
</div>
```

### Pattern 37: Line Chart Placeholder

折れ線グラフ用。

```html
<!-- _class: chart-line -->
<div class="h-full p-8">
  <h2 class="text-em-2xl text-navy mb-6">Trend Over Time</h2>
  <div class="h-64 border-b border-l border-gray-300 relative">
    <!-- SVG path or placeholder -->
    <svg class="w-full h-full">
      <path d="M 0 200 L 100 150 L 200 100 L 300 120 L 400 50"
            stroke="#3E9BA4" stroke-width="3" fill="none"/>
    </svg>
  </div>
</div>
```

### Pattern 38: Funnel

ファネル図。

```html
<!-- _class: funnel -->
<div class="h-full flex flex-col items-center justify-center p-8">
  <h2 class="text-em-2xl text-navy mb-8">Funnel</h2>
  <div class="space-y-2 w-full max-w-lg">
    <div class="bg-teal text-white text-center py-3 rounded text-em-lg" style="width: 100%">Awareness - 1000</div>
    <div class="bg-teal bg-opacity-80 text-white text-center py-3 rounded text-em-lg mx-auto" style="width: 75%">Interest - 500</div>
    <div class="bg-navy text-white text-center py-3 rounded text-em-lg mx-auto" style="width: 50%">Decision - 200</div>
    <div class="bg-navy bg-opacity-80 text-white text-center py-3 rounded text-em-lg mx-auto" style="width: 30%">Action - 100</div>
  </div>
</div>
```

---

## Closing (39-40)

### Pattern 39: Call to Action

CTA（行動喚起）。

```html
<!-- _class: cta -->
<div class="flex flex-col items-center justify-center h-full text-center">
  <h2 class="text-em-2xl text-navy mb-6">Ready to Get Started?</h2>
  <p class="text-em-lg text-secondary mb-8 max-w-xl">
    Brief compelling message here.
  </p>
  <div class="bg-teal text-white px-8 py-4 rounded-lg text-em-lg">
    Call to Action
  </div>
</div>
```

### Pattern 40: Thank You

締めくくり。

```html
<!-- _class: thank-you -->
<div class="flex flex-col items-center justify-center h-full text-center">
  <h2 class="text-em-3xl text-navy mb-6">Thank You</h2>
  <p class="text-em-lg text-secondary mb-8">Questions?</p>
  <div class="text-em-base text-muted">
    <p>name@example.com</p>
    <p>@twitter_handle</p>
  </div>
</div>
```
