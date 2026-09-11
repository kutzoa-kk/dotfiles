---
name: marp-rector-slides
description: Marpでレクタースライドスタイルガイドに基づいた美しいスライドを作成・整形する。frontmatter埋め込みCSSでグリッドレイアウトと視覚的一貫性を実現。使用タイミング：(1) Marpスライド新規作成、(2) 既存スライドのレイアウト整形、(3) プレゼン資料のデザイン改善、(4) スライドの視覚的品質向上。 Do NOT trigger for: PowerPoint（.pptx）を直接作る依頼、MCLabの書式・膝OA計画と同じ書式の指定（それは mclab-slide-design）。
---

# Marp Rector Slides

レクタースライドスタイルガイドに基づくMarpスライド作成スキル。

## Design Philosophy

**「人間がデザインし、AIが実行する」** — スライドをAIに丸投げするのではなく、構造化されたガイドラインに従って一貫性のあるスライドを生成。

## Quick Start

### CSS Setup — frontmatter `style:` に埋め込み

> **⚠️ 重要: Tailwind CDN (`<script>`) は使用禁止**
>
> Marpは `html: true` でも **`<script>` タグをストリップする**。
> Tailwind CDN を `<script>` で読み込んでも、Marpプレビュー（VS Code拡張、`marp -p`）では
> **全CSSクラスが無効になる**。HTMLビルド時にNode.jsで注入しても `.md` 直接表示では動かない。
>
> **解決策**: frontmatter の `style:` プロパティにCSSを直接定義する。

frontmatter に以下の `style:` ブロックを配置：

```yaml
---
marp: true
theme: default
paginate: true
style: |
  /* === Colors === */
  .text-navy { color: #1B4565; }
  .text-teal { color: #3E9BA4; }
  .text-text-secondary { color: #4A4A4A; }
  .text-text-muted { color: #6B6B6B; }
  .text-red { color: #E53E3E; }
  .text-green { color: #38A169; }
  .text-amber { color: #D69E2E; }
  .text-white { color: #fff; }
  .bg-bg-secondary { background-color: #F5F5F5; }
  .bg-teal { background-color: #3E9BA4; }
  .bg-navy { background-color: #1B4565; }
  .bg-red.bg-opacity-5 { background-color: rgba(229,62,62,0.05); }
  .bg-amber.bg-opacity-5 { background-color: rgba(214,158,46,0.05); }
  .bg-teal.bg-opacity-10 { background-color: rgba(62,155,164,0.1); }
  .bg-teal.bg-opacity-20 { background-color: rgba(62,155,164,0.2); }
  /* === Typography === */
  .text-em-3xl { font-size: 3em; line-height: 1.1; }
  .text-em-2xl { font-size: 2em; line-height: 1.2; }
  .text-em-xl { font-size: 1.5em; line-height: 1.3; }
  .text-em-lg { font-size: 1.25em; line-height: 1.5; }
  .text-em-base { font-size: 1em; line-height: 1.6; }
  .text-em-sm { font-size: 0.85em; line-height: 1.4; }
  .font-bold { font-weight: 700; }
  .text-center { text-align: center; }
  .text-left { text-align: left; }
  .leading-relaxed { line-height: 1.625; }
  /* === Layout: Flex === */
  .flex { display: flex; }
  .flex-col { flex-direction: column; }
  .items-center { align-items: center; }
  .items-start { align-items: flex-start; }
  .justify-center { justify-content: center; }
  .justify-between { justify-content: space-between; }
  /* === Layout: Grid === */
  .grid { display: grid; }
  .grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
  .col-span-2 { grid-column: span 2 / span 2; }
  .gap-2 { gap: 0.5rem; } .gap-3 { gap: 0.75rem; }
  .gap-4 { gap: 1rem; } .gap-6 { gap: 1.5rem; } .gap-8 { gap: 2rem; }
  /* === Sizing === */
  .w-full { width: 100%; } .w-56 { width: 14rem; }
  .h-full { height: 100%; } .h-4\/5 { height: 80%; }
  .block { display: block; }
  /* === Spacing === */
  .p-2 { padding: 0.5rem; } .p-3 { padding: 0.75rem; }
  .p-4 { padding: 1rem; } .p-6 { padding: 1.5rem; } .p-8 { padding: 2rem; }
  .pl-8 { padding-left: 2rem; }
  .py-0 { padding-top: 0; padding-bottom: 0; }
  .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
  .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
  .mb-0 { margin-bottom: 0; } .mb-1 { margin-bottom: 0.25rem; }
  .mb-2 { margin-bottom: 0.5rem; } .mb-4 { margin-bottom: 1rem; }
  .mb-6 { margin-bottom: 1.5rem; } .mb-8 { margin-bottom: 2rem; }
  .mt-0 { margin-top: 0; } .mt-1 { margin-top: 0.25rem; }
  .mt-2 { margin-top: 0.5rem; } .mt-4 { margin-top: 1rem; }
  .mt-8 { margin-top: 2rem; }
  .mr-2 { margin-right: 0.5rem; } .mr-3 { margin-right: 0.75rem; }
  .mr-4 { margin-right: 1rem; }
  .space-y-1 > * + * { margin-top: 0.25rem; }
  .space-y-2 > * + * { margin-top: 0.5rem; }
  .space-y-3 > * + * { margin-top: 0.75rem; }
  .space-y-4 > * + * { margin-top: 1rem; }
  /* === Border === */
  .border-l-4 { border-left: 4px solid; }
  .border-b { border-bottom: 1px solid #e5e7eb; }
  .border-b-2 { border-bottom: 2px solid; }
  .border-2 { border-width: 2px; border-style: solid; }
  .border-navy { border-color: #1B4565; }
  .border-teal { border-color: #3E9BA4; }
  .rounded { border-radius: 0.25rem; }
  .rounded-lg { border-radius: 0.5rem; }
  .rounded-full { border-radius: 9999px; }
  /* === Table fix: Marp sets display:block on all table elements === */
  section table { display: table !important; width: 100% !important; table-layout: auto; border-collapse: collapse; }
  section table thead { display: table-header-group !important; }
  section table tbody { display: table-row-group !important; }
  section table tr { display: table-row !important; }
  section table th, section table td { display: table-cell !important; }
---
```

