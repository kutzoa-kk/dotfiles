# 出どころ

- 取得元：https://github.com/fkubota/understand-mode （MIT ライセンス。`LICENSE` を参照）
- コミット：`89ebc91d3826676b6523d31092d90b9018907b69`
- 写した日：2026-11-21
- 写した範囲：`skill/understand/` 以下と `LICENSE`。開発用の `dev/` は写していない

## 手を入れたファイル

分からなかった文を記録し、書き方の決まり（`~/.claude/japanese-style-guide.md`）へ戻すための変更だけを入れた。

| ファイル | 変更 |
| --- | --- |
| `app/public/confusions.js` | 新規。付箋から「質問」「詳しく」「用語」の記録を組み立てる `collectConfusions` |
| `app/public/index.html` | `confusions.js` を `app.js` の前に読み込む |
| `app/public/app.js` | `finishWith` で `/api/return` に `confusions` を添えて送る |
| `app/server.js` | `sanitizeConfusions` を追加し、`/api/return` で `<DIR>/confusions.json` を書く |
| `SKILL.md` | 「3.『終わった』と言われたら」に、記録を決まりへ戻す手順を追加 |

試験は dotfiles の `.bin/tests/test_understand_skill.py`（`make test-understand`）。参考リポジトリの新しい版を取り込むときは、上の5か所を見比べる。
