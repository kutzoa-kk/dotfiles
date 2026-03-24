---
name: custom-lint-rules
description: プロジェクト固有のカスタム lint ルールを生成。エラーメッセージに WHY（理由）と FIX（修正方法）を含む教育的メッセージを付与し、AI エージェントが即座に自己修正できるようにする。トリガー：「custom lint rule」「lint rule with fix message」「architecture enforcement」「dependency direction」「import restrictions」「create eslint rule」「ast-grep」「instructive error message」、または標準 linter ではカバーできないコーディング規約の機械的な強制が必要なとき。
---

# Custom Lint Rules Generator

標準 lint エラーは **何が** 間違っているかだけ伝える。優れた lint エラーは **なぜ** そのルールが存在し、**どう修正すべきか** まで伝える。このスキルはそのような「教育的エラーメッセージ」を持つカスタム lint ルールを生成する。

## Error Message Structure (必須フォーマット)

生成する全ルールのエラーメッセージは以下の構造に従う：

```
ERROR: [何が間違っているか] [file:line]
WHY: [なぜこのルールが存在するか — ADR があればリンク]
FIX: [具体的な修正手順とコード例]
EXAMPLE:
  // Bad:
  [違反コード]
  // Good:
  [正しいコード]
```

## Four Rule Categories

| Category | Purpose | Examples |
|----------|---------|---------|
| **Grep-ability** | 検索発見性の向上 | named export 必須、一貫したエラー型、明示的 DTO |
| **Glob-ability** | ファイル構造の予測可能性 | feature-based ディレクトリ、命名規約、co-location |
| **Architecture Boundaries** | 依存方向の強制 | レイヤー import 制約、モジュール境界、provider パターン |
| **Security/Privacy** | セキュリティ問題の検出 | secret ハードコード禁止、input validation、eval 禁止 |

## Tool Selection by Language

| Language | Primary Tool | Custom Rule Format |
|----------|-------------|-------------------|
| TypeScript/JS | ESLint custom plugin or ast-grep | Rule module with instructive message |
| Python | ast-grep or pylint custom checker | Checker class with message template |
| Go | golangci-lint + go/analysis | Analyzer with Diagnostic message |
| Rust | Clippy (limited) + custom cargo tool | Compile error with help annotation |
| Any language | **ast-grep** (universal fallback) | YAML pattern with message field |

> **ast-grep は万能フォールバック**: 言語固有ツールが複雑すぎる・利用不可の場合、ast-grep パターンは複数言語で動作し記述が容易。

## Workflow

### Step 1: Analyze Project

プロジェクトを分析し、以下を特定する：

1. **言語・フレームワーク検出**
   ```bash
   # package.json, pyproject.toml, go.mod, Cargo.toml 等を確認
   ls package.json pyproject.toml go.mod Cargo.toml 2>/dev/null
   ```

2. **既存 linter 設定の確認**
   ```bash
   # ESLint, Ruff, golangci-lint, Clippy 等の設定を確認
   ls .eslintrc* eslint.config.* .ruff.toml ruff.toml pyproject.toml .golangci.yml .clippy.toml 2>/dev/null
   ```

3. **アーキテクチャパターンの推定**
   - ディレクトリ構造からレイヤーを推定（domain/, infrastructure/, api/, service/ 等）
   - 既存の import パターンを分析
   - 命名規約を検出

4. **既存の ast-grep 設定確認**
   ```bash
   ls sgconfig.yml .ast-grep/ rules/ 2>/dev/null
   ```

**出力**: 検出結果サマリーをユーザーに提示。

### Step 2: Interview

ユーザーに以下を確認する（可能な限り検出結果からデフォルトを提案）：

1. **どのカテゴリのルールが必要か？**（複数選択可）
   - [ ] Grep-ability（検索性）
   - [ ] Glob-ability（構造予測性）
   - [ ] Architecture Boundaries（依存方向）
   - [ ] Security/Privacy（セキュリティ）

2. **特定のルールの要望はあるか？**
   - 例：「domain 層から infrastructure を import 禁止」
   - 例：「default export 禁止」
   - 例：「全 API handler に zod validation 必須」

