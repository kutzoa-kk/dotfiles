# Codex の共通設定

- `AGENTS.md`: Codex の共通指示です。リポジトリ固有の指示は各リポジトリの `AGENTS.md` に置きます。
- `skills/`: 選択したユーザースキルを管理します。Codex が管理するシステムスキルは含めません。
- `config.toml`: モデル選択、ローカルパス、信頼履歴などを含む機械固有の稼働設定です。git の追跡対象外です。

リポジトリルートで `make link` を実行すると、[`.bin/link.sh`](../../.bin/link.sh) が `AGENTS.md` などの通常ファイルを `~/.codex/` へリンクします。`README.md` は除外され、ユーザースキルは個別にリンクされます。既存の `~/.codex/` ディレクトリは維持されます。

`make link` は他ツールの設定も反映します。共通指示だけを更新する場合は、既存の `~/.codex/AGENTS.md` を退避したうえで、この `AGENTS.md` だけをリンクします。リンク後は、このファイルの編集が稼働側にも反映されます。

更新した共通指示は新しい Codex セッションで確認してください。現在のセッションへの再読み込みは前提にしません。

## security-guidance の Codex adapter

Claude 用の security-guidance は、Codex が受け付けない `metrics` / `rewakeSummary` を出力し、Codex が解釈しない `if` 条件付きの hook を複数登録します。`scripts/security-guidance-adapter.py` が共通の検査本体を呼び、Codex 用の入力・出力と実行条件を扱います。

検査は同期で実行され、PostToolUse / Stop / SubagentStop は最大 600 秒待機します。検査本体の Claude Agent SDK と Claude の認証設定は引き続き必要です。Codex の `apply_patch` は変更後のファイル内容（postimage）をファイルごとの入力に変換し、削除・移動した元パスも検査本体へ伝えます。

```bash
make codex-security-hooks-dry-run  # hook 定義の差分だけを表示
make codex-security-hooks          # 対象 plugin のみ適用
make codex-security-hooks-check    # 未適用・古い定義があると非ゼロ終了
make test-codex-security-hooks     # 隔離 fixture と出力 schema で検証
```

適用先は `$CODEX_HOME`（未設定なら `~/.codex`）配下の `plugins/cache/claude-plugins-official/security-guidance/*/.codex-plugin/plugin.json` です。インストール済みの各 version に Codex 専用 manifest を作成し、`hooks` を明示します。既存 manifest の他の項目は保持し、未管理の Codex hook 定義や、優先されるルート manifest の `extensions.com.openai` がある場合は上書きせず停止します。共通の検査コード、Claude 用の `hooks/hooks.json`、Claude の設定、Codex の信頼履歴は変更しません。未インストールなら何も適用しません。

hook command は、この checkout の adapter を絶対パスで参照します。`make link` でも同じ適用処理を行いますが、hook だけを更新するときは専用 target を使います。**plugin の更新・再インストール後や、この checkout の移動後は `make codex-security-hooks` を再実行してください。** cache 自体の永続性や更新後の自動適用には依存しません。適用後は Codex を再起動し、表示された新しい hook 定義を確認・信頼してください。adapter の処理中に信頼を自動承認することはありません。

初回適用時の manifest は、同じディレクトリの `security-guidance-overlay.backup.json` に保存します。復元時は `original_manifest` が文字列ならその内容を `plugin.json` に戻し、`null` なら今回作成した Codex 用 `plugin.json` のみを削除します。先に overlay 以外の変更が加わっていないことを確認してください。上流が Codex 専用 hook を提供した場合は、上流の定義を優先するかを確認してから再適用します。

検証用の Codex home は `.bin/apply-codex-security-guidance.py --codex-home /path/to/fixture --check` のように明示できます。
