# 📝 Claude Code コマンド一覧

<div align="center">

![Commands](https://img.shields.io/badge/コマンド-218+-brightgreen?style=for-the-badge)
![Namespaces](https://img.shields.io/badge/名前空間-15+-blue?style=for-the-badge)

**Claude Codeで使用可能なスラッシュコマンド（`/command:name`形式）の包括的なガイド**

[クイックスタート](#-クイックスタート) • [コマンド名前空間](#-コマンド名前空間) • [使用方法](#-使用方法) • [よくあるワークフロー](#-よくあるワークフロー)

</div>

---

## 🌟 コマンドとは？

Claude Codeコマンドは、`.claude/commands/`ディレクトリ内のMarkdownファイルとして定義されたスラッシュコマンドです。各コマンドは構造化されたワークフローを実行し、開発タスクを自動化します。

### コマンドの特徴

- **名前空間**: `/namespace:command-name`形式で整理
- **自動認識**: Claude Codeが起動時に自動的に読み込み
- **構造化**: 各コマンドは明確な指示セクションを持つ
- **拡張可能**: 独自のコマンドを簡単に追加可能

## 🚀 クイックスタート

### 基本的な使用方法

```bash
# コマンドの実行
/dev:code-review                    # コードベース全体をレビュー
/project:create-feature dashboard   # 新機能の作成
/security:security-audit           # セキュリティ問題のチェック

# パラメータ付き
/dev:fix-issue 123                 # 特定のIssueを修正
/simulation:business-scenario-explorer "市場拡大を評価"  # シナリオ分析
```

### コマンドの構造

各コマンドファイルは以下の構造を持ちます：

```markdown
# コマンド名

コマンドの説明

## Instructions

1. **ステップ1**
   - 具体的なアクション
   - 確認事項

2. **ステップ2**
   - 実行内容
   - 結果の検証
```

## 📚 コマンド名前空間

### ルートディレクトリのコマンド

ルートディレクトリには、名前空間に分類されていない汎用的なコマンドが配置されています：

**分析・レビュー**
- `analyze-dependencies.md` - 依存関係の分析
- `analyze-performance.md` - パフォーマンス分析（UX観点）
- `smart-review.md` - 自動ロール判定レビュー
- `check-fact.md` - 事実確認
- `check-github-ci.md` - GitHub CI確認
- `check-prompt.md` - プロンプト確認

**コード操作**
- `explain-code.md` - コードの説明
- `fix-error.md` - エラー修正
- `refactor.md` - リファクタリング
- `design-patterns.md` - デザインパターン
- `tech-debt.md` - 技術的負債の管理

**コミット・Git**
- `commit-message.md` - コミットメッセージ生成
- `semantic-commit.md` - セマンティックコミット

**プルリクエスト** (`pr-*.md`)
- `pr-create.md` - PR作成
- `pr-review.md` - PRレビュー
- `pr-feedback.md` - PRフィードバック
- `pr-issue.md` - PRとIssueの連携
- `pr-list.md` - PR一覧
- `pr-auto-update.md` - PR自動更新

**ロール・思考**
- `role.md` - ロール設定
- `role-help.md` - ロールヘルプ
- `role-debate.md` - ロール討論
- `multi-role.md` - マルチロール
- `sequential-thinking.md` - 順次思考
- `ultrathink.md` - 超思考モード

**プロジェクト管理**
- `plan.md` - 計画作成
- `show-plan.md` - 計画表示
- `task.md` - タスク管理
- `spec.md` - 仕様定義

**依存関係更新** (`update-*-deps.md`)
- `update-node-deps.md` - Node.js依存関係更新
- `update-rust-deps.md` - Rust依存関係更新
- `update-flutter-deps.md` - Flutter依存関係更新
- `update-dart-doc.md` - Dartドキュメント更新
- `update-doc-string.md` - ドキュメント文字列更新

**ユーティリティ**
- `screenshot.md` - スクリーンショット
- `search-gemini.md` - Gemini検索
- `context7.md` - Context7統合
- `style-ai-writing.md` - AI文章スタイル
- `token-efficient.md` - トークン効率化

### `/project:*` - プロジェクト管理

プロジェクトの初期化、設定、管理。プロジェクト作成、依存関係管理、マイルストーン追跡、ヘルスモニタリング。

**主要コマンド:**
- `/project:init-project` - 新しいプロジェクトの初期化
- `/project:create-feature` - 新機能の作成
- `/project:add-package` - 依存関係の追加
- `/project:milestone-tracker` - マイルストーンの追跡
- `/project:project-health-check` - プロジェクトヘルスチェック
- `/project:pac-*` - Product as Code (PAC) 関連コマンド

詳細: [project/README.md](project/README.md)

### `/dev:*` - 開発ツール

コードレビュー、デバッグ、リファクタリング、分析モードなどの開発ユーティリティ。

**主要コマンド:**
- `/dev:code-review` - 包括的なコード品質レビュー
- `/dev:debug-error` - エラーの体系的デバッグと修正
- `/dev:explain-code` - コード機能の分析と説明
- `/dev:refactor-code` - インテリジェントなリファクタリングと品質改善
- `/dev:fix-issue` - コード問題の特定と解決
- `/dev:ultra-think` - 深い分析と問題解決モード
- `/dev:prime` - 複雑なタスク用の強化AIモード
- `/dev:all-tools` - 利用可能なすべての開発ツールの表示

詳細: [dev/README.md](dev/README.md)

### `/test:*` - テストスイート

ユニットテスト、統合テスト、E2Eテスト、カバレッジ分析、ミューテーションテスト、ビジュアルリグレッションテストのツール。

**主要コマンド:**
- `/test:generate-test-cases` - 包括的なテストケースの自動生成
- `/test:write-tests` - ユニットテストと統合テストの作成
- `/test:test-coverage` - テストカバレッジの分析とレポート
- `/test:setup-comprehensive-testing` - 包括的なテストインフラのセットアップ
- `/test:e2e-setup` - エンドツーエンドテストスイートの設定
- `/test:setup-visual-testing` - ビジュアルリグレッションテストのセットアップ

詳細: [test/README.md](test/README.md)

### `/security:*` - セキュリティ・コンプライアンス

セキュリティ監査、依存関係スキャン、認証実装、コードベースセキュリティの強化。

**主要コマンド:**
- `/security:security-audit` - 包括的なセキュリティ評価
- `/security:dependency-audit` - セキュリティ脆弱性の依存関係監査
- `/security:security-hardening` - アプリケーションセキュリティ設定の強化
- `/security:add-authentication-system` - 安全なユーザー認証システムの実装

詳細: [security/README.md](security/README.md)

### `/performance:*` - パフォーマンス最適化

ビルド時間、バンドルサイズ、データベースクエリ、キャッシュ戦略、アプリケーションパフォーマンスの最適化ツール。

**主要コマンド:**
- `/performance:performance-audit` - アプリケーションパフォーマンスメトリクスの監査
- `/performance:optimize-build` - ビルドプロセスと速度の最適化
- `/performance:optimize-bundle-size` - バンドルサイズの削減と最適化
- `/performance:optimize-database-performance` - データベースクエリとパフォーマンスの最適化
- `/performance:implement-caching-strategy` - キャッシュソリューションの設計と実装

詳細: [performance/README.md](performance/README.md)

### `/deploy:*` - デプロイメント・リリース

リリース準備、自動デプロイ、ロールバック機能、コンテナ化、Kubernetesデプロイメント管理。

**主要コマンド:**
- `/deploy:prepare-release` - リリースパッケージの準備と検証
- `/deploy:hotfix-deploy` - 重要なホットフィックスの迅速なデプロイ
- `/deploy:rollback-deploy` - 以前のバージョンへのデプロイロールバック
- `/deploy:setup-automated-releases` - 自動リリースワークフローのセットアップ
- `/deploy:containerize-application` - デプロイ用のアプリケーションコンテナ化

詳細: [deploy/README.md](deploy/README.md)

### `/sync:*` - 統合・同期

GitHub IssuesとLinearの双方向同期、PR追跡、競合解決、クロスプラットフォームタスク管理。

**主要コマンド:**
- `/sync:sync-issues-to-linear` - GitHub IssuesをLinearワークスペースに同期
- `/sync:sync-linear-to-issues` - LinearタスクをGitHub Issuesに同期
- `/sync:bidirectional-sync` - GitHub-Linear双方向同期の有効化
- `/sync:sync-pr-to-task` - プルリクエストをLinearタスクにリンク

詳細: [sync/README.md](sync/README.md)

### `/orchestration:*` - タスクオーケストレーション

複雑なプロジェクトを追跡可能なワークフローに整理するタスク管理と実行システム。タスク分解、進捗追跡、Git同期、コンテキスト保持。

**主要コマンド:**
- `/orchestration:start` - インテリジェントなタスク分解で新しいプロジェクトを開始
- `/orchestration:status` - 進捗を確認し、すべてのプロジェクトで何が起こっているかを見る
- `/orchestration:resume` - 完全なコンテキスト復元で中断した場所から続ける
- `/orchestration:move` - 作業が進むにつれてタスクステータスを更新
- `/orchestration:commit` - タスクにリンクされたプロフェッショナルなGitコミットを作成

詳細: [orchestration/ORCHESTRATION-README.md](orchestration/ORCHESTRATION-README.md)

### `/simulation:*` - シナリオシミュレーター

シナリオ探索、デジタルツイン、タイムライン圧縮による意思決定分析のためのシミュレーションとモデリングツール。

**主要コマンド:**
- `/simulation:business-scenario-explorer` - 制約検証付きマルチタイムラインビジネス探索
- `/simulation:digital-twin-creator` - データ品質チェック付き体系的なデジタルツイン作成
- `/simulation:decision-tree-explorer` - 確率重み付け付き意思決定ブランチ分析
- `/simulation:timeline-compressor` - 信頼区間付き加速シナリオテスト

詳細: [simulation/README.md](simulation/README.md)

### `/wfgy:*` - セマンティック推論・メモリ

数学的検証、永続メモリ、幻覚防止を提供するセマンティック推論システム。

**主要コマンド:**
- `/wfgy:init` - WFGYセマンティック推論システムの初期化
- `/wfgy:bbmc` - セマンティック残差最小化の適用
- `/wfgy:bbpf` - マルチパス進行の実行
- `/wfgy:bbcr` - 崩壊-再生修正のトリガー
- `/semantic:*` - セマンティックメモリ管理
- `/memory:*` - メモリ管理（チェックポイント、リコール、圧縮）

詳細: [wfgy/README.md](wfgy/README.md)

### `/docs:*` - ドキュメント生成

API、アーキテクチャ図、オンボーディングガイド、トラブルシューティングドキュメントのドキュメント自動化。

**主要コマンド:**
- `/docs:generate-api-documentation` - APIリファレンスドキュメントの自動生成
- `/docs:doc-api` - コードからAPIドキュメントを生成
- `/docs:create-architecture-documentation` - 包括的なアーキテクチャドキュメントの生成
- `/docs:create-onboarding-guide` - 開発者オンボーディングガイドの作成

詳細: [docs/README.md](docs/README.md)

### `/setup:*` - 設定・セットアップ

開発環境、リンティング、フォーマット、監視、データベーススキーマ、API設計のセットアップコマンド。

**主要コマンド:**
- `/setup:setup-development-environment` - 完全な開発環境のセットアップ
- `/setup:setup-linting` - コードリンティングと品質ツールのセットアップ
- `/setup:setup-formatting` - コードフォーマットツールの設定
- `/setup:migrate-to-typescript` - JavaScriptプロジェクトをTypeScriptに移行

詳細: [setup/README.md](setup/README.md)

### `/team:*` - チームコラボレーション

スタンドアップレポート、スプリント計画、レトロスペクティブ、ワークロードバランシング、ナレッジ管理を含むチームワークフローツール。

**主要コマンド:**
- `/team:standup-report` - 日次スタンドアップレポートの生成
- `/team:sprint-planning` - スプリントワークフローの計画と整理
- `/team:retrospective-analyzer` - 洞察のためのチームレトロスペクティブの分析
- `/team:team-workload-balancer` - チームワークロード分散のバランス調整

詳細: [team/README.md](team/README.md)

### `/skills:*` - Claude Code Skills

Claude Code Skillsの構築、管理、配布のためのプロフェッショナルツール。

**主要コマンド:**
- `/skills:build-skill` - 新しいClaude Code Skillの作成
- `/skills:package-skill` - Skillのパッケージ化と配布

詳細: [skills/README.md](skills/README.md)

### `/spec-workflow:*` - Spec Workflow

仕様駆動開発とインテリジェントなタスクオーケストレーション、マルチエージェント並列化を可能にする高度なタスク管理コマンド。

**主要コマンド:**
- `/spec-workflow:parallel-tasks` - 専門エージェントで複数のタスクを並列実行
- `/spec-workflow:parallel-tasks-help` - 並列タスク実行の包括的なヘルプ表示

詳細: [spec-workflow/README.md](spec-workflow/README.md)

## 💡 使用方法

### コマンドの実行

コマンドは`/namespace:command-name`形式で実行します。各コマンドはそのMarkdownファイルで定義された構造化ワークフローを実行します。

**例:**
- `/dev:code-review` - コードベースの品質、セキュリティ、パフォーマンスを分析
- `/project:create-feature dashboard` - 新機能の計画、実装、テスト
- `/dev:fix-issue 123` - 体系的なアプローチでGitHub Issueを解決

### コマンドの作成

新しいコマンドを作成するには、`.claude/commands/`ディレクトリにMarkdownファイルを追加します：

```markdown
# カスタムコマンド名

特定のタスクを実行します。

## Instructions

1. **最初のステップ**
   - このことを行う
   - そのことを確認

2. **2番目のステップ**
   - このアクションを実行
   - 結果を検証
```

すぐに`/namespace:custom-command-name`として使用できます。

## 🔄 よくあるワークフロー

### 新機能開発

```bash
/dev:code-review                    # 現在の状態を評価
/project:create-feature user-dashboard  # 機能を実装
/security:security-audit                 # セキュリティを確認
```

### バグ修正

```bash
/dev:fix-issue 456                  # 特定のIssueを修正
/dev:code-review                    # 修正品質を確認
```

### コードメンテナンス

```bash
/security:dependency-audit               # 古い依存関係をチェック
/performance:performance-audit              # ボトルネックを特定
/dev:refactor-code legacy-module    # 問題のある領域を改善
```

### 戦略的意思決定

```bash
/simulation:constraint-modeler              # 意思決定制約をマッピング
/simulation:business-scenario-explorer      # 複数のタイムラインを探索
/simulation:decision-tree-explorer          # 意思決定選択を最適化
```

### 複雑なプロジェクト管理

```bash
/orchestration:start                        # プロジェクトをタスクに分解
/orchestration:status                       # 進捗を監視
/orchestration:resume                       # 中断後も続行
/orchestration:commit                       # リンクされたGitコミットを作成
```

## 📊 コマンド統計

- **総コマンド数**: 218+
- **名前空間数**: 15+
- **ルートコマンド数**: 40+
- **カテゴリ**: 開発、テスト、セキュリティ、パフォーマンス、デプロイ、統合、ドキュメント、設定、チーム、シミュレーション、オーケストレーション、ユーティリティ

## 📁 ファイル整理の提案

現在、ルートディレクトリに多くのコマンドが散らばっています。以下の整理を提案します：

### 推奨される整理

**1. `/dev/` ディレクトリに移動**
- `explain-code.md` → `dev/explain-code.md`
- `fix-error.md` → `dev/fix-error.md`
- `refactor.md` → `dev/refactor.md`
- `design-patterns.md` → `dev/design-patterns.md`
- `tech-debt.md` → `dev/tech-debt.md`
- `sequential-thinking.md` → `dev/sequential-thinking.md`
- `ultrathink.md` → `dev/ultrathink.md`
- `analyze-dependencies.md` → `dev/analyze-dependencies.md`

**2. `/dev/pr/` ディレクトリを作成**
- `pr-*.md` すべて → `dev/pr/` に移動

**3. `/dev/commit/` ディレクトリを作成**
- `commit-message.md` → `dev/commit/commit-message.md`
- `semantic-commit.md` → `dev/commit/semantic-commit.md`

**4. `/project/` ディレクトリに移動**
- `plan.md` → `project/plan.md`
- `show-plan.md` → `project/show-plan.md`
- `spec.md` → `project/spec.md`

**5. `/orchestration/` ディレクトリに移動**
- `task.md` → `orchestration/task.md`

**6. `/performance/` ディレクトリに移動**
- `analyze-performance.md` → `performance/analyze-performance.md`

**7. `/setup/` ディレクトリに移動**
- `update-*-deps.md` すべて → `setup/update-deps/` に移動

**8. `/utils/` ディレクトリを作成**
- `screenshot.md` → `utils/screenshot.md`
- `search-gemini.md` → `utils/search-gemini.md`
- `context7.md` → `utils/context7.md`
- `style-ai-writing.md` → `utils/style-ai-writing.md`
- `token-efficient.md` → `utils/token-efficient.md`
- `check-*.md` → `utils/check/` に移動

**9. `/role/` ディレクトリを作成**
- `role.md`, `role-help.md`, `role-debate.md`, `multi-role.md` → `role/` に移動

この整理により、コマンドの検索性と保守性が向上します。

## 🔧 カスタマイズ

### コマンドの修正

既存のコマンドを修正するには、`.claude/commands/`内の対応するMarkdownファイルを編集します。

### コマンドの削除

使用しないコマンドは、対応するMarkdownファイルを削除するだけで無効化できます。

## 📚 追加リソース

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - Anthropicのベストプラクティス
- [Claude Code Documentation](https://docs.anthropic.com/claude-code) - 公式ドキュメント
- [Claude Command Suite](https://github.com/qdhenry/Claude-Command-Suite) - 元のリポジトリ

## 🤝 コントリビューション

新しいコマンドや既存コマンドの改善を歓迎します。各名前空間のREADMEを参照して、コマンドの構造とスタイルを確認してください。

---

<div align="center">

**🚀 開発ワークフローを加速する準備はできましたか？**  
`/dev:code-review`から始めましょう

*Powered by Claude Command Suite - コマンドがワークフローになる場所*

</div>

