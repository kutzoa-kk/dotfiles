# /understand スキル（自分用）の実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** fkubota/understand-mode を dotfiles に写し、分からなかった文を `confusions.json` に残して、メインの Claude が書き方の決まりへ戻せるようにする。

**Architecture:** 画面が付箋から記録を組み立て（新しい小さなファイル `confusions.js`）、`/api/return` で送る。サーバーは中身を検査して `<DIR>/confusions.json` に書く。`SKILL.md` の「終わった」の手順で、メインの Claude がそれを読んで `japanese-style-guide.md` に反映する。

**Tech Stack:** Node 18+ 標準モジュール（サーバー）、ビルドなしの素の JS（画面）、Python unittest（dotfiles の既存の試験の形）

**Spec:** `docs/superpowers/specs/2026-11-21-understand-skill-design.md`

## Global Constraints

- 土台は fkubota/understand-mode のコミット `89ebc91d3826676b6523d31092d90b9018907b69`。写す先は `dotdir/.claude/skills/understand/`。`dev/` は写さない。
- 依存を増やさない：サーバーは標準モジュールだけ、画面はビルドなし（参考のスキルの `CLAUDE.md`「守ること」）。
- 集める付箋の種類は `question`・`detail`・`term` の3つだけ。元の文が `グラフの値：` で始まる付箋は集めない。
- 回答の冒頭は500字まで。
- 画面の文言・指示文は日本語で、短く平易に。
- コミットはご本人の依頼があるまでしない（作業ツリーにこのセッション以前の未コミット変更が多いため、`git add` も対象ファイルだけにする）。

## Review Focus

1. 質問の付箋が1枚もないまま閉じた → `confusions.json` は `[]`。メインは「足すものはありません」で片付けまで進む。
2. 壊れた・巨大な記録が届いた（配列でない、種類が不明、文字列でない、極端に長い）→ サーバーは落ちず、不正な項目を捨て、長さを切り詰めて書く。
3. グラフの点から作った付箋 → 集めない。
4. コードの行を選んだ付箋 → `code: true` を付けて送り、メインがコードの読みにくさと文章の言い方を区別できるようにする。
5. 同じ指摘がすでに決まりにある → 行を増やさず既存の行を強める（`SKILL.md` の指示。コードの試験では確かめられないので、最後の手動確認で見る）。

---

### Task 1: 参考のスキルを写し、起動と返却の試験を作る

**Files:**
- Create: `dotdir/.claude/skills/understand/`（`skill/understand/` 以下をそのまま）
- Create: `dotdir/.claude/skills/understand/LICENSE`（参考リポジトリの `LICENSE`）
- Create: `dotdir/.claude/skills/understand/UPSTREAM.md`（取得元 URL・コミット・写した日・手を入れたファイルの一覧）
- Create: `.bin/tests/test_understand_skill.py`
- Modify: `Makefile`（`test-understand` を追加）、`.github/workflows/check.yml`（同じ手順を追加）

**Interfaces:**
- Produces: 試験の補助 `start_server(work_dir) -> (proc, port, token)`、`post(port, token, path, body) -> dict`。サーバーは `node server.js --dir <work_dir> --session test-session --cwd <work_dir> --port 0 --no-open` で起動し、`url.txt` から `port` と `?t=` の合言葉を読む。`post` は `Host: 127.0.0.1:<port>` と `X-Understand-Token` を付ける。

- [ ] **Step 1:** 作業用フォルダに参考リポジトリをコミット `89ebc91` で取得し、`skill/understand/` と `LICENSE` を写す。`UPSTREAM.md` を書く。
- [ ] **Step 2: 試験を書く** `test_return_writes_return_md`：`/api/return` に `{"text": "テスト"}` を送ると `{"ok": true}` が返り、`return.md` の中身が `テスト\n` になる。`test_rejects_wrong_token`：合言葉が違うと拒否される。
- [ ] **Step 3: 実行** `make test-understand` → 2件とも成功（写しただけなので最初から通る。土台が動くことの確認）
- [ ] **Step 4:** `Makefile` に `test-understand: @python3 -m unittest discover -s .bin/tests -p 'test_understand_skill.py' -v` を足し、CI に `make test-understand` の手順を足す。

### Task 2: 画面で記録を組み立てて送る

**Files:**
- Create: `dotdir/.claude/skills/understand/app/public/confusions.js`
- Modify: `dotdir/.claude/skills/understand/app/public/index.html`（`app.js` の直前で読み込む）
- Modify: `dotdir/.claude/skills/understand/app/public/app.js`（`finishWith` の `post('/api/return', ...)`）
- Test: `.bin/tests/test_understand_skill.py`

