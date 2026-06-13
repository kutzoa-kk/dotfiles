# Prompt Recipes for Report & Slide Visuals

Read this when the image is a **deliverable** — something a human will look at and judge — not a
throwaway. The recipes below are starting points; adapt the palette, mood, and composition to the
actual product. The goal is always the same: an image that *carries the idea*, not generic
stock-looking filler.

## The five levers of a good prompt

Every prompt is stronger when it names these explicitly. gpt-image-2 plans composition before it
renders, so the more you decide up front, the fewer retries you spend.

1. **Subject** — the literal thing or scene ("a brass compass", "data flowing through a pipeline").
2. **Style** — flat / 3D / isometric / watercolor / photographic / line art / blueprint / risograph.
3. **Palette** — name 2–3 colors, ideally tied to the report or brand. Vague color = generic image.
4. **Composition & aspect** — where the subject sits, where the negative space is, the ratio.
5. **Mood / lighting** — calm, energetic, premium, technical, warm. This is what makes it *feel*
   intentional rather than templated.

Then add **constraints**: "text-free", "no logos", "flat single background for easy overlay".

## Aspect ratios by surface

| Surface | Ratio | Size hint (`--size`) |
|---------|-------|----------------------|
| HTML report cover (wide) | 3:2 | `1536x1024` |
| Slide background / eyecatch (16:9) | 16:9 | `1536x864` |
| App icon / favicon | 1:1 | `1024x1024` |
| OG / social share | 1.91:1 | `1200x630` |
| Portrait section divider | 2:3 | `1024x1536` |

gpt-image-2 flags resolutions above 2560×1440 as experimental; for crisp large art, generate at
~2K and upscale externally if needed.

## Generate text-free, overlay type later

The single most useful habit for reports and slides: **don't bake text into the image.**
gpt-image-2 renders lettering imperfectly (garbled glyphs, wrong kerning), and baked-in text can't
be edited, translated, or restyled. Instead generate a clean background or illustration with
deliberate empty space, then layer real HTML/Marp type on top. It's sharper, accessible to screen
readers, and trivially editable.

Add to the prompt: `テキストやロゴは入れないでください。タイトルを後で重ねるため左側に広い余白を残す。`

## Recipe: report cover

```
落ち着いた{コーポレートブルー}基調の抽象幾何カバー。
半透明のレイヤーが重なるミニマルな構成、わずかなグレイン。
広い余白、テキストなし、印刷品質。3:2。
```
Levers: subject = abstract geometry; style = minimal flat with grain; palette = corporate blue;
composition = layered with wide margin; mood = calm/premium. Swap the braced palette per project.

## Recipe: slide eyecatch (conceptual)

Make an abstract idea concrete with a metaphor instead of a literal scene.

```
「{信頼}」を表す抽象イラスト。{握手や鍵といった陳腐な記号は避け}、
連結する有機的な構造で表現。{ティールとサンド}の2色、フラットデザイン、16:9、
左に余白、テキストなし。
```
The "avoid the cliché symbol" clause matters — it pushes the model off the obvious stock metaphor
(handshake = trust, lightbulb = idea) toward something that looks considered.

## Recipe: consistent icon set

Consistency across an icon set comes from repeating the *style spec* verbatim and changing only the
subject. Generate them in one batch with an identical style sentence:

```
スタイル: フラット、2pxの均一ストローク、角丸、{ミント}基調の単色、背景透過、1024x1024。
このスタイルで「{設定}」を表すアイコン。
```
Then re-run with the same style sentence and a new subject (`「通知」`, `「同期」`, …). For tight
consistency, pass the first accepted icon as `--ref` on subsequent runs.

## Recipe: edit / restyle an existing image

Pass the source with `--ref` and describe only the *change*, not the whole image:

```
--ref input.png
"背景を清潔な白のスタジオ背景に差し替え。被写体・ライティング・アングルは維持。"
```
Good for: cleaning backgrounds, recoloring to a brand palette, generating a second angle of the
same object, or adapting one hero image into multiple section variants that still feel related.

## Negative prompting

State what to exclude when the default tends to drift there: `テキストなし`, `ロゴなし`,
`ウォーターマークなし`, `人物の手や指は描かない`, `過度なグラデーションやレンズフレアは避ける`,
`ストックフォト調にしない`. Keep it short — a couple of targeted exclusions beat a long list.

## Cost discipline

Composition is decided at low quality just as well as high. Iterate the prompt at
`--quality low`, and only once the layout is right re-render the final at `--quality high`. One
low-quality image is ~30–60k Codex tokens (measured ~57k on a 1024² draft); a careless 10-variant
sweep is ~half a million. If a task genuinely needs many images, surface the count and confirm
before spending.