### Build Command

HTMLタグを有効にするため `--html` オプションを使用：

```bash
# HTML出力
marp --html slide.md -o slide.html

# PDF出力
marp --html slide.md -o slide.pdf

# プレビュー
marp --html -p slide.md
```

**marp CLIが使えない場合（Node.js v25+等）**、marp-core APIを使用：

```javascript
const { Marp } = require('@marp-team/marp-core');
const fs = require('fs');
const marp = new Marp({ html: true });
const md = fs.readFileSync('slide.md', 'utf8');
const { html, css } = marp.render(md);
const fullHtml = `<!DOCTYPE html><html><head>
<meta charset='utf-8'><style>${css}</style>
</head><body>${html}</body></html>`;
fs.writeFileSync('slide.html', fullHtml);
```

## Known Pitfalls

| 問題 | 原因 | 対策 |
|------|------|------|
| CSSクラスが効かない | `<script>`タグがMarpにストリップされた | frontmatter `style:` にCSS埋め込み（**絶対に`<script>`を使わない**） |
| テーブルが半分の幅になる | Marpがtable要素に`display:block`を設定 | `section table { display: table !important; }` 等のCSS上書き |
| `overflow: hidden`で切れが検出できない | Marpのsectionに`overflow:hidden`が設定されている | scrollHeightでなくgetBoundingClientRect()で検証 |
| Marpプレビューで崩れるがHTMLは正常 | HTMLビルド時のみCDN注入していた | 必ず `.md` 直接プレビューで確認 |

## Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Navy | `#1B4565` | 見出し、強調、CTA |
| Teal | `#3E9BA4` | アクセント、アイコン、ボーダー |
| bg-secondary | `#F5F5F5` | カード背景 |
| text-secondary | `#4A4A4A` | 本文 |
| text-muted | `#6B6B6B` | キャプション |

**ルール**: 1スライドにアクセントカラーは最大2色。

## Typography

| Class | Size | Use |
|-------|------|-----|
| `text-em-3xl` | 3em | Hero、統計数字 |
| `text-em-2xl` | 2em | スライドタイトル |
| `text-em-xl` | 1.5em | セクション見出し |
| `text-em-lg` | 1.25em | 本文 |
| `text-em-base` | 1em | キャプション |
| `text-em-sm` | 0.85em | 注釈、脚注 |

## Layout Patterns

40パターンを7カテゴリに分類。詳細は [references/layouts.md](references/layouts.md) 参照。

| Category | Count | Use |
|----------|-------|-----|
| Title | 5 | Opening, section breaks |
| Single Column | 7 | Text-heavy, quotes |
| Two Column | 10 | Comparison, image+text |
| Three Column | 6 | Features, benefits |
| Grid | 6 | Gallery, matrix |
| Chart | 4 | Data visualization |
| Closing | 2 | CTA, thank you |

## Key Rules

1. **1スライド1メッセージ** — 情報過多を避ける
2. **アクセントカラーは最大2色** — Navy + Tealの組み合わせ推奨
3. **グリッドレイアウト活用** — `grid-cols-{n}` で一貫した配置
4. **余白を恐れない** — 詰め込みより空白
5. **`--html`必須** — HTMLタグを有効にするため
6. **`<script>`タグ禁止** — Marpがストリップするため、frontmatter `style:` を使う
7. **テーブルにはCSS上書き必須** — `display: table !important` をstyleに含める

## CSSクラス追加方法

新しいユーティリティクラスが必要な場合は、frontmatter の `style:` ブロックに追加する。
Tailwind のクラス名規則に合わせるが、**実装はプレーンCSS**。

```yaml
style: |
  /* 既存のクラス... */
  /* 新しいクラスを末尾に追加 */
  .new-class { property: value; }
```

## 画像・アイキャッチ生成

スライドにカバー画像・アイキャッチ・概念イラストが欲しいときは **`codex-image-gen`** スキルで生成する（Codex CLI 経由、API キー不要）。

- **テキストは画像に焼かない** — タイトルは Marp テキストで重ねる。翻訳・編集が効き、文字化けも避けられる。
- 16:9 背景は `--size 1536x864` で生成し、`![bg]` または grid セルに配置。
- アイコンは同一スタイル文で揃える。生成後は `marp-layout-validator` で文字はみ出しを検証。

## Resources

- **[references/layouts.md](references/layouts.md)** — 40レイアウトパターン詳細
- **[assets/templates/basic.md](assets/templates/basic.md)** — コピー可能なスライドテンプレート
