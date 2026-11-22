# 日本語の記事・推敲スキルの設計

- 日付：2026-11-22
- 状態：承認済み（2026-11-22）。次は承認後に実装時の試験と反証検証で変え、完了報告で示したうえで commit の依頼を受けたものである
  - natural-japanese の本文への追記1節
  - 記事の種類別の構成を gist でなく blog-writing-guide-ja から組むこと
  - 出典ファイル `SOURCES.md` の同梱
  - natural-japanese の `description` の除外を、note 原稿の改稿まで広げること
  - tech-article-writer の事実と確認事項の規則の追加
- commit 後の安全性の点検を受けた変更：natural-japanese の `semantic.py` と `newfacts.py` を修正した

## 目的

公開されている3つの日本語文章スキルを手元で使えるようにする。どれも単独で使え、`note-article-writer` からも呼び出せるようにする。

ユーザーの指定：

- blog-writing-guide-ja、tech-article-ja（gist）、natural-japanese を組み合わせて作る
- 作成後は `note-article-writer` からも呼び出す
- `note-article-writer` とは別でも使えるようにする

それ以外の線引き（名前、分け方、呼び出す条件、優先順位）は設計側の提案である。

## 作り方の候補

単独で使う指定があるため、`note-article-writer` への取り込みは採らない。記事用の規則と汎用の推敲は使う場面が違うため、2つのスキルに分ける。残る分岐は natural-japanese の入れ方である。

| 案 | 内容 | 得るもの | 失うもの |
|---|---|---|---|
| A（推奨） | 版を固定して写し、`description` と実行環境の注意だけ直す（`understand` と同じ方式） | 既存スキルとの取り合いを防げる。Codex・agy と同じ実体を使える | 更新は手作業。約390KB の他者のコードが公開リポジトリに入る |
| B | 上流の Claude Code プラグインとして入れる | 更新が楽 | `description` を直しても更新で消える。`critical-thinking` も入る。Codex には別に入れる |
| C | `npx skills add` で入れる（`using-bee` と同じ方式） | 更新コマンドがある | `description` を直しても更新で上書きされる |

## 構成

```text
単独で使う
  技術記事を書く・直す ──> tech-article-writer
  文書を読みやすく直す ──> natural-japanese

note の記事を書く
  note-article-writer
    ├─ 1. 技術記事なら、書く前に tech-article-writer の基準を読む
    ├─ 2. 本文を書く
    ├─ 3. natural-japanese のクイックで推敲する
    ├─ 4. patterns-ja.md と learned-rules.md で仕上げる
    └─ 5. 仕上げた版を下書きとして保存する
```

呼び出しは一方向とする。呼ばれた2つは `note-article-writer` を呼ばず、互いも呼ばない。

### tech-article-writer（新規）

```text
tech-article-writer/
├── SKILL.md              # 進め方、品質基準、呼ばれたときの振る舞い。200行以内
├── references/design.md  # 読者の疑問への素材の割り当て、種類別の厚みの配分
├── references/review.md  # 記事単位の点検、技術記事に特有の点検
├── LICENSE               # Apache-2.0
├── SOURCES.md            # 原典の帰属表示（原文のまま）
└── UPSTREAM.md           # 出どころ、コミット、変更点、MIT の著作権表示と許諾文
```

改変元のあるファイルには、改変した旨を冒頭近くに記す。

`description` の案：

> 日本語の技術記事の企画・構成・執筆と、記事全体のレビュー・改稿を行う。対象は Zenn、Qiita、個人ブログ、企業の技術ブログ。note-article-writer から技術記事の基準としても呼ばれる。トリガー：「技術記事を書いて」「技術ブログにして」「Zenn の記事」「Qiita の記事」「技術記事の構成を考えて」「技術記事をレビューして」。Do NOT trigger for: note の記事作成（note-article-writer。そこから呼ばれる場合を除く）、文単位の推敲だけ（natural-japanese）、AI 臭だけの除去（humanize-ja）・指摘（stop-ai-slop）、論文・README・メール・スライド。

