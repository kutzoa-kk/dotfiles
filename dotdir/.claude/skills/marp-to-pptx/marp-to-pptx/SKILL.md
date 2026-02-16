---
name: marp-to-pptx
description: "Marp Rector スライド（.md）を編集可能な PPTX ファイルに変換する。レクタースタイルのカラーパレット（Navy/Teal）とレイアウトを維持しつつ、テキスト・画像・グリッドレイアウトを編集可能な PowerPoint 要素に変換。使用タイミング：(1) Marp スライドを PPTX に変換したい時、(2)「PPTX に変換して」「PowerPoint にして」、(3) スライドを PowerPoint で編集可能にしたい時。"
---

# Marp to PPTX Converter

Marp Rector スライドを編集可能な PPTX に変換する。PptxGenJS で各スライドのテキスト・画像・レイアウトを再構築。

## Quick Start

```bash
# 依存パッケージをインストール（初回のみ）
npm install pptxgenjs cheerio

# 変換実行
node scripts/convert.js slide.md output.pptx
```

## Conversion Workflow

1. **入力ファイル確認** — Marp markdown (.md) の存在確認
2. **依存パッケージ確認** — `pptxgenjs`, `cheerio` がインストール済みか確認
3. **変換スクリプト実行** — `node scripts/convert.js <input.md> [output.pptx]`
4. **出力確認** — PPTX ファイルが生成されたことを確認
5. **微調整（必要に応じて）** — 複雑なレイアウトは手動で PptxGenJS コードを書いて補正

## Supported Layouts

自動検出される 14 のレクターレイアウトパターン:

| Layout | 検出パターン |
|---|---|
| hero-title | 中央配置 + `text-em-3xl` |
| title-bg | Navy 背景オーバーレイ |
| split-title | 2カラム + Navy 背景 |
| section-break | Teal 左ボーダー (`border-l-4`) |
| chapter-title | 下部配置のチャプター番号 |
| text-only | テキストのみのスライド |
| bullet-list | Teal 箇条書き |
| quote | `<blockquote>` |
| big-number | 大きな統計数値 |
| two-column | 2カラムグリッド |
| three-column | 3カラムグリッド |
| feature-cards | カード付き3カラム |
| grid-2x2 | 2x2 グリッド |
| closing | Thank You / 締めスライド |

## Manual Adjustment

convert.js で対応しきれない複雑なレイアウト（チャート、タイムライン、画像ギャラリー等）は、手動で PptxGenJS コードを記述。

詳細は [references/layout-mapping.md](references/layout-mapping.md) を参照:
- カラーパレット対応表
- タイポグラフィスケール
- PPTX 要素の座標・サイズ一覧
- 手動変換パターン（比較、タイムライン等）
- PptxGenJS の重要ルール（hex フォーマット、bullet 等）

## Rector Color Palette

変換で使用するカラー:

| 用途 | Hex | PptxGenJS |
|---|---|---|
| 見出し | Navy | `"1B4565"` |
| アクセント | Teal | `"3E9BA4"` |
| カード背景 | Light Gray | `"F5F5F5"` |
| 本文 | Dark Gray | `"4A4A4A"` |
| キャプション | Muted | `"6B6B6B"` |

## Troubleshooting

- **依存エラー**: `npm install pptxgenjs cheerio` を実行
- **レイアウト誤検出**: HTML コメント (`<!-- Section Break -->` 等) で明示的にヒントを記述
- **画像が含まれない**: 画像パスが Marp ファイルからの相対パスで存在するか確認
- **テキストが空**: Tailwind CSS のカスタムクラス名がレクター規約に沿っているか確認
