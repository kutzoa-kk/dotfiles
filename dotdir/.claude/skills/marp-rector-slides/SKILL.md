---
name: marp-rector-slides
description: Marpでレクタースライドスタイルガイドに基づいた美しいスライドを作成・整形する。Tailwind CSS CDNとカスタムテーマでグリッドレイアウトと視覚的一貫性を実現。使用タイミング：(1) Marpスライド新規作成、(2) 既存スライドのレイアウト整形、(3) プレゼン資料のデザイン改善、(4) スライドの視覚的品質向上。
---

# Marp Rector Slides

レクタースライドスタイルガイドに基づくMarpスライド作成スキル。

## Design Philosophy

**「人間がデザインし、AIが実行する」** — スライドをAIに丸投げするのではなく、構造化されたガイドラインに従って一貫性のあるスライドを生成。

## Quick Start

### Tailwind CDN Setup

最初のスライドに以下を配置：

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  theme: {
    extend: {
      colors: {
        navy: '#1B4565',
        teal: '#3E9BA4',
        'bg-secondary': '#F5F5F5',
        'text-secondary': '#4A4A4A',
        'text-muted': '#6B6B6B',
      },
      fontSize: {
        'em-3xl': ['3em', { lineHeight: '1.1' }],
        'em-2xl': ['2em', { lineHeight: '1.2' }],
        'em-xl': ['1.5em', { lineHeight: '1.3' }],
        'em-lg': ['1.25em', { lineHeight: '1.5' }],
        'em-base': ['1em', { lineHeight: '1.6' }],
      }
    }
  }
}
</script>
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
5. **`--html`必須** — Tailwind CDNを有効にするため

## Resources

- **[references/layouts.md](references/layouts.md)** — 40レイアウトパターン詳細
- **[assets/templates/basic.md](assets/templates/basic.md)** — コピー可能なスライドテンプレート
- **[assets/tailwind.css](assets/tailwind.css)** — オフライン用フォールバックCSS