3. **ツール選択の確認**
   - 検出した言語に基づくデフォルト提案
   - ast-grep をユニバーサルオプションとして常に提示

4. **ADR（Architecture Decision Record）の有無**
   - ルールの理由を ADR にリンクしたいか
   - 既存 ADR ディレクトリの場所

### Step 3: Generate Rules

選択されたカテゴリとツールに基づきルールを生成する。

各ルールに含めるもの：

1. **ルール実装**（ESLint plugin / ast-grep YAML / pylint checker / golangci-lint config）
2. **教育的エラーメッセージ**（ERROR / WHY / FIX / EXAMPLE 構造）
3. **テストケース**（ルールが正しくトリガーされることの検証）
4. **ADR リンク**（存在する場合）

#### ルール生成の手順

```
For each requested rule:
  1. references/rule-templates.md からカテゴリ×ツールのテンプレートを参照
  2. references/error-message-guide.md に従いエラーメッセージを作成
  3. プロジェクト固有のパス・型名・パターンをテンプレートに適用
  4. テストケースを作成（正常コードがパスし、違反コードが検出されること）
```

#### ast-grep を使う場合

`references/ast-grep-patterns.md` のパターンを参照：

```yaml
# sgconfig.yml に追加（なければ新規作成）
ruleDirs:
  - .ast-grep/rules
```

```bash
# ルールファイル配置
mkdir -p .ast-grep/rules
# 各ルールを .ast-grep/rules/<rule-id>.yml として生成
```

#### ESLint custom plugin を使う場合

```bash
# プロジェクトローカルプラグインとして生成
mkdir -p eslint-rules/rules
mkdir -p eslint-rules/tests
# eslint.config.js (flat config) または .eslintrc に登録
```

#### pylint custom checker を使う場合

```bash
mkdir -p pylint_custom/checkers
# pyproject.toml の [tool.pylint.master] load-plugins に登録
```

### Step 4: Integration

1. **linter 設定に追加**
   - 生成したルールを既存設定に組み込む
   - 新しい設定ファイルが必要な場合は作成

2. **PostToolUse hook の更新**（存在する場合）
   - ファイル保存時に lint が走るよう hook を設定
   - Claude Code の hooks 設定に ast-grep / eslint を追加

3. **CI への組み込みガイド**（推奨のみ、自動適用はしない）
   ```yaml
   # GitHub Actions example
   - name: Custom lint rules
     run: npx @ast-grep/cli scan --rule .ast-grep/rules/
   ```

4. **動作確認**
   ```bash
   # ast-grep の場合
   npx @ast-grep/cli scan --rule .ast-grep/rules/<rule-id>.yml <target-file>

   # ESLint の場合
   npx eslint --rulesdir eslint-rules/rules <target-file>

   # pylint の場合
   pylint --load-plugins=pylint_custom.checkers <target-file>
   ```

## References

- [Rule Templates](./references/rule-templates.md) — カテゴリ×ツール別テンプレート集
- [ast-grep Patterns](./references/ast-grep-patterns.md) — ユニバーサル ast-grep パターン集
- [Error Message Guide](./references/error-message-guide.md) — 教育的エラーメッセージの書き方

## Quick Start Example

ユーザーが「domain 層から infrastructure への import を禁止したい」と言った場合：

```yaml
# .ast-grep/rules/no-cross-layer-import.yml
id: no-cross-layer-import
language: typescript
rule:
  pattern: import { $$$NAMES } from '$PATH'
  inside:
    kind: program
constraints:
  PATH:
    regex: '\.\./infrastructure/'
fix: "// TODO: Use domain interface instead of infrastructure import"
message: |
  ERROR: Cross-layer import from infrastructure layer detected.
  WHY: Domain/service layers must not depend on infrastructure directly.
        This violates the Dependency Inversion Principle and makes the
        codebase harder to test and refactor. See ADR-005 if available.
  FIX: Import via the domain interface instead.
  EXAMPLE:
    // Bad:
    import { PrismaClient } from '../infrastructure/prisma'
    // Good:
    import { UserRepository } from '../domain/repositories'
```
