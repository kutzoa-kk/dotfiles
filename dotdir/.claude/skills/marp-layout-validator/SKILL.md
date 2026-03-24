---
name: marp-layout-validator
description: Marpスライドの視覚的品質検証をPlaywrightで自動化。文字はみ出し、レイアウト崩れ、要素のオーバーフローを検出。使用タイミング：(1) Marpスライド作成後のレイアウト確認、(2) 「スライドを確認して」「レイアウトチェック」、(3) 特定スライド範囲の検証（例：スライド15-25を確認）、(4) プレゼン前の品質チェック。
---

# Marp Layout Validator

Playwrightを使用してMarpスライドをブラウザでレンダリングし、視覚的な問題を検出するスキル。

## Workflow

### Step 1: HTMLを生成

```bash
marp --html slides.md -o slides.html
```

**注意**: `--html`オプションはHTMLタグを有効にするために必須。

**marp CLIが使えない場合（Node.js v25+等）**、marp-core APIを使用：

```javascript
const { Marp } = require('@marp-team/marp-core');
const fs = require('fs');
const marp = new Marp({ html: true });
const md = fs.readFileSync('slides.md', 'utf8');
const { html, css } = marp.render(md);
const fullHtml = `<!DOCTYPE html><html><head>
<meta charset='utf-8'><style>${css}</style>
</head><body>${html}</body></html>`;
fs.writeFileSync('slides.html', fullHtml);
```

### Step 2: HTTPサーバーを起動

Playwright MCPは`file://`プロトコルをブロックするため、HTTPサーバー経由でアクセスする。

```bash
python3 -m http.server 8888 &
```

### Step 3: Playwrightでページを開く

```
browser_navigate → http://localhost:8888/slides.html
```

ページ読み込み後、スナップショットでスライド総数を確認（「Page X of Y」表示）。

### Step 4: 各スライドをスクリーンショット撮影・検証

各スライドの `<img>` 要素をrefで直接指定して `browser_take_screenshot` で撮影。
（`ArrowRight`/`ArrowLeft`でのスライド移動は不要 — 全スライドが1ページに並んでいる）

各スライドで:
1. `browser_take_screenshot` でスクリーンショット撮影（`.playwright-mcp/`に保存される）
2. 撮影した画像を視覚的に確認
3. 問題を検出（テキストはみ出し、レイアウト崩れ等）

### Step 5: クリーンアップと報告

```bash
# ブラウザを閉じる
browser_close

# HTTPサーバーを停止
pkill -f "python3 -m http.server"

# 生成したHTMLを削除（任意）
rm slides.html
```

検出した問題を一覧で報告し、修正提案を行う。

## ⚠️ Marp固有の落とし穴

### 1. `<script>`タグは使えない

Marpは `html: true` でも **`<script>` タグをストリップする**。
Tailwind CDN等の`<script>`ベースのCSSフレームワークは動作しない。

**対策**: frontmatter `style:` プロパティにCSSを直接定義する。

### 2. テーブルが半分の幅になる

Marpは `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` に
全て `display: block` を設定する。これにより：
- テーブルが `width: 100%` でも内部要素が50%程度の幅にしかならない
- 列の配置が崩れる

**対策**: frontmatter `style:` に以下を追加：

```css
section table { display: table !important; width: 100% !important; table-layout: auto; border-collapse: collapse; }
section table thead { display: table-header-group !important; }
section table tbody { display: table-row-group !important; }
section table tr { display: table-row !important; }
section table th, section table td { display: table-cell !important; }
```

### 3. overflow検出が困難

Marpは `<section>` に `overflow: hidden` を設定している。そのため：
- `scrollHeight > clientHeight` は常に `false`（切れていても検出不可）
- はみ出したコンテンツは単に見えなくなる

**対策**: `getBoundingClientRect()` で子要素の位置をsectionの境界と比較する：

```javascript
// Playwright evaluate で使用
const sections = document.querySelectorAll('section');
sections.forEach((sec, i) => {
  const secRect = sec.getBoundingClientRect();
  const children = sec.querySelectorAll('*');
  children.forEach(child => {
    const childRect = child.getBoundingClientRect();
    if (childRect.bottom > secRect.bottom) {
      console.log(`P${i+1}: overflow by ${childRect.bottom - secRect.bottom}px`);
    }
  });
});
```

### 4. Marpプレビュー vs HTMLビルドの差異

ビルドHTMLでは正常でも、Marpプレビュー（VS Code拡張、`marp -p`）で崩れることがある。
原因：HTMLビルド時のみ注入されるCSS（CDN等）が、プレビューでは読み込まれない。

**対策**: 必ず `.md` ファイルをMarpプレビューで直接確認する。CSSは全てfrontmatter `style:` に含める。

## 検証項目

| 問題 | 視覚的特徴 | 修正方法 |
|------|-----------|---------|
| テキストはみ出し | 文字が折り返されて孤立文字が発生、端で切れる | フォントサイズ縮小、テキスト短縮 |
| 要素オーバーフロー | カード/ボックスがスライド境界を超える | padding/margin削減、グリッド調整 |
| 縦方向の詰め込み | 項目が重なる、余白がない | 2カラム化、項目数削減 |
| 横方向の崩れ | カラムが重なる、不均等な幅 | col-span調整、カラム数削減 |
| 余白不足 | 端までびっしり、窮屈な印象 | padding追加、コンテンツ削減 |
| テーブル幅不足 | テーブルがスライドの半分程度の幅 | `display: table !important` CSS追加 |
| CSSクラス無効 | 色・レイアウトが全く効かない | `<script>`→frontmatter `style:` に移行 |

## Quick Reference

```bash
# 1. HTML生成
marp --html slides.md -o slides.html

# 2. サーバー起動
python3 -m http.server 8888 &

# 3. 検証後、サーバー停止
pkill -f "python3 -m http.server"
```

**Playwright MCP Tools**:
- `browser_navigate`: URL移動
- `browser_snapshot`: アクセシビリティスナップショット（構造確認）
- `browser_take_screenshot`: スクリーンショット撮影（`.playwright-mcp/`に保存）
- `browser_press_key`: キー入力（`ArrowRight`/`ArrowLeft`でスライド移動）
- `browser_close`: ブラウザ終了

## 修正パターン詳細

詳細な修正パターンは [references/fix-patterns.md](references/fix-patterns.md) 参照。
