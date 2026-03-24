---
name: mvh-setup
description: >
  Minimum Viable Harness セットアップウィザード。プロジェクトに harness engineering のベストプラクティスを
  段階的に導入するオーケストレーションスキル。
  使用タイミング：(1)「set up harness」「harness engineering」、(2)「initialize project for Claude」、
  (3)「MVH」「minimum viable harness」、(4)「project setup for AI」、
  (5)「configure Claude Code for this project」、(6) 新規プロジェクトでベストプラクティスを導入したい場合、
  (7)「ハーネスセットアップ」「プロジェクト初期設定」。
  個別スキル（claude-md-generator, auto-format-hook, lint-config-guard, repo-hygiene-audit）を
  フェーズに沿って順序立てて実行し、ハーネススコアカードで進捗を可視化する。
---

# Minimum Viable Harness (MVH) Setup Wizard

プロジェクトに harness engineering のベストプラクティスをフェーズごとに導入するオーケストレーションスキル。

## Why This Exists

Harness の品質がベンチマークで 22 ポイントの差を生む一方、モデル交換は 1 ポイントしか変わらない。しかし harness 構築には多くのコンポーネントがあり、どこから始めるべきか分かりにくい。このスキルは段階的なフェーズに沿ってセットアップをガイドし、何が完了済みで何が未着手かをスコアカードで可視化する。

## Core Principles

1. **Non-destructive** -- 既存の設定は上書きしない。必ず確認してからマージする
2. **Incremental** -- 何度でも実行可能。前回の続きから再開できる
3. **Phased** -- Week 1 の基盤から始め、段階的に強化する
4. **Delegating** -- 専門スキルが存在するコンポーネントはそのスキルに委譲する

## Workflow

### Step 1: Project Analysis

プロジェクトルートをスキャンし、現在の状態を把握する。

```bash
# 言語・フレームワーク検出
ls package.json pyproject.toml go.mod Cargo.toml Gemfile build.gradle.kts Package.swift 2>/dev/null

# 既存 CLAUDE.md の確認
test -f CLAUDE.md && wc -l CLAUDE.md

# 既存 hooks の確認
test -f .claude/settings.json && cat .claude/settings.json
ls .claude/scripts/hooks/ 2>/dev/null

# ADR ディレクトリの確認
ls docs/adr/ docs/decisions/ adr/ 2>/dev/null

# Pre-commit hooks の確認
ls lefthook.yml lefthook-local.yml .husky/ 2>/dev/null

# テストコマンドの確認
# package.json の scripts.test, Makefile の test ターゲット等を確認

# CI 設定の確認
ls .github/workflows/ .gitlab-ci.yml Jenkinsfile 2>/dev/null

# ハーネススコアカードの確認（前回の実行結果）
test -f .claude/harness-scorecard.md && cat .claude/harness-scorecard.md
```

以下の項目の状態を判定する:

| Component | 判定方法 |
|-----------|----------|
| CLAUDE.md | ファイル存在 + 50行以下か |
| PostToolUse auto-format | `.claude/settings.json` に PostToolUse hook があるか |
| Linter config protection | `.claude/scripts/hooks/lint-config-guard.sh` があるか |
| ADR directory | `docs/adr/` 等が存在し ADR-0001 があるか |
| Stop Hook (test gate) | `.claude/settings.json` に Stop hook があるか |
| Session startup routine | `.claude/settings.json` に startup 設定があるか、または CLAUDE.md にセッション開始手順があるか |
| Pre-commit hooks | `lefthook.yml` または `.husky/` が存在するか |
| Repo hygiene | 最近の audit 結果があるか |

### Step 2: Phase Selection

分析結果をフェーズ別に表示し、ユーザーに選択させる。

表示フォーマット:

```
## Current Harness Status

### Week 1 -- Foundation
1. [✅] CLAUDE.md (37 lines, pointer-based)
2. [⬜] PostToolUse auto-format -- Run /auto-format-hook
3. [⬜] Linter config protection -- Run /lint-config-guard
4. [⬜] ADR-0001 (harness engineering decision)

### Week 2-4 -- Reinforcement
5. [⬜] Repo hygiene audit -- Run /repo-hygiene-audit
6. [⬜] Stop Hook (test gate before completion)
7. [⬜] Session startup routine
8. [⬜] Pre-commit hooks (Lefthook / Husky)

### Month 2-3 -- Advanced
9.  [⬜] Custom lint rules
10. [⬜] Garbage collection schedule
11. [⬜] PreToolUse safety gates

Which items would you like to set up? (e.g., "1-4" for all Week 1, or "2,3,6")
```

