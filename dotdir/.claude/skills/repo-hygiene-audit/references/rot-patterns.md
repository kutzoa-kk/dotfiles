# Rot Patterns -- 詳細分類ガイド

ドキュメント腐敗の分類パターンと検出方法の詳細リファレンス。

## Classification Matrix

### Low Risk: Executable Artifacts

CI や実行時に壊れたら即座に検知される成果物。

| Pattern | Examples | Why low risk |
|---------|----------|-------------|
| Test files | `*.test.*`, `*_test.*`, `*.spec.*` | テスト失敗で CI が落ちる |
| Schema definitions | `schema.sql`, `*.prisma`, `*.graphql` | マイグレーション/ビルドが壊れる |
| Type definitions | `*.d.ts`, `types.go`, `models.py` | コンパイルエラーになる |
| Linter/formatter config | `.eslintrc.*`, `pyproject.toml`, `.rubocop.yml` | lint 実行時にエラーになる |
| CI config | `.github/workflows/*`, `.gitlab-ci.yml` | パイプラインが失敗する |
| Package manifests | `package.json`, `go.mod`, `Cargo.toml` | ビルドが壊れる |
| OpenAPI/Swagger specs | `openapi.yaml`, `swagger.json` | 生成ツールが検知する（自動生成の場合） |

**判定基準**: ファイルの内容が不正確になったとき、自動化されたプロセス（CI, ビルド, テスト）が失敗するか？

### Low Risk: Well-Structured ADRs

ADR（Architecture Decision Records）は以下の構造を持つ場合に low risk：

```markdown
# Required fields for "safe" ADR
- Status: Accepted | Superseded by ADR-NNN | Deprecated
- Date: YYYY-MM-DD
```

**判定基準**:
- `Status` フィールドが存在するか
- `Date` フィールドが存在するか
- Status が明確な lifecycle を持つか（Accepted → Superseded → Deprecated）

**注意**: Status/Date がない「意思決定メモ」は ADR ではなく prose description として分類する。

### High Risk: Prose Descriptions

コードと独立して存在し、変更されても誰も気づかない散文。

| Pattern | Detection method |
|---------|-----------------|
| System overview | `grep -l "This system\|Our system\|The system is"` |
| Technology stack description | `grep -l "we use\|our stack\|built with\|powered by"` |
| Architecture narrative | `grep -l "architecture\|design\|how it works"` in non-ADR .md files |
| Setup instructions | `grep -l "getting started\|setup\|install"` with hardcoded versions |
| Team conventions | `grep -l "convention\|guideline\|best practice"` without enforcement |

**典型的な腐敗シナリオ**:

1. **README.md のセットアップ手順**: Node.js v18 と書いてあるが実際は v22 に移行済み
2. **ARCHITECTURE.md**: マイクロサービス構成図が2世代前
3. **docs/api.md**: 手書きのエンドポイント一覧が実際の routes と不一致
4. **CONTRIBUTING.md**: 古いブランチ戦略やレビュープロセスを記述

### High Risk: Hand-Written API Documentation

| Signal | What it means |
|--------|--------------|
| Endpoint lists in Markdown | 手動更新が必要 = 腐敗する |
| Request/response examples | コード変更で即座に古くなる |
| Parameter descriptions in prose | 型定義やバリデーションコードが source of truth |
| Status code tables | テストで保証すべき仕様 |

**Source of truth alternatives**:
- OpenAPI spec generated from code annotations
- Type definitions (`*.d.ts`, Pydantic models, Go structs)
- Integration tests that document behavior
- GraphQL schema (introspection)

### Medium Risk: Inline Architecture Overviews

ファイルやディレクトリの冒頭に書かれたアーキテクチャ概要。

| Signal | Example |
|--------|---------|
| File-header architecture comments | `// This module handles the authentication flow by...` |
| Directory README with flow descriptions | `src/auth/README.md` describing "how auth works" |
| Inline diagrams (ASCII art) | Flow charts that drift from actual code paths |
| Module-level docstrings describing "current" behavior | `"""This service currently uses Redis for caching..."""` |

**Why medium risk**: 開発者がファイルを編集するときにコメントに気づく可能性があるが、保証はない。

## Detection Heuristics

### Staleness Signals

ファイルが stale である可能性を示す信号：

| Signal | Command | Weight |
|--------|---------|--------|
| Last git commit >90 days | `git log -1 --format="%ci" -- <file>` | High |
| Contains "currently" / "right now" | `grep -c "currently\|right now"` | Medium |
| Contains hardcoded version numbers | `grep -cP "v\d+\.\d+"` | Medium |
| Contains dates >6 months old | `grep -cP "20\d{2}[-/](0[1-9]\|1[0-2])"` | Low-Medium |
| References deleted files/dirs | Check link targets existence | High |
| Describes behavior that contradicts tests | Cross-reference with test files | Critical |

### Freshness Signals

ファイルが fresh である可能性を示す信号（腐敗リスク低減）：

| Signal | Meaning |
|--------|---------|
| Last updated within 30 days | Active maintenance |
| Referenced in CI pipeline | Automated validation exists |
| Contains `<!-- auto-generated -->` | Tool-maintained |
| Has corresponding test file | Behavior is verified |
| Part of a build process | Breakage is detected |

### Cross-Reference Checks

コードとドキュメントの一致を検証する手法：

```bash
# 1. README のコマンド例が実際に動くか
grep -oP '`([a-z]+ [^`]+)`' README.md | while read cmd; do
  echo "Testing: $cmd"
done

# 2. ドキュメントが参照するファイルパスが存在するか
grep -oP '`([a-zA-Z_./-]+\.[a-z]+)`' docs/*.md | while read path; do
  [ ! -e "$path" ] && echo "Missing: $path"
done

# 3. パッケージ名・バージョンがマニフェストと一致するか
# (package.json, go.mod, Cargo.toml 等との突合)

# 4. 環境変数名がコードと一致するか
grep -oP '\$\{?\w+\}?' docs/*.md | sort -u > doc_vars.txt
grep -roP 'process\.env\.(\w+)\|os\.environ\[.(\w+).\]' src/ | sort -u > code_vars.txt
diff doc_vars.txt code_vars.txt
```

## Remediation Decision Tree

```
File flagged as potentially stale
  |
  +-- Does code/config already express this info?
  |     +-- Yes -> DELETE doc, add pointer comment if needed
  |     +-- No --+
  |              |
  +-- Is it a decision/rationale?
  |     +-- Yes -> CONVERT to ADR (see adr-template.md)
  |     +-- No --+
  |              |
  +-- Is it a specification/behavior?
  |     +-- Yes -> CONVERT to test
  |     +-- No --+
  |              |
  +-- Is it a "how to" guide?
  |     +-- Yes -> REPLACE with pointers to actual commands/configs
  |     +-- No --+
  |              |
  +-- Is it still valuable as context?
        +-- Yes -> CONVERT to ADR with Status: Accepted + Date
        +-- No  -> DELETE
```
