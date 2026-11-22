# 出どころ

- 取得元：https://github.com/coji/natural-japanese （MIT ライセンス。`LICENSE` を参照）
- 版：2.0.0
- コミット：`840bd400cbcb64c8b64d492a144da54fc05776c5`
- 写した日：2026-11-22
- 写した範囲：`skills/natural-japanese/` 以下と、リポジトリ直下の `LICENSE`

## 手を入れたファイル

| ファイル | 変更 |
| --- | --- |
| `SKILL.md` | `description` の1行。humanize-ja、stop-ai-slop、japanese-output-review、note-article-writer との取り合いを防ぐ |
| `SKILL.md` | 「この環境での使い方」の1節を追加。文末体を保つこと、他スキルから呼ばれたときに報告を足さないこと、省かない検査を示す。RTK による出力の切り詰めを避け、`uv` が動かない隔離環境での代わりの手順を示す |

`SKILL.md` の本文にある `critical-thinking` は入れていない。

## 新しい版を取り込む手順

`~/.claude/skills` はこのリポジトリへのリンクなので、ここへ置いた時点で全セッションに反映される。プラグインや `npx skills` では更新しない（`description` の変更が消えるため）。

1. 新しい版を作業用の一時ディレクトリに取得する。
2. このコミットからの差分を読む。スクリプトの通信、プロセス起動、書き込み、依存の追加は特に確かめる。
3. 一時ディレクトリの側で、現在の `description` と追加した1節を当て直す。
4. 検査スクリプト（`lint.py`、`calques.py`、`newfacts.py`）を別の作業ディレクトリから動かす。50行を超える出力が `rtk proxy` で欠けないことも確かめる。
5. このフォルダの中身を置き換え、この文書の版、コミット、日付を直す。