### Step 3: Execute Selected Items

選択された各項目を順に実行する。

#### Item 1: CLAUDE.md Generation

**既存スキルに委譲する。**

ユーザーに伝える: "Run `/claude-md-generator` to create a lean, pointer-based CLAUDE.md (under 50 lines)."

既に CLAUDE.md が存在し 50 行以下なら、スキップして OK と伝える。50 行超なら slim mode を提案する。

#### Item 2: PostToolUse Auto-Format

**既存スキルに委譲する。**

ユーザーに伝える: "Run `/auto-format-hook` to detect your stack and set up auto-formatting hooks."

#### Item 3: Linter Config Protection

**既存スキルに委譲する。**

ユーザーに伝える: "Run `/lint-config-guard` to protect linter configs from agent tampering."

#### Item 4: First ADR (ADR-0001)

**直接生成する。** 以下の内容で ADR-0001 を作成:

```bash
mkdir -p docs/adr
```

ADR-0001 の内容:

```markdown
# ADR-0001: Adopt Harness Engineering Practices

## Status

Accepted

## Date

<today's date>

## Context

AI coding agents (Claude Code, etc.) perform significantly better when guided by
a well-structured harness: CLAUDE.md, PostToolUse hooks, linter protection, and
completion gates. Research shows harness quality causes a 22-point benchmark swing,
while model choice causes only 1 point of difference.

Without a harness, agents drift: they forget to format, weaken lint rules to silence
errors, skip tests, and produce inconsistent output across sessions.

## Decision

We adopt harness engineering as a core development practice for this project:

1. **CLAUDE.md** -- lean, pointer-based (under 50 lines), no prose duplication
2. **PostToolUse hooks** -- auto-format and lint after every file edit
3. **Linter config protection** -- PreToolUse hook blocks agent from modifying lint configs
4. **Stop Hook** -- test suite must pass before agent declares "done"
5. **Pre-commit hooks** -- same linters enforced at commit time
6. **Periodic hygiene audits** -- prevent documentation rot

## Consequences

- Agents produce consistently formatted, lint-clean code
- Quality gates cannot be circumvented by the agent
- New team members (human or AI) onboard faster with clear CLAUDE.md pointers
- Slightly more initial setup time, offset by fewer review cycles
```

**重要**: 既に `docs/adr/ADR-0001*` が存在する場合は上書きしない。次の番号 (ADR-0002 等) で作成するか、ユーザーに確認する。

#### Item 5: Repo Hygiene Audit

**既存スキルに委譲する。**

ユーザーに伝える: "Run `/repo-hygiene-audit` to find and fix documentation rot."

#### Item 6: Stop Hook (Test Gate)

**直接生成する。** テンプレートは [references/stop-hook-template.md](./references/stop-hook-template.md) を参照。

生成するファイル:
- `.claude/scripts/hooks/stop-test-gate.sh` -- テスト実行スクリプト
- `.claude/settings.json` への Stop hook エントリ追加

Stop hook の登録:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/scripts/hooks/stop-test-gate.sh"
          }
        ]
      }
    ]
  }
}
```

**重要**: 既存の `settings.json` がある場合はマージする。

#### Item 7: Session Startup Routine

**直接生成する。** テンプレートは [references/startup-routine-template.md](./references/startup-routine-template.md) を参照。

CLAUDE.md に以下のセクションを追加する（既に存在しなければ）:

```markdown
## Session Startup

Every session, run these checks before starting work:
1. `git log --oneline -5` -- understand recent changes
2. `cat .claude/harness-scorecard.md` -- check harness status
3. Verify dev server / build works
4. Read any in-progress notes in `docs/` or `TODO.md`
```

#### Item 8: Pre-commit Hooks

**Lefthook をセットアップする。**

Lefthook がインストールされていない場合はインストールを案内する。

`lefthook.yml` が存在しなければ、stack に応じたテンプレートを生成する:

```yaml
# See https://github.com/evilmartians/lefthook
pre-commit:
  parallel: true
  commands:
    # Uncomment and adjust for your stack:
    # lint:
    #   glob: "*.{ts,tsx,js,jsx}"
    #   run: npx biome check --write {staged_files}
    #   stage_fixed: true
    # format:
    #   glob: "*.{ts,tsx,js,jsx}"
    #   run: npx biome format --write {staged_files}
    #   stage_fixed: true
    # typecheck:
    #   run: npx tsc --noEmit

