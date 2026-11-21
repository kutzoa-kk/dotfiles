# AGENTS.md

macOS dotfiles repository. Setup instructions and directory structure are in [README.md](README.md).

## Working with This Repo

- `make link` でシンボリックリンクを作成。`dotdir/` 配下のファイルが `$HOME` にリンクされる
- リンク戦略はツールごとに異なる。詳細は `.bin/link.sh` を参照

## Codex セッション開始時

- このリポジトリで新しい Codex セッションを始めたら、最初の作業時に一度だけ [share-claude-skills](dotdir/.claude/skills/share-claude-skills/SKILL.md) を読み、共有状況の確認を実行します。コンテキスト圧縮後の再実行は不要です。
- 起動時は読み取りだけに留め、未共有・競合・リンク切れがあれば件数と代表例を短く伝えて依頼された作業を続けます。共有済みだけなら一言で済ませます。共有リンクの追加や修正は、ユーザーから共有・同期を依頼されたときに行います。

## Change Guidelines

- **dotdir/ 配下を編集** = `$HOME` の設定が変わる。影響範囲を意識すること
- **秘密鍵・トークン等は絶対にコミットしない**（`.ssh/` には config のみ）
- AI tool configs（`.claude/`, `.codex/`, `.cursor/`, `.gemini/`）はツール自動生成ファイルと共存するため、merge 戦略でリンクされる。リンク対象外のファイルを壊さないこと
- `.Brewfile` 変更時は `brew bundle --file=.Brewfile` で検証可能
- `settings.json` の扱い（git=種／稼働=ライブ／symlink 禁止。恒久変更は `make settings-pull`）は docs/[settings-ownership.md](docs/settings-ownership.md)を参照

