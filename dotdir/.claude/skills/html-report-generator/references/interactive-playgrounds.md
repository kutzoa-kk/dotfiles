# Interactive Playgrounds

Use when the user wants to **tune a value, animation, prompt, or design**
and have the result handed back as something pasteable. The pattern:

1. Render a live preview of the thing being tuned.
2. Expose controls (slider, color picker, dropdown, drag-and-drop) that
   adjust it.
3. End with a **"Copy as prompt / JSON / Markdown"** button that exports
   the user's choices in a form Claude can read.

The export step is what turns a playground from "a fun demo" into a real
loop — the user adjusts, copies, pastes back into Claude, iterates.

## When this pattern shines

- "Make me a checkout button animation; let me try several easings."
- "I'm tuning a system prompt; give me a side-by-side editor with live preview."
- "Find the right gradient angle / brand color combo."
- "Show me how this regex matches under different inputs."
- "Build a chart whose styling I can adjust."

## Skeleton

```html
<div class="playground">
  <section class="playground__preview">
    <!-- Live preview of the thing being tuned. -->
    <button id="preview-btn" class="cta">Buy now</button>
  </section>

  <section class="playground__controls">
    <label>
      <span class="caption">Hue</span>
      <input type="range" min="0" max="360" value="255" data-param="hue">
      <output data-output="hue">255</output>
    </label>
    <label>
      <span class="caption">Lightness</span>
      <input type="range" min="0" max="100" value="55" data-param="lightness">
      <output data-output="lightness">55</output>
    </label>
    <label>
      <span class="caption">Duration (ms)</span>
      <input type="number" min="0" max="2000" step="50" value="280" data-param="duration">
    </label>
    <label>
      <span class="caption">Easing</span>
      <select data-param="easing">
        <option>ease</option>
        <option>ease-in</option>
        <option>ease-out</option>
        <option selected>cubic-bezier(0.2,0.7,0.2,1)</option>
      </select>
    </label>

    <button type="button" id="copy-btn" class="copy-btn">Copy as prompt</button>
  </section>
</div>

<script>
(function () {
  const params = {};
  const apply = () => {
    document.querySelectorAll('[data-param]').forEach(input => {
      params[input.dataset.param] = input.value;
      const out = document.querySelector(`[data-output="${input.dataset.param}"]`);
      if (out) out.textContent = input.value;
    });
    const btn = document.getElementById('preview-btn');
    btn.style.background = `oklch(${params.lightness}% 0.18 ${params.hue})`;
    btn.style.transition = `background ${params.duration}ms ${params.easing}`;
  };
  document.querySelectorAll('[data-param]').forEach(el => el.addEventListener('input', apply));
  apply();

  document.getElementById('copy-btn').addEventListener('click', async () => {
    const text = [
      `Apply this CTA button style:`,
      `- background: oklch(${params.lightness}% 0.18 ${params.hue})`,
      `- transition: background ${params.duration}ms ${params.easing}`,
    ].join('\n');
    await navigator.clipboard.writeText(text);
    const btn = document.getElementById('copy-btn');
    const original = btn.textContent;
    btn.textContent = 'Copied ✓';
    setTimeout(() => { btn.textContent = original; }, 1200);
  });
})();
</script>
```

## Layout

Two-column when the screen has room, stacked on mobile:

```html
<div class="playground" style="
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  align-items: start;
">
  <!-- preview, controls -->
</div>

<style>
  @media (max-width: 700px) {
    .playground { grid-template-columns: 1fr; }
  }
</style>
```

For full-bleed previews (animation, large illustration), put the preview on
top and controls underneath in a sticky bar.

## Control patterns

| Control | Use for | HTML |
|---------|---------|------|
| `input[type=range]` | Continuous numeric (color, easing, opacity) | with paired `<output>` for current value |
| `input[type=number]` | Discrete numeric (duration, count) | with `min`, `max`, `step` |
| `input[type=color]` | Single color pick | renders OS-native picker |
| `<select>` | Enumerated options (easing curve, layout variant) | |
| `input[type=checkbox]` | Boolean flag | |
| `input[type=text]` | Short freeform (label text, copy variant) | |
| `<textarea>` | Multi-line freeform (prompts, system messages) | |

