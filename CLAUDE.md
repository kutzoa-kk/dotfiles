# CLAUDE.md

macOS dotfiles repository. Setup instructions and directory structure are in [README.md](README.md).

## Working with This Repo

- `make link` でシンボリックリンクを作成。`dotdir/` 配下のファイルが `$HOME` にリンクされる
- リンク戦略はツールごとに異なる。詳細は `.bin/link.sh` を参照

## Change Guidelines

- **dotdir/ 配下を編集** = `$HOME` の設定が変わる。影響範囲を意識すること
- **秘密鍵・トークン等は絶対にコミットしない**（`.ssh/` には config のみ）
- AI tool configs（`.claude/`, `.codex/`, `.cursor/`, `.gemini/`）はツール自動生成ファイルと共存するため、merge 戦略でリンクされる。リンク対象外のファイルを壊さないこと
- `.Brewfile` 変更時は `brew bundle --file=.Brewfile` で検証可能
