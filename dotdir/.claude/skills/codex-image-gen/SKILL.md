---
name: codex-image-gen
description: |
  Generate real raster images — icons, diagrams, cover art, hero banners, illustrations,
  UI mockups — via the Codex CLI's built-in image_gen tool (gpt-image-2), using the user's
  existing ChatGPT login. No API key, no extra deps. Reach for this whenever a deliverable
  would land harder with a custom image than with an emoji or a stock placeholder: an HTML
  report that needs a cover or section visuals, a Marp/PPTX deck that needs an eyecatch or a
  conceptual diagram, a README hero, an app icon, an OG image, an explainer illustration that
  makes an idea click for the reader. Trigger on "画像を生成", "画像を作って", "アイキャッチ",
  "カバー画像", "バナー", "アイコンを作って", "レポートに図/イラストを", "スライドに画像",
  "ドキュメントに図解を", "資料に画像を", "説明図を作って", "generate an image",
  "make an illustration", "cover image", "hero banner", "icon for", or whenever you're authoring
  a document, report, slide deck, README, design doc, tutorial, or any material and reach a point
  where a custom visual would communicate an idea more intuitively than words alone. Also use it
  to edit or restyle an existing image by passing it as a reference. Skip for diagrams you can hand-author in SVG/CSS (use html-report-generator's
  svg-and-diagrams), for charts/plots of real data (use a charting library so numbers stay
  accurate), and for sourcing existing stock photography.
---

# Codex Image Generation

This skill turns the **Codex CLI's image_gen tool (gpt-image-2)** into a one-command image
generator you can call from inside any task. The point is to make reports and slides
*communicate* — a cover that sets the tone, a conceptual illustration that makes an abstract
idea concrete, a clean icon set instead of mismatched emoji.

**Why Codex instead of an image API:** it rides the user's existing `codex login` (ChatGPT
subscription) — no API key to manage, no `pip install`, nothing to wire up. Before rendering,
gpt-image-2 reasons through composition and layout, so UI mockups and diagrams tend to need
fewer retries than a raw text-to-image call.

**Why a raster image at all — and not always:** raster shines for texture, lighting,
illustration, photographic feel, and "make this feel like a real product." It is the *wrong*
tool when the content is structured: a flowchart, an architecture diagram, or a chart of real
numbers is clearer, editable, and accurate as hand-authored SVG or a charting library. Generated
pixels can't be diffed, re-themed, or trusted to label data correctly. Choose deliberately — the
table below draws the line.

## When this skill helps most (and when not)

| You want… | Use |
|-----------|-----|
| Report cover / section eyecatch / hero banner | **this skill** |
| Conceptual or metaphorical illustration ("trust", "pipeline", "growth") | **this skill** |
| App icon, favicon, OG/social share image | **this skill** |
| UI mockup or product screenshot mood | **this skill** |
| Restyle / edit an existing image (new background, angle, palette) | **this skill** (pass `--ref`) |
| Flowchart, architecture, sequence, ER diagram | `html-report-generator` → `references/svg-and-diagrams.md` |
| Chart/plot of actual data | a charting library (numbers must stay exact) |
| An existing real-world photo | stock source / web search, not generation |

## Prerequisite check (once per environment)

```bash
codex login status   # expect: "Logged in using ChatGPT"
```

If it isn't logged in: `codex login` (opens a browser, signs in with the ChatGPT account).
If `codex` is missing: `brew install --cask codex`, then `codex login`.

## Fast path — the bundled wrapper

`scripts/gen_image.sh` encapsulates the correct flags, the `$imagegen` trigger, absolute-path
saving, non-interactive execution, and **output verification** (it fails loudly if no real PNG
landed, instead of reporting a phantom success). Prefer it over hand-typing `codex exec`.