Two-state toggles (light / dark, on / off) look nicer as a labeled radio
group than as a generic checkbox:

```html
<fieldset class="radio-group">
  <legend>Theme</legend>
  <label><input type="radio" name="theme" value="light" checked> Light</label>
  <label><input type="radio" name="theme" value="dark"> Dark</label>
</fieldset>
```

## The copy button is non-negotiable

Without a copy button, the user has to read values off the screen and retype.
The whole point of the playground is to skip that. The button output should
be:

- A **prompt** the user pastes back into Claude (most common).
- A **JSON / YAML** block they paste into config.
- A **code snippet** (CSS rule, function call) they paste into the codebase.
- A **diff** of what changed from defaults.

Multiple buttons are fine — let the user pick the format.

```html
<button data-export="prompt">Copy as prompt</button>
<button data-export="json">Copy as JSON</button>
<button data-export="css">Copy as CSS</button>
```

```js
const exporters = {
  prompt: () => `Update the CTA to match: ${describe(params)}`,
  json:   () => JSON.stringify(params, null, 2),
  css:    () => `.cta { background: oklch(${params.lightness}% 0.18 ${params.hue}); transition: background ${params.duration}ms ${params.easing}; }`,
};
document.querySelectorAll('[data-export]').forEach(b => {
  b.addEventListener('click', async () => {
    await navigator.clipboard.writeText(exporters[b.dataset.export]());
    flashFeedback(b);
  });
});
```

## Worked example: side-by-side prompt tuner

The user wants to tune a system prompt and see the effect on multiple sample
inputs at once.

```html
<div class="playground" style="grid-template-columns: 1fr 1fr;">
  <section>
    <h3>System prompt</h3>
    <textarea id="prompt" rows="16" style="width:100%;font-family:var(--font-mono);">
You are a helpful assistant. Be concise.
    </textarea>
    <p class="caption" id="token-count">~0 tokens</p>
    <button id="copy">Copy current prompt</button>
  </section>

  <section>
    <h3>Filled examples</h3>
    <div id="examples"></div>
  </section>
</div>

<script>
const samples = [
  { user: "How do I sort a list in Python?" },
  { user: "Explain monads to me." },
  { user: "What's the capital of Australia?" },
];
const render = () => {
  const prompt = document.getElementById('prompt').value;
  document.getElementById('token-count').textContent = `~${Math.ceil(prompt.length / 4)} tokens`;
  document.getElementById('examples').innerHTML = samples.map(s => `
    <div class="card">
      <p class="caption">User: ${s.user}</p>
      <pre style="white-space:pre-wrap;font-size:0.85em;">${prompt}\n\nUser: ${s.user}</pre>
    </div>
  `).join('');
};
document.getElementById('prompt').addEventListener('input', render);
document.getElementById('copy').addEventListener('click', async () => {
  await navigator.clipboard.writeText(document.getElementById('prompt').value);
});
render();
</script>
```

## Common mistakes

- **No live preview.** A panel of sliders with no visible effect feels broken.
  The preview is the whole product.
- **No copy button.** The user finds the right value, then has to manually
  transcribe it. Defeats the purpose.
- **Resetting all params when one changes.** Make controls independent;
  don't recompute defaults on each input.
- **Slider with no readout.** Pair every `range` with an `<output>` showing
  the current value.
- **Controls behind a tab the user can't see.** Keep all knobs visible at
  once if possible. Cognitive load is the cost of every hidden control.

## When NOT to use

- The user wants a final value, not exploration — just produce the value.
- The thing to tune is binary or has 2–3 options — radio buttons in a
  paragraph are fine, no need for a playground.
- The artifact is meant to be read, not interacted with — make a static
  comparison grid (see [comparison-grids.md](comparison-grids.md)).
