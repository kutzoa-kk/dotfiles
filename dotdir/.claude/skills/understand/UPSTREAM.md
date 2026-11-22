# 出どころ

- 取得元：https://github.com/fkubota/understand-mode （MIT ライセンス。`LICENSE` を参照）
- コミット：`89ebc91d3826676b6523d31092d90b9018907b69`
- 写した日：2026-11-21
- 写した範囲：`skill/understand/` 以下と `LICENSE`。開発用の `dev/` は写していない

## 手を入れたファイル

分からなかった文を書き方の決まり（`~/.claude/japanese-style-guide.md`）へ戻す変更と、Codex の会話を分岐して使うための変更を入れた。

| ファイル | 変更 |
| --- | --- |
| `app/public/confusions.js` | 新規。付箋から「質問」「詳しく」「用語」の記録を組み立てる `collectConfusions` |
| `app/public/index.html` | `confusions.js` を `app.js` の前に読み込み、案内を両ツール共通の表現にする |
| `app/public/app.js` | `finishWith` で `confusions` を添えて送り、待機中の案内を共通化 |
| `app/server.js` | `sanitizeConfusions` と記録保存、`--provider claude\|codex` に応じた呼び出しと終了処理 |
| `app/codex-provider.js` | 新規。Codex app-server の分岐・追質問・権限制御・分岐削除 |
| `SKILL.md` | 記録を決まりへ戻す手順と、Claude Code / Codex それぞれの起動手順 |
| `agents/openai.yaml` | 新規。Codex でも明示的に呼び出すスキルとして扱う |

試験は dotfiles の `.bin/tests/test_understand_*.py`（`make test-understand`）。参考リポジトリの新しい版を取り込むときは、上の変更箇所を見比べる。
