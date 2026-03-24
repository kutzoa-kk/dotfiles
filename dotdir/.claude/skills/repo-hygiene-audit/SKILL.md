---
name: repo-hygiene-audit
description: リポジトリの「ドキュメント腐敗」を監査する。コードから乖離した古い prose ドキュメントを検出し、agent が誤情報を信頼するリスクを低減。使用タイミング：(1)「audit docs」「stale documentation」「repo hygiene」「documentation rot」(2)「clean up docs」「find outdated docs」「ドキュメント整理」(3) agent がリポジトリの古い記述に基づいて誤った判断をした時 (4) リポジトリの定期メンテナンス。
---

# Repo Hygiene Audit

リポジトリ内のドキュメント腐敗（documentation rot）を検出・分類・修正提案するスキル。

## Background

> "Agents grep/find/cat the repo freely and treat discovered text as equally authoritative. They can't intuitively judge 'this is a 3-month-old memo'."
> "18 frontier models all showed performance degradation with increased context length. Stale/irrelevant info accumulation directly causes performance degradation."

Agent はリポジトリ内のテキストを等しく信頼する。古い prose ドキュメントが残っていると、agent の判断精度が低下する。このスキルはその腐敗を体系的に検出する。

## Workflow

### Step 1: Scan for rot candidates

以下のパターンでリポジトリをスキャンし、腐敗候補を収集する。

#### 1a: Prose ドキュメントの列挙

```bash
# Markdown prose docs
find . -name '*.md' -not -path './.git/*' -not -path './node_modules/*' \
  -not -path './vendor/*' -not -path './.venv/*'

# 特に注目するファイル
# README.md, ARCHITECTURE.md, DESIGN.md, CONTRIBUTING.md, docs/**/*.md
```

#### 1b: 長期未更新ファイルの検出

```bash
# 90日以上更新されていないファイルを検出
find . -name '*.md' -not -path './.git/*' -mtime +90 -type f
```

Git の最終コミット日も確認する：

```bash
# 各ファイルの最終コミット日を取得
git log -1 --format="%ci" -- <file_path>
```

#### 1c: 「現在の状態」を記述するファイルの検出

以下のパターンを含むファイルを重点的にチェック：

- `"currently"`, `"right now"`, `"at the moment"`, `"as of"`
- `"we use"`, `"we are using"`, `"our stack"`, `"our architecture"`
- `"v1."`, `"v2."` などバージョン番号を含むインラインコメント
- `"TODO"`, `"FIXME"`, `"HACK"` で日付が古いもの

```bash
# "current state" を示唆する表現を検索
grep -rn -E '(currently|right now|at the moment|as of|we use|we are using)' \
  --include='*.md' --exclude-dir='.git'
```

#### 1d: 壊れた内部リンクの検出

Markdown 内の相対リンクが実在するか確認：

```bash
# Markdown 内のリンク先を抽出して存在チェック
grep -oP '\[.*?\]\(\K[^)]+' <file> | while read link; do
  # URLは除外、相対パスのみチェック
  if [[ ! "$link" =~ ^https?:// ]] && [[ ! -e "$link" ]]; then
    echo "BROKEN: $link in <file>"
  fi
done
```

### Step 2: Classify each candidate

収集したファイルを以下のテーブルで分類する。詳細は [references/rot-patterns.md](references/rot-patterns.md) を参照。

| Type | Risk | Action |
|------|------|--------|
| **Executable artifact** (test, schema, type def, linter config) | Low | Keep -- breaks loudly when stale |
| **ADR** (Status + timestamp 付き) | Low | Keep -- agent が解析しやすい構造 |
| **Prose description** ("This system is...", "We use X for...") | High | Flag -- 静かに腐敗する |
| **API documentation** (手書きエンドポイント一覧) | High | Flag -- OpenAPI/型定義が source of truth |
| **Inline architecture overview** | Medium | Flag -- ADR またはテストに変換すべき |

**分類の判断基準**:

1. **ファイルが壊れたら CI が落ちるか？** → Yes なら executable artifact（Low risk）
2. **Status/Date フィールドがあるか？** → Yes なら ADR（Low risk）
3. **「現在の状態」を散文で記述しているか？** → Yes なら prose description（High risk）
4. **API エンドポイントを手動で列挙しているか？** → Yes なら API doc（High risk）
5. **アーキテクチャをインラインで説明しているか？** → Yes なら inline overview（Medium risk）

### Step 3: Generate report

以下の形式でレポートを生成する。

#### 3a: サマリーメトリクス

```markdown
## Audit Summary

| Metric | Value |
|--------|-------|
| Total Markdown files | N |
| Executable artifacts (low risk) | N |
| ADRs (low risk) | N |
| Prose docs (high risk) | N |
| API docs (high risk) | N |
| Inline overviews (medium risk) | N |
| Prose-to-executable ratio | N:M |
| Files >90 days old referencing "current" state | N |
| Broken internal links | N |
```

#### 3b: 個別ファイルレポート

フラグされた各ファイルについて：

```markdown
### <file_path>

- **Type**: Prose description | API documentation | Inline architecture overview
- **Last updated**: YYYY-MM-DD (N days ago)
- **Severity**: critical | warning | info
- **What it says**: <ファイルの主張の要約>
- **What code shows**: <実際のコードとの差異、検出できた場合>
- **Recommended action**: delete | convert to ADR | replace with pointer | convert to test
- **Rationale**: <理由>
```

**Severity の基準**:

| Severity | Condition |
|----------|-----------|
| **critical** | コードと明確に矛盾している（積極的に誤解を招く） |
| **warning** | 90日以上未更新で「現在の状態」を記述（おそらく stale） |
| **info** | 将来腐敗する可能性があるが、現時点では正確かもしれない |

### Step 4: Suggest remediation

各フラグファイルに対して具体的な修正アクションを提案する。

#### 4a: Prose description → Pointer に変換

散文の説明を、source of truth へのポインターに置き換える：

```markdown
# Before (rots silently)
## Database
We use PostgreSQL 14 with pgvector extension for vector search.
The connection pool is set to 20 connections max.

# After (self-maintaining)
## Database
- Schema: `db/schema.sql`
- Config: `config/database.yml`
- Migration history: `db/migrations/`
```

#### 4b: Decision → ADR に変換

意思決定の記録は ADR フォーマットに変換する。テンプレートは [references/adr-template.md](references/adr-template.md) を参照。

#### 4c: Specification → Test に変換

仕様の記述はテストに変換して、コードとの一致を CI で保証する：

```markdown
# Before (prose spec that rots)
"The API returns 429 when rate limit exceeded, with Retry-After header"

# After (executable spec)
test("returns 429 with Retry-After header when rate limited", ...)
```

#### 4d: 重複ドキュメント → 削除

設定ファイルやコードが既に同じ情報を持っている場合、prose ドキュメントは削除する：

```markdown
# Delete candidate: docs/linter-config.md
# Reason: .eslintrc.json is the source of truth, this doc duplicates it
```

## Tips

- **定期実行を推奨**: 月1回程度このスキルを実行し、腐敗の蓄積を防ぐ
- **CI 連携**: 壊れた内部リンクの検出は CI に組み込むと効果的
- **ADR の導入**: 初めて ADR を導入する場合、`docs/adr/` ディレクトリを作成し、`0001-record-architecture-decisions.md` から始める
- **Prose-to-executable ratio**: この比率が高いほど腐敗リスクが高い。目標は executable artifacts が prose docs を上回る状態
- **CLAUDE.md の監査**: CLAUDE.md 自体も腐敗対象。コマンド例やディレクトリ構造の記述が実態と一致するか確認する
