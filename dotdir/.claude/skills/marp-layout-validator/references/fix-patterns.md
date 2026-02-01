# 修正パターン詳細

## テキストはみ出し

### 症状
- 文字がスライドの端で切れている
- 長い単語が折り返されず枠外に出る
- 日本語テキストが途中で切れる

### 修正方法

```html
<!-- Before: テキストが長すぎる -->
<div class="text-em-2xl">
  これは非常に長いテキストでスライドの端まで到達してはみ出します
</div>

<!-- After: フォントサイズを小さく -->
<div class="text-em-xl">
  これは非常に長いテキストでスライドの端まで到達してはみ出します
</div>

<!-- または改行を追加 -->
<div class="text-em-2xl">
  これは非常に長いテキストで<br>
  スライドの端まで到達してはみ出します
</div>
```

### フォントサイズ縮小の目安

| 元のサイズ | 縮小後 |
|-----------|--------|
| text-em-3xl | text-em-2xl |
| text-em-2xl | text-em-xl |
| text-em-xl | text-em-lg |
| text-em-lg | text-em-base |

---

## 要素オーバーフロー

### 症状
- カードやボックスがスライド境界を超える
- グリッドアイテムが重なる
- フッターやヘッダーが見切れる

### 修正方法

```html
<!-- Before: paddingが大きすぎる -->
<div class="grid grid-cols-3 gap-8 p-8">
  <div class="bg-bg-secondary p-6">...</div>
</div>

<!-- After: padding/gapを削減 -->
<div class="grid grid-cols-3 gap-4 p-4">
  <div class="bg-bg-secondary p-4">...</div>
</div>
```

### padding削減の目安

| 元の値 | 縮小後 |
|--------|--------|
| p-8 | p-4 or p-6 |
| p-6 | p-4 |
| gap-8 | gap-4 or gap-6 |
| gap-6 | gap-4 |

---

## 縦方向の詰め込み

### 症状
- 項目が縦に並びすぎて重なる
- リストアイテム間の余白がない
- スクロールが必要に見える（実際はできない）

### 修正方法

**パターン1: 2カラム化**

```html
<!-- Before: 5項目を縦に並べる -->
<ul>
  <li>項目1</li>
  <li>項目2</li>
  <li>項目3</li>
  <li>項目4</li>
  <li>項目5</li>
</ul>

<!-- After: 2カラムグリッド -->
<div class="grid grid-cols-2 gap-4">
  <div>
    <ul>
      <li>項目1</li>
      <li>項目2</li>
      <li>項目3</li>
    </ul>
  </div>
  <div>
    <ul>
      <li>項目4</li>
      <li>項目5</li>
    </ul>
  </div>
</div>
```

**パターン2: 項目数削減**

```html
<!-- Before: 情報過多 -->
<ul>
  <li>詳細な説明1</li>
  <li>詳細な説明2</li>
  <li>詳細な説明3</li>
  <li>詳細な説明4</li>
  <li>詳細な説明5</li>
</ul>

<!-- After: 重要な3項目に絞る -->
<ul>
  <li>重要ポイント1</li>
  <li>重要ポイント2</li>
  <li>重要ポイント3</li>
</ul>
```

### 目安
- 縦1カラム: 最大4-5項目
- 項目が5つ以上: 2カラム化を検討
- 項目が8つ以上: 3カラム化 or 複数スライドに分割

---

## 横方向の崩れ

### 症状
- カラムが重なる
- 不均等な幅
- 画像とテキストの配置ずれ

### 修正方法

```html
<!-- Before: 3カラムが狭すぎる -->
<div class="grid grid-cols-3 gap-4">
  <div>長いコンテンツ...</div>
  <div>長いコンテンツ...</div>
  <div>長いコンテンツ...</div>
</div>

<!-- After: 2カラムに変更 -->
<div class="grid grid-cols-2 gap-6">
  <div>長いコンテンツ...</div>
  <div>長いコンテンツ...</div>
</div>
```

### col-span調整

```html
<!-- 不均等な幅が必要な場合 -->
<div class="grid grid-cols-3 gap-4">
  <div class="col-span-2">メインコンテンツ（2/3幅）</div>
  <div>サイド（1/3幅）</div>
</div>
```

---

## 余白不足

### 症状
- コンテンツがスライド端ぎりぎり
- 窮屈な印象
- 要素間の区切りが不明瞭

### 修正方法

```html
<!-- Before: 余白なし -->
<div class="grid grid-cols-2">
  <div>コンテンツ</div>
  <div>コンテンツ</div>
</div>

<!-- After: 適切な余白 -->
<div class="grid grid-cols-2 gap-6 p-8">
  <div class="p-4">コンテンツ</div>
  <div class="p-4">コンテンツ</div>
</div>
```

### 余白の目安

| 要素 | 推奨padding |
|------|------------|
| スライド全体 | p-8 ~ p-12 |
| カード | p-4 ~ p-6 |
| グリッドgap | gap-4 ~ gap-6 |

---

## 複合パターン

複数の問題が同時に発生する場合、以下の優先順位で修正:

1. **構造変更**: カラム数の変更、レイアウト再設計
2. **サイズ調整**: フォントサイズ、padding/margin
3. **コンテンツ削減**: 項目数削減、テキスト簡略化