- 単独で使うときは、構成だけ、執筆、レビューだけのどれにも応じる。執筆の依頼では本文まで書き、質問は最大2問とする
- gist からは「素材から答えを拾ってから書く」という観点だけを使う。型別の構成と質問は写さず、答えのない核心だけを尋ねる
- 体験、数値、失敗談は素材にあるものに限る
- です・ます体を基本とし、書き手の既存の文体があれば従う。調子を変えるための体言止めは足さない
- 検索流入向けの規則は、検索流入を狙うと言われたときだけ使う
- 呼ばれたときは基準だけを提供する。媒体、分量、締め、出力の型は呼ぶ側に従う
- AI 臭の一覧は持たない。文単位の仕上げは natural-japanese と既存の辞書に任せる
- 原典にある、手元にないスキル（`writing-ja`、`blog-ops`、`fact-check-ja`）への参照は持ち込まない

### natural-japanese（上流の複製）

- `coji/natural-japanese` の `skills/natural-japanese/` と、リポジトリ直下の `LICENSE` を写し、`UPSTREAM.md` を足す
- 変更は `SKILL.md` の `description` と実行環境の注意1節、および `semantic.py` と `newfacts.py` の安全上の修正とする。文末体を保ち、呼ばれたときは報告を足さない。RTK が検査結果を切り詰めるため `rtk proxy uv run` で実行し、`uv` が動かない隔離環境では手動の点検表を使う
- 作業領域で `description` を直してから `dotdir` へ移す。原本のまま置くと、その時点で他のセッションの「AI臭い」の依頼を横取りする
- 更新するときは、新しい版を作業領域に写し、`description`、追記した1節、安全上の修正を当て直し、差分を読んでから置き換える。この手順を `UPSTREAM.md` に書く
- `critical-thinking` は入れない。本文にある参照はそのまま残し、`UPSTREAM.md` に未導入と記す

`description` の案：

> 仕事の日本語文書や記事を、意味を変えずに読みやすく、わかりやすく推敲する。議事録、報告書、社内ガイド、企画書、技術記事など。note-article-writer の仕上げからも呼ばれる。トリガー：「読みやすくして」「わかりにくい」「何を言っているかわからない」「直訳っぽい」「文章を推敲して」「natural-japanese で」。Do NOT trigger for: AI 臭だけの除去・「自然な文章にして」（humanize-ja）、AI 臭の指摘・採点（stop-ai-slop。natural-japanese の score を明示された場合を除く）、Claude 応答の点検（japanese-output-review）、note の記事・原稿の作成と改稿（「note の原稿を読みやすくして」を含む。note-article-writer。そこから呼ばれる場合を除く）。

`disable-model-invocation: true` と `allow_implicit_invocation: false` は、どちらのスキルにも付けない。他スキルからの呼び出しを塞ぐおそれがあるためである。誤起動は `description` で防ぐ。

### note-article-writer（追記）

「書く前に」の次へ、次の節を足す。

> ## 他のスキルの使い方
>
> Claude Code では Skill ツールで呼びます。Codex など Skill ツールがない環境では、このスキルの隣にある同名フォルダの `SKILL.md` を読んで従います。
>
> - 技術記事（コード、開発手順、設計判断、ツールの検証が主題）は、書く前に `tech-article-writer` を呼びます。
> - 新しい記事と、読みやすさを含む改稿は、本文を書いた後に `natural-japanese` をクイックで呼びます。1か所だけの修正、育成、note への入力・投稿では呼びません。
> - 優先順位は、本人の今回の指示、`learned-rules.md`、この SKILL.md、呼んだスキルの順です。題材と範囲、事実の扱い、有料部分の目印、有料記事への案内、出力の型は変えさせません。
> - 推敲の作業記録と推敲前の写しは一時フォルダに置き、出力と下書きフォルダには入れません。
> - どちらかを使えなかったときは、記事は仕上げたうえで、使えなかったことを本文の外に1行で伝えます。

「書き方」の最後の項は、`natural-japanese` の後に `patterns-ja.md` と `learned-rules.md` で仕上げる順序に書き換える。育成用の下書きには仕上げた版を保存する。これにより、育成で比べる差分は本人の直しだけになる。

「出力の型」には、保存しても3節を全文そのまま応答に出すこと、3節の外に置ける行、育成の依頼の1行を書く（型崩れ対策。完了報告の後にユーザーが依頼）。

