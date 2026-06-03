# Custom Editing Interfaces

Use when the user wants a **throwaway editor purpose-built for one task**.
Not a product, not a reusable tool — a single HTML file that lets them
manipulate something Claude can't easily manipulate via prose, and then
exports the result.

The pattern, distilled:

1. Read the user's data into the page.
2. Give them a UI tuned for that specific manipulation
   (drag-drop, form, dataset curator, annotator).
3. End with a **"Copy as JSON / Markdown / prompt"** button that emits the
   result for the user to paste back into Claude.

The export is the whole point. Without it, the editor is a toy.

## When this pattern shines

| Task | Editor type |
|------|-------------|
| Reorder / triage / bucket items (tickets, test cases, feedback) | Draggable cards across columns |
| Edit structured config (feature flags, env vars, validation rules) | Form with grouping and dependency warnings |
| Tune a prompt, template, or copy block | Side-by-side editor + live preview |
| Curate a dataset (approve / reject / tag rows) | Table with action buttons |
| Annotate a document, transcript, or diff | Highlighter + comment textarea per span |
| Pick values that hurt to express in text | Color picker, easing curve editor, crop selector, cron builder, regex tester |

## Draggable cards (Now / Next / Later / Cut)

The most common variant. Read the items, render as cards, let the user
drag between columns, export the final state.

```html
<header>
  <h1>Sprint triage</h1>
  <p class="lead">Drag tickets between columns. Pre-sorted by your best guess.</p>
  <button type="button" id="export" class="export-btn">Copy as markdown</button>
</header>

<div class="board">
  <div class="board__column" data-column="Now">
    <header><h2>Now</h2><span class="caption" data-count></span></header>
    <ul class="board__list" data-column-list="Now">
      <li class="card-item" draggable="true" data-id="TKT-101">
        <strong>TKT-101</strong>
        <p>Fix login redirect loop after OIDC change.</p>
      </li>
    </ul>
  </div>
  <div class="board__column" data-column="Next">
    <header><h2>Next</h2><span class="caption" data-count></span></header>
    <ul class="board__list" data-column-list="Next"></ul>
  </div>
  <div class="board__column" data-column="Later">
    <header><h2>Later</h2><span class="caption" data-count></span></header>
    <ul class="board__list" data-column-list="Later"></ul>
  </div>
  <div class="board__column" data-column="Cut">
    <header><h2>Cut</h2><span class="caption" data-count></span></header>
    <ul class="board__list" data-column-list="Cut"></ul>
  </div>
</div>

<style>
  .board {
    display: grid;
    grid-template-columns: repeat(4, minmax(220px, 1fr));
    gap: 1rem;
  }
  .board__column {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 0.75rem;
    min-height: 200px;
  }
  .board__column.is-drop-target {
    border-color: var(--color-accent);
    background: color-mix(in oklch, var(--color-accent), transparent 92%);
  }
  .board__list { list-style: none; padding: 0; margin: 0; min-height: 100px; }
  .card-item {
    background: var(--color-surface-2);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    cursor: grab;
  }
  .card-item.is-dragging { opacity: 0.4; }
  .card-item:active { cursor: grabbing; }
</style>

<script>
(function () {
  let dragged = null;

  document.querySelectorAll('.card-item').forEach(card => {
    card.addEventListener('dragstart', e => {
      dragged = card;
      card.classList.add('is-dragging');
      e.dataTransfer.effectAllowed = 'move';
    });
    card.addEventListener('dragend', () => {
      dragged?.classList.remove('is-dragging');
      dragged = null;
      updateCounts();
    });
  });

  document.querySelectorAll('.board__column').forEach(col => {
    col.addEventListener('dragover', e => {
      e.preventDefault();
      col.classList.add('is-drop-target');
    });
    col.addEventListener('dragleave', () => col.classList.remove('is-drop-target'));
    col.addEventListener('drop', e => {
      e.preventDefault();
      col.classList.remove('is-drop-target');
      if (dragged) col.querySelector('[data-column-list]').appendChild(dragged);
    });
  });

  const updateCounts = () => {
    document.querySelectorAll('.board__column').forEach(col => {
      const n = col.querySelectorAll('.card-item').length;
      col.querySelector('[data-count]').textContent = `${n} 件`;
    });
  };
  updateCounts();

  document.getElementById('export').addEventListener('click', async () => {
    const columns = Array.from(document.querySelectorAll('.board__column'));
    const md = columns.map(col => {
      const name = col.dataset.column;
      const items = Array.from(col.querySelectorAll('.card-item'));
      return `## ${name}\n` + (items.length
        ? items.map(c => `- ${c.querySelector('strong').textContent} — ${c.querySelector('p').textContent}`).join('\n')
        : '- (なし)');
    }).join('\n\n');
    await navigator.clipboard.writeText(md);
    const btn = document.getElementById('export');
    btn.textContent = 'Copied ✓';
    setTimeout(() => { btn.textContent = 'Copy as markdown'; }, 1200);
  });
})();
</script>
```

## Form-based config editor

For structured config (feature flags, env vars, validation thresholds),
build a form grouped by concern, with dependency hints and a "diff from
defaults" export.

```html
<form id="config-form">
  <fieldset>
    <legend>Rate limiting</legend>
    <label>
      <span>Enable rate limiting</span>
      <input type="checkbox" name="rate.enabled" checked>
    </label>
    <label>
      <span>Requests per minute</span>
      <input type="number" name="rate.rpm" value="60" min="0" data-depends-on="rate.enabled">
    </label>
    <label>
      <span>Burst</span>
      <input type="number" name="rate.burst" value="20" min="0" data-depends-on="rate.enabled">
    </label>
  </fieldset>

  <fieldset>
    <legend>Logging</legend>
    <label>
      <span>Log level</span>
      <select name="log.level">
        <option>error</option><option selected>warn</option>
        <option>info</option><option>debug</option>
      </select>
    </label>
  </fieldset>

  <div class="form-actions">
    <button type="button" data-export="diff">Copy changed keys only</button>
    <button type="button" data-export="full">Copy full config</button>
  </div>
