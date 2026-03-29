# Dotfiles

個人用のdotfilesリポジトリです。macOS環境の設定を管理します。

## 含まれる設定

- **zsh**: zinit、Powerlevel10k、各種プラグイン
- **Homebrew**: パッケージとアプリケーションの管理
- **iTerm2**: ターミナル設定
- **macOS**: システム設定
- **Git**: `.gitconfig`（ユーザー名、メールアドレス）
- **GitHub CLI**: `.config/gh/config.yml`（エイリアス、プロトコル設定）
- **SSH**: `.ssh/config`（SSH接続設定）
- **VSCode**: `.vscode/`（エディタ設定、キーバインド、スニペット）
- **Cursor**: `.cursor/`（エディタ設定、MCP設定）
- **Codex**: `.codex/`（Codex設定、ユーザースキル）
- **ClaudeCode**: `.claude/`（ClaudeCode設定）
- **Gemini**: `.gemini/`（Gemini設定）
- **npm**: `.npm-global-packages.txt`（グローバルパッケージリスト）

## セットアップ方法

### 新規PCへの移行時

1. このリポジトリをクローン:
```bash
git clone <repository-url> ~/dotfiles
cd ~/dotfiles
```

2. セットアップスクリプトを実行:
```bash
make setup
```

または、個別のスクリプトを実行:
```bash
make all
```

### 個別のセットアップ

- `make init` - HomebrewとXcode Command Line Toolsのインストール
- `make link` - dotfileのシンボリックリンク作成
- `make brew` - Homebrewパッケージのインストール
- `make macos_setup` - macOSシステム設定の適用
- `make iterm2` - iTerm2設定の適用
- `make npm` - npmグローバルパッケージのインストール
- `make github` - GitHub SSH設定（オプション）

## ファイル構成

```
dotfiles/
├── .bin/              # セットアップスクリプト
│   ├── init.sh        # Homebrewのインストール
│   ├── link.sh        # dotfileのリンク作成
│   ├── brew.sh        # Homebrew Bundleの実行
│   ├── macos_setup.sh # macOS設定
│   ├── iterm2_setup.sh # iTerm2設定
│   ├── npm_install.sh  # npmグローバルパッケージのインストール
│   ├── github.sh      # GitHub SSH設定
│   └── setup.sh       # 新規PC移行用スクリプト
├── iterm2/            # iTerm2設定ファイル
├── .zshrc             # zsh設定
├── .zprofile          # zshログイン時設定
├── .p10k.zsh          # Powerlevel10k設定
├── .gitconfig         # Git設定
├── .ssh/              # SSH設定（configファイルのみ）
│   └── config
├── .vscode/           # VSCodeエディタ設定
│   └── User/
│       ├── settings.json     # エディタ設定
│       ├── keybindings.json  # キーバインド設定
│       └── snippets/         # スニペット
├── .cursor/           # Cursorエディタ設定
│   ├── argv.json      # エディタ起動設定
│   └── mcp.json       # MCPサーバー設定
├── .codex/            # Codex設定
│   ├── README.md      # 設定ディレクトリの説明
│   ├── config.json    # Codex設定ファイル（存在する場合）
│   └── skills/        # Codexユーザー定義スキル（存在する場合）
├── .claude/           # ClaudeCode設定
├── .gemini/           # Gemini設定
├── .config/           # アプリケーション設定
│   ├── git/           # Git設定
│   │   ├── ignore     # Gitグローバルignoreファイル
│   │   └── commit_template  # Gitコミットテンプレート
│   └── gh/            # GitHub CLI設定
│       └── config.yml # エイリアス、プロトコル設定
├── .npm-global-packages.txt  # npmグローバルパッケージリスト
├── .Brewfile          # Homebrewパッケージリスト
└── Makefile           # メイクターゲット

## 注意事項

### SSH設定について
- `.ssh/config`のみを管理します
- **秘密鍵は含まれません**。新しいPCに移行する際は、秘密鍵を別途コピーしてください
- `make link`実行時、`~/.ssh`ディレクトリが存在しない場合は自動的に作成されます

### GitHub CLI設定について
- `.config/gh/config.yml`のみを管理します
- **`hosts.yml`は認証トークンを含むためリンク対象外**です

### VSCode設定について
- `dotdir/.vscode/User/`内の設定ファイル（`settings.json`、`keybindings.json`、`snippets/`）を`~/Library/Application Support/Code/User/`にリンクします
- 拡張機能やワークスペース設定は含まれません

### Cursor設定について
- `.cursor/`ディレクトリ内の設定ファイルのみをリンクします
- 拡張機能やプロジェクト情報などの個人固有のファイルは含まれません

### Codex設定について
- `.codex/`ディレクトリ内の設定ファイル（`config.json`など）をリンクします
- `.codex/skills/`ディレクトリ内のユーザー定義スキルをリンクします（システムスキルは除外）
- 既存の`~/.codex`ディレクトリがある場合、設定ファイルのみをマージしてリンクします

### ClaudeCode設定について
- `.claude/`ディレクトリ内の設定ファイルをリンクします
- 設定ファイルを追加すると、自動的にリンクされます