pre-push:
  commands:
    test:
      run: echo "Add your test command here"
```

Stack に応じてコマンドを調整する。既に `lefthook.yml` や `.husky/` が存在する場合はスキップ。

#### Items 9-11: Advanced (Month 2-3)

これらは高度な項目。ユーザーが選択した場合はガイダンスを提供するが、自動生成はしない:

- **Item 9: Custom lint rules** -- プロジェクト固有のルールを作成するガイダンスを提供。ESLint custom rules, Ruff custom rules, clippy lints 等。
- **Item 10: Garbage collection schedule** -- `.claude/harness-scorecard.md` に次回監査日を記録し、CLAUDE.md に定期監査のリマインダーを追加。
- **Item 11: PreToolUse safety gates** -- 破壊的コマンド（`rm -rf`, `git reset --hard` 等）をブロックする PreToolUse hook のガイダンスを提供。

### Step 4: Generate Harness Scorecard

全項目の実行後、スコアカードを生成して `.claude/harness-scorecard.md` に保存する。

```bash
mkdir -p .claude
```

スコアカードのフォーマット:

```markdown
# Harness Scorecard

Generated: <date>
Project: <project name from package.json or directory name>

## Status

| # | Component | Phase | Status | Details |
|---|-----------|-------|--------|---------|
| 1 | CLAUDE.md (<=50 lines) | Week 1 | ✅ Done | 37 lines, pointer-based |
| 2 | PostToolUse auto-format | Week 1 | ✅ Done | Biome + Oxlint |
| 3 | Linter config protection | Week 1 | ⬜ Not set | Run /lint-config-guard |
| 4 | ADR directory | Week 1 | ✅ Done | ADR-0001 created |
| 5 | Repo hygiene audit | Week 2-4 | ⬜ Not audited | Run /repo-hygiene-audit |
| 6 | Stop Hook (test gate) | Week 2-4 | ⬜ Not set | Needs test command |
| 7 | Session startup routine | Week 2-4 | ⬜ Not set | Add to CLAUDE.md |
| 8 | Pre-commit hooks | Week 2-4 | ✅ Done | Lefthook configured |
| 9 | Custom lint rules | Month 2-3 | ⬜ Not set | Advanced |
| 10 | Garbage collection | Month 2-3 | ⬜ Not set | Advanced |
| 11 | PreToolUse safety gates | Month 2-3 | ⬜ Not set | Advanced |

## Score

- **Week 1 (Foundation)**: 3/4
- **Week 2-4 (Reinforcement)**: 1/4
- **Month 2-3 (Advanced)**: 0/3
- **Total**: 4/11

## Next Steps

1. Run `/lint-config-guard` to protect linter configs
2. Set up Stop Hook after configuring test command
3. Add session startup routine to CLAUDE.md

## Audit History

- <date>: Initial MVH setup (score 4/11)
```

**重要**: 既存のスコアカードがある場合は、Audit History に前回の記録を残しつつ更新する。

## File Output Summary

このスキルが直接生成する可能性のあるファイル:

| File | Purpose | When |
|------|---------|------|
| `docs/adr/ADR-0001-adopt-harness-engineering.md` | First ADR | Item 4 selected |
| `.claude/scripts/hooks/stop-test-gate.sh` | Stop Hook script | Item 6 selected |
| `.claude/settings.json` (updated) | Hook registration | Items 6, 7 |
| `CLAUDE.md` (updated) | Startup routine section | Item 7 selected |
| `lefthook.yml` | Pre-commit hook config | Item 8 selected |
| `.claude/harness-scorecard.md` | Progress tracking | Always (Step 4) |

## References

- [Phase checklist with acceptance criteria](./references/phase-checklist.md)
- [Stop Hook script template](./references/stop-hook-template.md)
- [Session startup routine template](./references/startup-routine-template.md)

## Important Notes

- スコアカードは `.claude/harness-scorecard.md` に永続化される。次回セッションでの進捗確認に使用する
- 委譲先スキルの具体的な実装内容はそのスキルの SKILL.md を参照すること。このスキルはオーケストレーションのみを担当する
- 既存の設定ファイルは必ずマージする。上書きは禁止
- ユーザーが「全部やって」と言った場合は Week 1 (Items 1-4) から開始し、完了後に Week 2-4 へ進むか確認する