既存の未コミットの変更（`description` の書式、Codex 向けの投稿手順）は残す。

## 変更するファイルと影響範囲

| 対象 | 変更 | 影響 |
|---|---|---|
| `dotdir/.claude/skills/tech-article-writer/` | 新規 | `~/.claude/skills` に即反映 |
| `dotdir/.claude/skills/natural-japanese/` | 新規 | 同上 |
| `dotdir/.claude/skills/note-article-writer/SKILL.md` | 追記と1項の書き換え | 次の記事作成から反映 |
| `.gitignore` | 2スキルの追跡許可 | git のみ |
| `~/.agents/skills/` | 個別リンクを2本 | Codex と agy に反映 |

`humanize-ja`、`stop-ai-slop`、`japanese-output-review` は変更しない。`make link` は実行しない。commit は 2026-11-22 に依頼を受けて分割して行う。push は依頼されたときに行う。

## 出どころと利用条件

dotfiles は公開リポジトリのため、次のとおり扱う。

| 原典 | 固定するコミット | 条件 | 扱い |
|---|---|---|---|
| [blog-writing-guide-ja](https://github.com/j1nn0/skills/tree/main/skills/blog-writing-guide-ja) | `16ca3bcfa644c1eebf091a2ca0ef3ebfba8722e4` | Apache-2.0（一部は coji の MIT） | 改変して使う。Sentry と j1nn0 と coji の表示、ライセンス文、変更点を残す |
| [tech-article-ja](https://gist.github.com/sheepla/4509b70adffba5a315521d31a551cd8a) | `c1b0a7bc4cf4393113844a593168c06e927fdd74` | 表記が見当たらない | 文面、例文、一覧を写さない。観点だけを参考に独自に書き、リンクを記す |
| [natural-japanese](https://github.com/coji/natural-japanese) | `840bd400cbcb64c8b64d492a144da54fc05776c5` | MIT | 複製し、ライセンス文を残す |

## 費用と危険

- natural-japanese の本文は19,334文字ある。段落ごとの確認と検査結果を合わせ、note の記事1本あたり2〜3万トークン増える見込みである（文字数からの概算で、未計測）。重ければ「有料記事と頼まれたときだけ呼ぶ」に変える
- Claude Code では、スキルの本文から別のスキルを呼ぶ実例がある（superpowers）。Codex での動作は未確認のため、実際に動かして確かめる
- `sudachipy` がこの環境に入るかは未確認のため、検査スクリプトの動作確認を実装の最初に行う
- 検査スクリプトは初回に `uv` で辞書などを取得する。実行前に中身を点検する。約1GB を取得する実験的な `semantic.py` は実行しない

## 完了条件

- 2スキルの frontmatter が読め、`description` が1,536文字以内である（上限は公式文書の要約による）
- natural-japanese の複製と固定したコミットの差が、`description`、実行環境の注意1節、`semantic.py` と `newfacts.py` の安全上の修正、`LICENSE`、`UPSTREAM.md` だけである
- 検査スクリプト（`lint.py`、`calques.py`、`newfacts.py`）が、別の作業ディレクトリから動く
- tech-article-writer に gist の文面と一致する長い文字列がないことを機械で照合する
- Claude Code と Codex の一覧に2スキルが出る。`check_sharing.py` で共有済みになる
- 新しいセッションで、次の依頼が意図したスキルを選ぶ

  | 依頼 | 選ばれるスキル |
  |---|---|
  | 「このメモで技術記事を」「Zenn の記事を書いて」 | tech-article-writer |
  | 「note に技術記事を書きたい」 | note-article-writer（そこから他の2つを呼ぶ） |
  | 「読みやすくして」「この文章、何を言っているかわからないので直して」 | natural-japanese |
  | 「AIっぽいので読みやすくして」 | natural-japanese |
  | 「AI臭を消して」「自然な文章にして」 | humanize-ja |
  | 「AIっぽくないか見て」 | stop-ai-slop |

- 非公開情報のない試験用メモで note 記事を1本作り、2スキルの呼び出し、出力の型、有料部分の目印、素材にない事実が増えていないことを確かめる。試験の下書きは育成用フォルダに残さない
- `git check-ignore` で2スキルが追跡対象になり、着手前からある変更が残っている
