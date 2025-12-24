# Dotfiles

個人用のdotfilesリポジトリです。macOS環境の設定を管理します。

## 含まれる設定

- **zsh**: zinit、Powerlevel10k、各種プラグイン
- **Homebrew**: パッケージとアプリケーションの管理
- **iTerm2**: ターミナル設定
- **macOS**: システム設定
- **Git**: `.gitconfig`（ユーザー名、メールアドレス）
- **SSH**: `.ssh/config`（SSH接続設定）
- **Cursor**: `.cursor/`（エディタ設定、MCP設定）

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
- `make github` - GitHub SSH設定（オプション）

## ファイル構成

```
dotfiles2/
├── .bin/              # セットアップスクリプト
│   ├── init.sh        # Homebrewのインストール
│   ├── link.sh        # dotfileのリンク作成
│   ├── brew.sh        # Homebrew Bundleの実行
│   ├── macos_setup.sh # macOS設定
│   ├── iterm2_setup.sh # iTerm2設定
│   ├── github.sh      # GitHub SSH設定
│   └── setup.sh       # 新規PC移行用スクリプト
├── iterm2/            # iTerm2設定ファイル
├── .zshrc             # zsh設定
├── .zprofile          # zshログイン時設定
├── .p10k.zsh          # Powerlevel10k設定
├── .gitconfig         # Git設定
├── .ssh/              # SSH設定（configファイルのみ）
│   └── config
├── .cursor/           # Cursorエディタ設定
│   ├── argv.json      # エディタ起動設定
│   └── mcp.json       # MCPサーバー設定
├── .config/           # アプリケーション設定
│   └── git/           # Git設定
│       └── ignore     # Gitグローバルignoreファイル
├── .Brewfile          # Homebrewパッケージリスト
└── Makefile           # メイクターゲット

## 注意事項

### SSH設定について
- `.ssh/config`のみを管理します
- **秘密鍵は含まれません**。新しいPCに移行する際は、秘密鍵を別途コピーしてください
- `make link`実行時、`~/.ssh`ディレクトリが存在しない場合は自動的に作成されます

### Cursor設定について
- `.cursor/`ディレクトリ内の設定ファイルのみをリンクします
- 拡張機能やプロジェクト情報などの個人固有のファイルは含まれません