</form>

<script>
const defaults = { 'rate.enabled': true, 'rate.rpm': 60, 'rate.burst': 20, 'log.level': 'warn' };

function readForm() {
  const result = {};
  document.querySelectorAll('#config-form [name]').forEach(input => {
    const v = input.type === 'checkbox' ? input.checked :
              input.type === 'number'   ? Number(input.value) :
              input.value;
    result[input.name] = v;
  });
  return result;
}

function applyDependencies() {
  document.querySelectorAll('[data-depends-on]').forEach(input => {
    const parent = document.querySelector(`[name="${input.dataset.dependsOn}"]`);
    input.disabled = parent && !parent.checked;
  });
}

document.getElementById('config-form').addEventListener('input', applyDependencies);
applyDependencies();

document.querySelectorAll('[data-export]').forEach(btn => {
  btn.addEventListener('click', async () => {
    const config = readForm();
    const out = btn.dataset.export === 'diff'
      ? Object.fromEntries(Object.entries(config).filter(([k, v]) => defaults[k] !== v))
      : config;
    await navigator.clipboard.writeText(JSON.stringify(out, null, 2));
  });
});
</script>
```

## Dataset curator (approve / reject / tag)

Same skeleton as the data table from the base scaffold, but each row has
action buttons. Export the selection.

```html
<header>
  <h1>Training set curation</h1>
  <p class="lead">Approve, reject, or tag each example. <strong id="counts"></strong>.</p>
  <button id="export-keep">Copy approved as JSONL</button>
</header>

<table class="data-table">
  <thead><tr><th>Input</th><th>Output</th><th>Action</th></tr></thead>
  <tbody id="rows">
    <!-- row template:
    <tr data-state="pending">
      <td>What's 2+2?</td>
      <td>4</td>
      <td>
        <button data-action="keep">Keep</button>
        <button data-action="drop">Drop</button>
        <input data-action="tag" placeholder="tag…">
      </td>
    </tr>
    -->
  </tbody>
</table>
```

The visual cue (row tint, badge) for state lets the user see at a glance
what's left to triage.

## Annotator (highlight + comment)

For reviewing a transcript, diff, or document, let the user select text
and attach a comment.

```html
<article class="annotatable" id="doc">
  <p>The quick brown fox jumps over the lazy dog. The five boxing wizards
  jump quickly.</p>
</article>

<section id="comments">
  <h2>Comments</h2>
  <ul id="comment-list"></ul>
</section>

<script>
let nextId = 1;
document.getElementById('doc').addEventListener('mouseup', () => {
  const sel = window.getSelection();
  const text = sel.toString().trim();
  if (!text) return;
  const id = `note-${nextId++}`;
  const note = prompt(`Comment on: "${text}"`);
  if (!note) return;
  // wrap selection in a span tied to the comment
  const span = document.createElement('mark');
  span.dataset.note = id;
  span.style.background = 'color-mix(in oklch, var(--color-warning), transparent 70%)';
  sel.getRangeAt(0).surroundContents(span);
  const li = document.createElement('li');
  li.id = id;
  li.innerHTML = `<strong>"${text}"</strong><br>${note}`;
  document.getElementById('comment-list').appendChild(li);
  sel.removeAllRanges();
});
</script>
```

## The export step

The export button is the entire reason this pattern works. Without it:
the user manipulates the UI, sees what they want, and has to retype it
into Claude. With it: one click, paste, continue.

Export formats by use case:

| Editor | Export format |
|--------|---------------|
| Card triage | Markdown grouped by column |
| Config form | JSON (full or diff) |
| Dataset curator | JSONL of approved rows |
| Annotator | Markdown with quoted excerpts + notes |
| Prompt tuner | The final prompt string |
| Color/animation picker | CSS rule or token assignment |

The button label should say what you'll get: "Copy as JSON", not "Export"
(too vague).

## Common mistakes

- **No export.** This is the most important bit; it's also the most
  commonly omitted. Without it, the editor is a toy.
- **Building a real product.** The point is throwaway. Resist generic
  abstractions; hardcode the user's specific case.
- **Over-validating.** This is a 1-user, 1-session tool. Skip the schema
  validation; let the user export whatever they want.
- **Persistence ambition.** Don't add localStorage save/load by default.
  If the user wants to come back, they can keep the tab open or copy
  their progress.
- **Mobile-first concern.** Most editing UIs are used on desktop in
  practice. Don't compromise the layout for phone screens.

## Worked example prompts

- > "I need to reprioritize these 30 Linear tickets. Make me an HTML file
  > with each ticket as a draggable card across Now / Next / Later / Cut
  > columns. Pre-sort them by your best guess. Add a 'copy as markdown'
  > button that exports the final ordering with a one-line rationale per
  > bucket."

- > "Here's our feature flag config. Build a form-based editor for it,
  > group flags by area, show dependencies between them, warn me if I
  > enable a flag whose prerequisite is off. Add a 'copy diff' button that
  > gives me just the changed keys."

- > "I'm tuning this system prompt. Make a side-by-side editor: editable
  > prompt on the left with the variable slots highlighted, three sample
  > inputs on the right that re-render the filled template live. Add a
  > character/token counter and a copy button."
