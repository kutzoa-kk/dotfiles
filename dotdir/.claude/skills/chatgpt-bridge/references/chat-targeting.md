# チャット選択（新規 / 既存名）

質問先チャットを解決する。全セレクタは**実行時にプローブ**（count を確認）し、ヒットした方法をログする。難読化 testid は A/B で変わりうるため fallback を常備。

## 新規チャット

最も堅牢なのは**直接 URL 遷移**:

- MCP: `navigate_page` で `https://chatgpt.com/`（type: "url"）。新規の空チャットになる。

ボタン経由が必要なら（既にチャット画面にいて遷移を避けたい等）:

- 第一候補: `button[data-testid="create-new-chat-button"]`
- fallback: `button:has-text("New chat")` / `[data-testid="new-chat-button"]`

## 既存チャットを名前で選択

サイドバーのチャットを列挙し、タイトルで照合する。`evaluate_script` で実行:

```js
() => {
  return [...document.querySelectorAll('nav a[href^="/c/"]')].map(a => ({
    title: (a.getAttribute('title') || a.textContent || '').trim(),
    href:  a.getAttribute('href'),   // 例 "/c/abc123..."
  })).filter(c => c.title);
}
```

照合ロジック（Claude 側で実施）:

1. **完全一致**を優先（`title === wanted`）。
2. 無ければ**部分一致**（`title.includes(wanted)` / 正規化して比較）。
3. **無一致** → ユーザーに「該当チャットが無い。新規作成しますか？」と確認（勝手に新規化しない）。
4. **複数一致** → 候補（title + href）を提示してユーザーに選ばせる。

選択した chat への遷移（href が分かれば直接遷移が確実）:

```js
(href) => { location.assign(href); return location.pathname; }
```

（MCP では `evaluate_script` に href を args で渡すか、`navigate_page` で `https://chatgpt.com{href}` へ遷移。）

## 仮想化の注意

サイドバーは**仮想化**されており、画面外のチャットは DOM に存在しない。列挙で見つからない場合:

1. サイドバーのスクロールコンテナを `evaluate_script` でスクロール（`el.scrollTop = el.scrollHeight`）して再列挙、または
2. 検索 UI（あれば）でタイトル検索、または
3. 既知の href があれば `https://chatgpt.com/c/{id}` へ直接遷移。

見つからないまま放置せず、上記いずれかを試し、それでも無ければ「無一致」として扱う。
