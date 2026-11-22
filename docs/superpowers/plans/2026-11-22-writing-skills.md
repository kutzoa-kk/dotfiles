# 日本語の記事・推敲スキル 実装計画

> **実行方法:** 主担当がこのセッションで順に実装する（2026-11-22 承認）。commit は完了報告後の依頼で行う。push はしない。

**Goal:** `tech-article-writer` と `natural-japanese` を単独でも、`note-article-writer` からも使えるようにする。

**Architecture:** 2スキルを作業領域で完成させ、検査に通してから `dotdir/.claude/skills/` へ移す。移した時点で全セッションに反映される。Codex と agy には個別リンクで共有する。

**Tech Stack:** Markdown のスキル、上流の Python 検査スクリプト（`uv`、`sudachipy`）

**Spec:** `docs/superpowers/specs/2026-11-22-writing-skills-design.md`

## Global Constraints

- `description` と note への追記文は設計書の文をそのまま使う
- natural-japanese の変更は `description`、実行環境の注意1節、`LICENSE`、`UPSTREAM.md` だけ
- gist の文面、例文、一覧を写さない
- 着手前からある未コミットの変更を変えない
- `make link`、`semantic.py`、push は実行しない。commit は依頼されてから行う
- 試験で実際の育成用フォルダ、learned-rules、note、外部公開に触れない

## Review Focus

- 「AIっぽいので読みやすくして」：natural-japanese が選ばれる
- note の技術記事：note-article-writer が主になり、出力の型が崩れない
- 有料部分の目印と `【要確認：】`：推敲で消えない
- 素材にない体験や数値：2スキルを通しても増えない
- 別の作業ディレクトリ：検査スクリプトと参照ファイルを解決できる

### Task 1: 検査を先に用意する

- [x] 着手前の未コミットのファイルの写しとハッシュを作業領域に保存する
- [x] 設計書の完了条件を検査するスクリプトを作業領域に書き、未実装の状態で失敗することを確かめる
- [x] 上流のスクリプトを点検し、`lint.py`、`calques.py`、`newfacts.py` を別ディレクトリから動かす

### Task 2: 2スキルを作業領域で作る

- [x] `tech-article-writer/{SKILL.md,references/design.md,references/review.md,LICENSE,UPSTREAM.md}` を書く
- [x] `natural-japanese/` を写し、`description` を替え、`LICENSE` と `UPSTREAM.md` を足す
- [x] 検査：frontmatter、行数、参照先、上流との差、gist との一致

### Task 3: 反映する

- [x] `.gitignore` に2スキルを許可する
- [x] 2スキルを `dotdir/.claude/skills/` へ写す
- [x] `note-article-writer/SKILL.md` に呼び出しの節を足し、仕上げの項を書き換える
- [x] `~/.agents/skills/` に個別リンクを2本張る
- [x] 検査：全項目が通り、`check_sharing.py` で共有済みになる

### Task 4: 新しいセッションで試す

- [x] 設計書の依頼表で、選ばれるスキルを確かめる（起動した時点で止め、書き込みはさせない）
- [x] 架空のメモから有料の技術記事を作り、呼び出し、出力の型、目印、事実の追加を確かめる（Claude Code と Codex）
- [x] 育成用フォルダ、learned-rules、着手前の変更が無傷であることを確かめる
- [x] 独立した反証検証を受け、指摘を直してから報告する

## 実施結果（2026-11-22）

- 最終の受け入れ検査は42項目、共有の試験は6件、Claude Code の起動判定は10件が通った
- note の通し試験（Claude Code・Codex 各1本）では、出力の3節、有料部分の目印、`【要確認：】`、内訳の確認事項が保たれた。ただし試験文で「出力の型どおり」と指示した条件である。Codex の最終応答には3節の前に保存報告が1行付いた。この試験の後に natural-japanese の `description` だけを変え、起動判定をやり直した
- Claude Code の通し試験は1本約6分、表示費用 $3.66。natural-japanese 単独の増分は測っていない

## 残る制約

- Codex の隔離環境では `uv` が依存物を取得できず、検査スクリプトが動かない。手動の点検表に切り替わる
- Codex の単独推敲で「検討を進めた結果」が2回とも消えた。文末体の変化は規則の追加で直ったが、意味の保持は直り切っていない
- Claude Code の単独推敲は、最終試験と再試験のどちらも複合コマンドを拒否された時点で目視に切り替え、許可した実行形式を試さなかった。検査スクリプト3本の実行は単独利用では未検証（note の通し試験では3本とも実行）
- 出力の型は、対策の追記後、試験文での指示がない条件でも3節と本文の一致、育成の1行を確かめた（Codex と Claude Sonnet。最終版）。Sonnet では3節の前後に一言ずつ余分な文が残った。Opus は追記の初版で型どおりだった（最終版では未試験）
- 起動判定10件の通過は1回の結果である
- スキル一覧の枠が足りないと説明文が省かれ、起動先が変わりうる。途中の試験では「AIっぽいので読みやすくして」が1度外れた
- Codex の暗黙の起動と agy での動作は試していない
- Claude Sonnet では、note の通し試験2回とも `natural-japanese` を呼ばなかった（Bash を拒否された後に推敲を省いた）。未実施であることは応答の末尾に書かれた。Opus の試験では呼ばれた