**Interfaces:**
- Produces: `collectConfusions(stickies: {[id]: Sticky}, order: string[]) -> Confusion[]`。ブラウザでは大域関数、Node では `module.exports`。
  `Confusion = { type: 'question'|'detail'|'term', anchor: string, question: string, answer: string, code: boolean, fromSticky: boolean }`
  - `anchor`：`anchorText`。空なら集めない
  - `question`：最初の `role: 'user'` の `text`（なければ空文字）
  - `answer`：最後の `role: 'assistant'` の `text` の先頭500字（なければ空文字）
  - `code`：`Boolean(st.code)`、`fromSticky`：`st.parent !== 'main'`
  - 並びは `order` の順

- [ ] **Step 1: 試験を書く**（Python から `node -e` で `confusions.js` を読み込み、JSON を受け取って確かめる）
  - `test_collect_keeps_only_three_types`：`question`・`diagram`・`memo` の3枚 → 1件だけ、`type == 'question'`
  - `test_collect_skips_graph_value`：`anchorText` が `グラフの値：x=1` → 0件
  - `test_collect_truncates_answer`：回答が600字 → `answer` が500字
  - `test_collect_marks_child_and_code`：`parent: 'st2'`・`code: true` → `fromSticky` と `code` が真
- [ ] **Step 2: 実行して失敗を確かめる** → `confusions.js` がないので失敗
- [ ] **Step 3:** `confusions.js` を書き、`index.html` で読み込み、`finishWith` で `{ text, confusions: collectConfusions(S.stickies, S.order) }` を送る。
- [ ] **Step 4: 実行** `make test-understand` → すべて成功

### Task 3: サーバーで検査して `confusions.json` に書く

**Files:**
- Modify: `dotdir/.claude/skills/understand/app/server.js`（`/api/return` の処理と、新しい関数 `sanitizeConfusions`）
- Test: `.bin/tests/test_understand_skill.py`

**Interfaces:**
- Consumes: Task 2 の `Confusion` の形
- Produces: `<DIR>/confusions.json`（`Confusion[]`、UTF-8、2字下げ）。`sanitizeConfusions(x: unknown) -> Confusion[]`：配列でなければ `[]`、最大200件、種類が3つ以外の項目は捨てる、文字列は `anchor` 2000字・`question` 1000字・`answer` 500字に切る、真偽値は `=== true` で判定

- [ ] **Step 1: 試験を書く**
  - `test_return_writes_confusions`：1件送る → `confusions.json` が同じ1件
  - `test_return_without_confusions_writes_empty`：`confusions` なし → `[]`
  - `test_return_sanitizes_bad_items`：`"confusions": "壊れた"` → `[]`。`[{type:'diagram'}, {type:'term', anchor: 'あ'*5000}]` → 1件、`anchor` は2000字
- [ ] **Step 2: 実行して失敗を確かめる** → `confusions.json` がないので失敗
- [ ] **Step 3:** `sanitizeConfusions` を書き、`/api/return` で `return.md` の直後に `confusions.json` を書く。
- [ ] **Step 4: 実行** `make test-understand` → すべて成功

### Task 4: `SKILL.md` に決まりへ戻す手順を足し、手動で通しを確かめる

**Files:**
- Modify: `dotdir/.claude/skills/understand/SKILL.md`（「3.『終わった』と言われたら」）
- Modify: `dotdir/.claude/skills/understand/UPSTREAM.md`（手を入れたファイルの一覧を最終版に）

- [ ] **Step 1:** 手順 2 と 3 の間に次を足す。
  - `<DIR>/confusions.json` を読む。空なら何も足さない。
  - 1件ずつ、「言い方が悪かった」（英語の裸書き・略語・結論が後ろ・前提の飛ばし・用語の説明不足など）か「中身が難しいだけ」かを仕分ける。`code: true` のものはコードそのものの難しさと区別する。`fromSticky: true` は分身の回答の文。
  - 言い方が悪かったものは、`~/.claude/japanese-style-guide.md` の「育て方」に従い、対応表に「❌ → ✅。理由（日付）」の1行を足す。同じ指摘の行があれば、その行を強めて日付を更新する。
  - 足した行・強めた行を本人に短く報告する。確認は挟まない。
- [ ] **Step 2: 通しの確認**：参考リポジトリの `dev/mock-claude.js` を作業用フォルダに置き、`UNDERSTAND_CLAUDE_BIN` でそれを使ってサーバーを起動する。ブラウザで「質問」の付箋を1枚作り、「理解を終える」→「メインに送って閉じる」を押し、`confusions.json` に1件入ることを確かめる。
- [ ] **Step 3: 本物での確認**（費用：分岐1回で約1ドル）：新しいセッションで `/understand` を開き、付箋を1枚作って閉じ、「終わった」の後に決まりへの反映か「足すものはありません」の報告が出ることを確かめる。ご本人に実行してもらうか、了承を得てから行う。
- [ ] **Step 4:** `git status` で、変更が計画したファイルだけであることを確かめ、差分をご本人に示してコミットの可否を聞く。
