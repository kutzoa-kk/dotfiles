# 質問送信と回答取得

1 つのチャット画面で、質問を送り、ストリーミング完了を検知し、最終回答テキストを抽出する。

## 0. モード選択（既定で GPT-5.6 を選択）

送信前に必ず実行する。**既定モデルは `GPT-5.6`**——ユーザーがモードを明示（例「Pro拡張で」「最高で」「標準で」）した場合はその指定を、無ければ `GPT-5.6` を `want` として選択する。現在モードが既に `want` なら選択操作はスキップされる（下の選択スニペットが早期 return）。既定モデルは選択スニペット冒頭の `DEFAULT_MODE` 1箇所で管理し、新モデルへ移行するときはそこだけ変更する。

モードセレクタは上部バーの `button[aria-haspopup="menu"]` で、ボタンの innerText が現在のモード（例 `最高`）。**Radix メニューはプログラム的 `.click()` では開かない**——`pointerdown`→`pointerup`→`click` を dispatch する（ライブ検証で確認）。

現在モードの確認＋選択肢の列挙（ラベルはドリフトしうるので実行時に確認）:

```js
async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const btn = [...document.querySelectorAll('button')]
    .find(b => b.getAttribute('aria-haspopup') === 'menu' &&
               /^(最速|標準|高|最高|Pro|GPT|Auto|Thinking|Sol|Luna|Terra)/i.test((b.innerText||'').trim()));
  if (!btn) return { ok:false, reason:'mode selector not found' };
  const current = (btn.innerText||'').trim();
  const o = { bubbles:true, cancelable:true, view:window, pointerId:1, pointerType:'mouse', button:0 };
  btn.dispatchEvent(new PointerEvent('pointerdown', o));
  btn.dispatchEvent(new PointerEvent('pointerup', o));
  btn.dispatchEvent(new MouseEvent('click', o));
  await sleep(700);
  const options = [...document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]')]
    .map(e => (e.innerText||'').trim()).filter(Boolean);
  document.dispatchEvent(new KeyboardEvent('keydown', { key:'Escape', bubbles:true }));
  return { ok:true, current, options };
}
```

目的モードを選択（`want` は関数本体に文字列リテラルで埋め込む。args では渡さない）:

```js
async () => {
  const DEFAULT_MODE = "GPT-5.6";  // 既定モデル。新モデルへ移行するときはこの1行だけ変更する
  // ユーザーが別モードを明示した場合のみ、その文字列に差し替える（例: "Pro 拡張" / "最高" / "標準"）
  const want = DEFAULT_MODE;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s||'').replace(/\s/g,'');
  const btn = [...document.querySelectorAll('button')]
    .find(b => b.getAttribute('aria-haspopup') === 'menu' &&
               /^(最速|標準|高|最高|Pro|GPT|Auto|Thinking|Sol|Luna|Terra)/i.test((b.innerText||'').trim()));
  if (!btn) return { ok:false, reason:'mode selector not found' };
  if (norm(btn.innerText) === norm(want)) return { ok:true, already:true, mode: (btn.innerText||'').trim() };
  const o = { bubbles:true, cancelable:true, view:window, pointerId:1, pointerType:'mouse', button:0 };
  btn.dispatchEvent(new PointerEvent('pointerdown', o));
  btn.dispatchEvent(new PointerEvent('pointerup', o));
  btn.dispatchEvent(new MouseEvent('click', o));
  await sleep(700);
  const item = [...document.querySelectorAll('[role="menuitem"],[role="menuitemradio"]')]
    .find(e => norm(e.innerText) === norm(want));
  if (!item) {
    document.dispatchEvent(new KeyboardEvent('keydown', { key:'Escape', bubbles:true }));
    return { ok:false, reason:'mode not in menu', want };
  }
  item.dispatchEvent(new PointerEvent('pointerdown', o));
  item.dispatchEvent(new PointerEvent('pointerup', o));
  item.dispatchEvent(new MouseEvent('click', o));
  await sleep(500);
  return { ok:true, selected: (btn.innerText||'').trim() };
}
```

選択後はセレクタボタンの innerText が `want` に変わったか確認。変わらなければ **fail-loud**（推測で送信しない）。既定の `GPT-5.6` がメニューに見つからない場合（モデル選択が推論強度とは別 UI の可能性）も、選択せず fail-loud でユーザーに報告する。

観測済みモード（2026-07-15 時点、ドリフトしうるので上の列挙で実行時確認）: `最速` / `標準` / `高` / `最高` / `Pro 拡張` / `GPT-5.6`（既定） / `Sol` / `Luna` / `Terra`。
- **GPT-5.6**（既定モデル。選択スニペットの `DEFAULT_MODE` で一元管理）: 旧 `GPT-5.5` は廃止。表示ラベルの正確な表記は実機の実行時列挙で確認し、メニューに無ければ選択せず fail-loud で報告する（モデル選択が推論強度とは別 UI の可能性があるため）。
- ユーザーの「Pro拡張」= メニュー表記「**Pro 拡張**」。**最重量で応答が数分**かかるため、§3 の完了検知タイムアウトを **600s 以上**に上げること。
- **Sol / Luna / Terra**（ChatGPT Pro に新規追加）: 表示ラベルがそのままメニュー表記。推論の重さは未確定なので、必ず上の列挙で実在を確認したうえで選択し、応答が数分に及ぶ場合は Pro 拡張と同様に §3 のタイムアウトを **600s 以上**へ延長する。

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
  if (document.querySelector('button[data-testid="stop-button"]')) return true; // 生成中（停止ボタンあり）
  const turns = document.querySelectorAll('[data-message-author-role="assistant"]');
  if (turns.length === 0) return true;  // まだ assistant ターンが無い → 未完了扱い
  // 完了サイン: ターンアクション（コピー等）の出現をページ全体で確認する。
  // 注意: 現行 chatgpt.com では assistant ターンは <article> で包まれず（closest('article')=null）、
  //       copy ボタンは role 要素の外側にあるため、article/role スコープ検索では見つからない（ライブ検証で確認）。
  const done = document.querySelector(
    'button[data-testid="copy-turn-action-button"], button[data-testid="good-response-turn-action-button"]'
  );
  return !done;  // finished-action がまだ無ければ生成中
}
```

ポーリング手順（Claude 側）:

1. **内部ポーリング型の `evaluate_script` を 1 回呼ぶ**：関数内で ~400ms 間隔に上記判定を回し、`false`（=完了）を **2 連続**で得たら `{done:true, answer:...}` を返す。1 回の内部ループは **~20s 以内**に収める（`evaluate_script` 自体のタイムアウト回避）。
2. `done:false` が返ったら生成継続中。**Claude 側で同じ呼び出しを繰り返す**。
3. **総タイムアウト（モード依存）**:
   - 通常／高速モード: ~180s。
   - **Pro拡張・最高など重い推論モード**: 応答が数分に及ぶため **600s 以上**に延ばす（モードに応じて調整。重いほど内部ループ間隔も数秒に広げてツール呼び出しを節約）。
   - 超過したら「生成が完了しない」と報告（勝手に再送しない）。
4. 2 連続デバウンスはトークン間の隙間での誤検知防止。MCP `wait_for` は本文の語が事前に不明なため補助に留める。

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
