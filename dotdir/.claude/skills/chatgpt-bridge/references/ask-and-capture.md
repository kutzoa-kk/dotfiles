# 質問送信と回答取得

1 つのチャット画面で、質問を送り、ストリーミング完了を検知し、最終回答テキストを抽出する。

## 1. 質問を入力

composer は `#prompt-textarea`（**contenteditable ProseMirror div**、textarea ではない）。`fill` は使わず**ネイティブ打鍵**で入力する:

- MCP: `take_snapshot` → `#prompt-textarea` の uid を得る → `click`（focus）→ `type_text`（text=質問文）。
- `type_text` は実キーイベントを発火するので ProseMirror が正しく反応し、`input` イベントで send ボタンが有効化される。

`evaluate_script` で直接入れる場合の代替（ネイティブ打鍵が使えないとき）:

```js
() => {
  const text = "<<質問文を文字列リテラルで埋め込む>>";
  const el = document.querySelector('#prompt-textarea');
  el.focus();
  document.execCommand('selectAll', false);
  document.execCommand('insertText', false, text);  // PM が期待する beforeinput/input を発火
  return el.innerText.length;
}
```

`evaluate_script` の `args` は snapshot の element uid 専用であり、質問文などのデータは args で渡さず関数本体に文字列リテラルとして埋め込む（Claude が呼び出し時に埋め込む）。

## 2. 送信

- 第一候補: `button[data-testid="send-button"]` を `click`（テキスト入力で有効化済みのはず）。
- fallback: composer で Enter（MCP `type_text` の submitKey="Enter"、または `press_key` "Enter"）。
- 送信前に send ボタンが**有効**か確認（disabled のままなら `input` 未発火 → 入力やり直し）。

## 3. 完了検知（二重シグナル + デバウンス）

単一シグナルは危険。**stop ボタン消失 AND finished-action 出現**の両方で判定する:

```js
() => {
  // 生成中は true、完了で false。false が2連続したら完了とみなす。
  if (document.querySelector('button[data-testid="stop-button"]')) return true; // 生成中
  const turns = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = turns[turns.length - 1];
  if (!last) return true;  // まだ assistant ターンが無い → 未完了扱い
  const root = last.closest('article') || last;
  const done = root.querySelector(
    'button[data-testid="copy-turn-action-button"], button[data-testid="good-response-turn-action-button"]'
  );
  return !done;  // finished-action がまだ無ければ生成中
}
```

ポーリング手順（Claude 側）:

1. 送信直後から ~300ms 間隔で上記 `evaluate_script` を呼ぶ。
2. `false`（=完了）を**2 連続**で得たら完了とみなす（トークン間の隙間で誤検知しないため）。
3. **タイムアウト上限**（例 180s）。超えたら「生成が完了しない」とユーザーに報告（勝手に再送しない）。
4. MCP `wait_for`（text 配列の出現待ち）は補助に使えるが、回答本文の語は事前に分からないので主判定は上記ポーリングにする。

## 4. 最終回答を抽出

```js
() => {
  const nodes = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = nodes[nodes.length - 1];
  if (!last) return null;
  const md = last.querySelector('.markdown') || last;  // .markdown = 整形済み本文
  return md.innerText.trim();
}
```

- `null` が返る/空文字 → セレクタ不一致を疑う。`take_snapshot` で assistant ターンの実構造を確認し、fallback（`article:last-of-type` の innerText から "ChatGPT said:" 接頭辞を除去）に切替。
- 切替時はどの fallback を使ったかをユーザーに報告（セレクタ drift の早期発見）。

## エラー処理

- **レート制限 / 利用上限**: 画面に上限メッセージが出たら抽出は中止し、ユーザーに報告（自動リトライ禁止）。
- **生成停止ボタンが消えない**: タイムアウトで打ち切り報告。
- **セレクタ全滅**: `stop-button` も `copy-turn-action-button` も assistant コンテナも見つからない → DOM 構造が変わった可能性。fail-loud（推測で進めない）。`take_snapshot` 結果を添えてユーザーに調査を促す。
