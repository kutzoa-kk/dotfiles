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

**注意**: `--html`オプションはTailwind CDN等のHTMLタグを有効にするために必須。

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

スライド移動: `browser_press_key` で `ArrowRight` / `ArrowLeft`

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

## 検証項目

| 問題 | 視覚的特徴 | 修正方法 |
|------|-----------|---------|
| テキストはみ出し | 文字が折り返されて孤立文字が発生、端で切れる | フォントサイズ縮小、テキスト短縮 |
| 要素オーバーフロー | カード/ボックスがスライド境界を超える | padding/margin削減、グリッド調整 |
| 縦方向の詰め込み | 項目が重なる、余白がない | 2カラム化、項目数削減 |
| 横方向の崩れ | カラムが重なる、不均等な幅 | col-span調整、カラム数削減 |
| 余白不足 | 端までびっしり、窮屈な印象 | padding追加、コンテンツ削減 |

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
