# Code Review HTML

Use when explaining a PR, walking through unfamiliar code, or attaching a
human-readable review to a change. The HTML version of a PR explainer is
strictly better than the GitHub diff view for non-trivial changes because:

- You can **annotate specific lines** with prose (not just a comment thread).
- You can **render diagrams** of the data flow alongside the diff.
- You can **color-code findings by severity** so the reader triages instantly.
- You can **link** to related code, ADRs, dashboards, and prior incidents.
- The reviewer can read it on their phone, share it with someone outside
  GitHub, or save it.

## When this pattern shines

- The PR is non-trivial (>200 lines or touches concurrency / data integrity).
- The author wants to **brief** reviewers before they look at the diff.
- The reviewer wants to **explain their concerns** in one place.
- Onboarding a new engineer to a piece of complex code.
- Post-mortem analysis pointing at specific commits.

## Skeleton

```html
<header class="report-header">
  <p class="eyebrow">PR Review · #4218 · 2026-05-12</p>
  <h1>Streaming backpressure rework</h1>
  <p class="lead">12 files, +482/-187. Replaces blocking queue with a
  reactive stream. Focus areas: backpressure correctness, timeout handling,
  shutdown ordering.</p>
  <dl class="report-meta">
    <span><dt>Author</dt><dd>@alice</dd></span>
    <span><dt>Reviewer</dt><dd>@bob</dd></span>
    <span><dt>Status</dt><dd><span class="pip pip--warning"></span> Needs changes</dd></span>
  </dl>
</header>

<section id="summary" data-toc="サマリー">
  <h2 style="margin-top:0;padding-top:0;border-top:0;">サマリー</h2>
  <p>本PRはストリーミング処理の backpressure を Reactor 風の reactive stream
  に置き換える。設計の方向は妥当だが、シャットダウン順序とタイムアウト挙動に
  Critical 1件 / High 2件あり修正必須。</p>
</section>

<section id="findings" data-toc="発見">
  <h2>発見サマリー</h2>
  <div class="grid-kpi">
    <div class="kpi"><p class="kpi__label">Critical</p>
      <div class="kpi__value" style="color:var(--color-danger);">1</div></div>
    <div class="kpi"><p class="kpi__label">High</p>
      <div class="kpi__value" style="color:var(--color-warning);">2</div></div>
    <div class="kpi"><p class="kpi__label">Medium</p>
      <div class="kpi__value">4</div></div>
    <div class="kpi"><p class="kpi__label">Praise</p>
      <div class="kpi__value" style="color:var(--color-success);">3</div></div>
  </div>
</section>

<section id="dataflow" data-toc="データフロー">
  <h2>データフロー</h2>
  <p>新しいパイプラインの全体像。番号は下の Findings と対応。</p>
  <div class="architecture"><pre class="mermaid">
flowchart LR
  Src[Source] --> Buf[Bounded buffer]
  Buf --> Proc[Processor]
  Proc --> Sink[Sink]
  Buf -.->|F-001 overflow| Drop[Drop policy]
  Proc -.->|F-002 timeout| Halt[Halt]
  </pre></div>
</section>

<section id="reviews" data-toc="コードレビュー詳細">
  <h2>コードレビュー詳細</h2>
  <!-- See diff-with-annotations pattern below -->
</section>
```

## Diff with inline annotations

The core pattern: render a diff with a margin column for your comments,
color-coded by severity. Don't try to recreate GitHub's full diff view —
focus on the lines you're commenting on.

```html
<article class="review-finding" id="F-001">
  <header class="review-finding__header">
    <span class="badge badge--critical">Critical</span>
    <h3>F-001 Buffer overflow drops with no metric</h3>
    <p class="caption"><code>src/stream/buffer.ts:42</code></p>
  </header>

  <div class="review-finding__diff">
    <table class="diff-table">
      <tr class="diff-row diff-row--ctx"><td class="diff-line">40</td><td class="diff-code">if (queue.length &gt;= MAX_BUFFER) {</td><td class="diff-note"></td></tr>
      <tr class="diff-row diff-row--add"><td class="diff-line">41</td><td class="diff-code">  queue.shift();</td><td class="diff-note"><span class="badge badge--critical">Drop is silent — no metric, no log.</span></td></tr>
      <tr class="diff-row diff-row--ctx"><td class="diff-line">42</td><td class="diff-code">}</td><td class="diff-note"></td></tr>
    </table>
  </div>

  <div class="review-finding__body">
    <p><strong>影響:</strong> Backpressure 過剰時にメッセージが silent drop され、
    監視からは検知不能。前回のインシデント #1207 と同じパターン。</p>
    <p><strong>推奨:</strong> drop時に <code>metrics.buffer_drops.inc()</code>
    を呼び、サンプルログを出す。policy 自体は議論する価値あり (drop-oldest vs
    drop-newest vs reject)。</p>
  </div>
</article>
```

CSS for the diff rows (drop-in to the base scaffold):