```bash
SKILL_DIR=~/.claude/skills/codex-image-gen   # adjust if running from the repo

# Report cover — wide, text-free, calm
"$SKILL_DIR/scripts/gen_image.sh" --out assets/report-cover.png --size 1536x1024 \
  "落ち着いたコーポレートブルーの抽象幾何カバー。レイヤー感のある半透明シェイプ、広い余白、文字なし"

# Slide eyecatch from a reference image's tone
"$SKILL_DIR/scripts/gen_image.sh" --out slides/img/intro.png --ref brand/hero.png --quality high \
  "添付のブランドトーンに合わせた、データが流れる様子の抽象イラスト。16:9、左に余白"
```

Flags: `--out` (required), `--ref` (repeatable reference image), `--size WxH` hint,
`--quality low|medium|high` (default `low`), `--timeout` seconds. Run with `-h` for the full list.

**Cost-aware loop:** iterate composition at `--quality low` (cheapest), then re-render the
chosen prompt once at `--quality high`. Each image counts against the user's Codex usage limit —
a single low-quality image is roughly **30–60k agent tokens** (measured ~57k on a 1024² draft).
Don't silently fan out 10 variants; if a task implies many images, say so and confirm scope first.

## Manual invocation (when the wrapper doesn't fit)

The wrapper is just this, made safe. Use the raw form for one-offs or unusual sandbox needs:

```bash
codex exec --sandbox workspace-write --skip-git-repo-check \
  '$imagegen フラットデザインのターミナルアイコン、パステル配色、1024x1024。
   /absolute/path/to/icon.png に PNG で保存してください。' \
  < /dev/null
```

Three things the model needs every time, or it quietly does nothing useful:
1. **`$imagegen`** at the start — the trigger that activates the image_gen tool.
2. **Subject + style** — what to draw and how (palette, composition, mood, aspect ratio).
3. **An absolute save path** + "保存してください" — without it the model may describe an image
   instead of writing a file. `--sandbox workspace-write` is what permits the write.

Attach references with `-i /abs/ref1.png -i /abs/ref2.png` for editing or tone-matching.

## Writing prompts that communicate

The difference between a generic stock-looking image and one that *carries an idea* is in the
prompt. For report/slide-oriented recipes — palettes, aspect ratios, "text-free so you overlay
real type later", icon-set consistency, metaphor design, negative prompts — read
**`references/prompt-recipes.md`**. Pull from it whenever the image is a deliverable rather than
a throwaway.

## Wiring generated images into reports & slides

- **HTML reports** (`html-report-generator`): generate into the report's `assets/`, then
  reference with explicit `width`/`height` and `loading="lazy"` for below-the-fold art (keeps
  CLS at 0). A text-free cover lets you layer real HTML type on top — sharper than baked-in text.
- **Marp slides** (`marp-rector-slides`): save under the deck's `img/` and use `![bg]` or grid
  cells. Generate eyecatches **text-free** and add titles as Marp text so they stay editable and
  translatable. After placing images, `marp-layout-validator` catches overflow.
- **PPTX** (`marp-to-pptx`): the converted deck embeds the PNGs as editable picture elements.

Keep generated assets out of source control unless they're final deliverables — they're large
and regenerable.

## Troubleshooting

| Symptom | Cause → Fix |
|---------|-------------|
| Script exits "画像が保存されていません" | Model didn't write the file. Re-run; make the save path explicit. Already handled by the wrapper's verification. |
| `codex exec` hangs | Missing `< /dev/null` (waiting on stdin) — the wrapper always adds it. |
| Text inside the image is garbled | gpt-image-2 renders text imperfectly. Generate text-free and overlay real type in HTML/Marp. |
| "not logged in" / auth error | `codex login`; verify with `codex login status`. |
| Hit usage limits | Each image spends Codex tokens. Iterate at `--quality low`, finalize once at `high`. |
| Write blocked by sandbox | Output path outside the writable root. The wrapper `cd`s into the output dir to avoid this; for manual runs keep `--out` under cwd. |

## References

- `references/prompt-recipes.md` — prompt patterns for report covers, slide eyecatches, icon
  sets, conceptual illustrations, and reference-image editing; palettes, aspect ratios, and
  negative-prompt guidance.