```css
.diff-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}
.diff-row td { padding: 0.25rem 0.75rem; vertical-align: top; }
.diff-line  { color: var(--color-faint); user-select: none; width: 3rem; text-align: right; }
.diff-code  { white-space: pre; }
.diff-note  { width: 28%; font-family: var(--font-sans); font-size: 0.8rem; }
.diff-row--add  { background: color-mix(in oklch, var(--color-success), transparent 92%); }
.diff-row--del  { background: color-mix(in oklch, var(--color-danger),  transparent 92%); }
.diff-row--ctx  { background: transparent; }
.diff-row--add .diff-code::before { content: "+ "; color: var(--color-success); }
.diff-row--del .diff-code::before { content: "− "; color: var(--color-danger);  }
.diff-row--ctx .diff-code::before { content: "  "; }
```

## Side-by-side (before / after)

For larger structural changes, side-by-side reads better than unified diff:

```html
<div class="grid-kpi" style="grid-template-columns: 1fr 1fr;">
  <div class="card">
    <h3 class="chart-card__title">Before</h3>
    <pre><code>function handle(req) {
  const data = readSync(req);
  process(data);
}</code></pre>
  </div>
  <div class="card">
    <h3 class="chart-card__title">After</h3>
    <pre><code>async function handle(req) {
  const data = await readAsync(req);
  return process(data);
}</code></pre>
  </div>
</div>
```

## File tree

For PRs touching many files, a file tree with severity dots gives instant
orientation:

```html
<ul class="file-tree">
  <li><code>src/stream/</code>
    <ul>
      <li><span class="pip pip--danger"></span> <a href="#F-001"><code>buffer.ts</code></a> <span class="caption">+24/-8</span></li>
      <li><span class="pip pip--warning"></span> <a href="#F-002"><code>processor.ts</code></a> <span class="caption">+102/-44</span></li>
      <li><span class="pip pip--success"></span> <code>sink.ts</code> <span class="caption">+18/-12</span></li>
    </ul>
  </li>
  <li><code>tests/</code>
    <ul>
      <li><span class="pip pip--info"></span> <code>buffer.test.ts</code> <span class="caption">+45/-0</span></li>
    </ul>
  </li>
</ul>

<style>
.file-tree, .file-tree ul { list-style: none; padding-left: 1.5rem; margin: 0; }
.file-tree > li > ul { border-left: 1px dashed var(--color-border); }
.file-tree li { padding: 0.2rem 0; line-height: 1.6; }
</style>
```

## Praise

A review with only criticism produces defensive authors. Reserve a section
for **what the author got right** — same severity-card layout, with
`badge--success`. Real praise (pointing at a specific decision) builds
review trust over time.

```html
<article class="review-finding">
  <header>
    <span class="badge badge--success">Praise</span>
    <h3>P-001 Clean separation between policy and mechanism</h3>
  </header>
  <p>Pulling the drop policy out as a strategy interface makes future
  variants trivial — drop-oldest / drop-newest / reject can all plug in
  without changing the buffer.</p>
</article>
```

## Decision needed

End with the explicit ask. Often it's "approve with the Critical fixes" or
"hold for a follow-up RFC."

```html
<section class="card" style="margin-top:3rem;border-left:3px solid var(--color-accent);">
  <h2 style="margin:0;">判断</h2>
  <p>F-001 (Critical) は今回のPRで修正必須。F-002, F-003 (High) は
  別PRで対応OK、ただし期限 5/20。それ以外の Medium はマージ後の
  cleanup PR にまとめても可。</p>
</section>
```

## Common mistakes

- **Recreating GitHub's diff view in full.** You can't beat them at their
  own game and you don't need to. Focus on the lines you're commenting on.
- **Severity inflation.** Mark only what's actually Critical critical.
  Two findings in a small PR shouldn't both be Critical.
- **No data flow diagram.** For PRs that change how data moves, a 5-node
  Mermaid diagram is worth 3 paragraphs of prose.
- **Buried decisions.** End the page with the explicit ask, near the top
  if you can. The reviewer should know what they're being asked to approve.
- **No "what's NOT covered" section.** If the PR explicitly defers some
  concerns (perf, migration, monitoring) to a follow-up, name them so the
  reader doesn't ask about them.

## Worked example prompts

- > "Help me review this PR by creating an HTML artifact that describes it.
  > I'm not very familiar with the streaming/backpressure logic so focus
  > on that. Render the actual diff with inline margin annotations,
  > color-code findings by severity and whatever else might be needed to
  > convey the concept well."

- > "Walk me through the auth middleware code. Make an HTML explainer:
  > flowchart of request lifecycle, the 4–5 key code snippets annotated,
  > and a gotchas section. Optimize for someone reading it once."

- > "Generate a PR pre-review for the rate limiter rewrite — sections for
  > what changed, what to look at carefully, what's deferred, and my
  > recommendation. Color-code concerns by severity."
