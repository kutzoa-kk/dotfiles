---
name: mvh-setup
description: >
  Minimum Viable Harness セットアップウィザード。プロジェクトに harness engineering のベストプラクティスを
  段階的に導入するオーケストレーションスキル。
  使用タイミング：(1)「set up harness」「harness engineering」、(2)「initialize project for Claude」、
  (3)「MVH」「minimum viable harness」、(4)「project setup for AI」、
  (5)「configure Claude Code for this project」、(6) 新規プロジェクトでベストプラクティスを導入したい場合、
  (7)「ハーネスセットアップ」「プロジェクト初期設定」、
  (8) ECC プラグイン稼働環境で、プロジェクト側にコミット可能な harness（CLAUDE.md / hooks / ADR /
  pre-commit）を整備したい場合。
---

# Minimum Viable Harness (MVH) Setup Wizard

プロジェクトに harness engineering のベストプラクティスをフェーズごとに導入するオーケストレーションスキル。

## Why This Exists

エージェントの成果はモデル単体ではなく harness（CLAUDE.md・hooks・完了ゲート・pre-commit）の質に大きく左右される。community の SWE-bench 分析では「同一モデルでも harness の交換でスコアが約 22 ポイント動く一方、モデルの交換では約 1 ポイントしか変わらない」という報告がある（Anthropic 公式の一次出典は未確認。数値は目安として扱い、断定引用しない）。

harness には多くのコンポーネントがあり、どこから始めるべきか分かりにくい。このスキルは段階的なフェーズに沿ってセットアップをガイドし、何が完了済みで何が未着手かをスコアカードで可視化する。

ECC プラグイン等のグローバル hooks が稼働する環境では、その充足分を検出して二重導入を避ける。mvh-setup の固有価値は「**プロジェクトにコミットでき、チームで共有できる成果物**」（CLAUDE.md・ADR・lefthook.yml・プロジェクト hooks）を作ることにある。グローバル hooks は個人環境にしか存在しない。

## Core Principles

1. **Non-destructive** -- 既存の設定は上書きしない。必ず確認してからマージする
2. **Incremental** -- 何度でも実行可能。前回の続きから再開できる
3. **Phased** -- Week 1 の基盤から始め、段階的に強化する
4. **Delegating** -- 専門スキルが存在するコンポーネントはそのスキルに委譲する
5. **ECC-aware** -- グローバル（ECC hooks 等）で既に満たされている項目はプロジェクトへ再導入せず、スコアカードに「✳️ グローバル充足」と記録する。ただしチーム共有が要件の場合はプロジェクト版を優先する。詳細は [references/ecc-coexistence.md](./references/ecc-coexistence.md)

## Workflow

### Step 0: 実行環境の注意（GateGuard 稼働時）

ECC の Fact-Forcing Gate（GateGuard）が有効な環境では、**ファイルごとの初回 Edit/Write と初回 Bash がブロックされる**（新規ファイルの Write は必ず対象。Step 1 の分析コマンドも初手でブロックされ得る）。このスキルはファイルを複数生成するため、各生成の直前に「参照元 / 同目的の既存ファイルの不在 / データ構造 / ユーザー指示の原文」を先に提示してから Write すること。ブロックされた場合は事実を提示して同じ操作を再試行すれば通る。対処テンプレートは [references/ecc-coexistence.md](./references/ecc-coexistence.md) を参照。

### Step 1: Project Analysis

プロジェクトルートをスキャンし、現在の状態を把握する。

```bash
# 言語・フレームワーク検出
ls package.json pyproject.toml go.mod Cargo.toml Gemfile build.gradle.kts Package.swift 2>/dev/null

# 既存 CLAUDE.md / AGENTS.md の確認
test -f CLAUDE.md && wc -l CLAUDE.md
test -f AGENTS.md && wc -l AGENTS.md

# 既存 hooks / permissions の確認
test -f .claude/settings.json && cat .claude/settings.json
ls .claude/scripts/hooks/ 2>/dev/null

# ECC プラグインの検出（グローバル hooks の充足判定に使う）
grep -o '"ecc@ecc"[^,}]*' ~/.claude/settings.json 2>/dev/null

# ADR ディレクトリの確認
ls docs/adr/ docs/decisions/ adr/ 2>/dev/null

# Pre-commit hooks の確認
ls lefthook.yml lefthook-local.yml .husky/ 2>/dev/null

# テストコマンドの確認（Item 6 の導入可否に直結）
grep -o '"test"[[:space:]]*:[[:space:]]*"[^"]*"' package.json 2>/dev/null
grep -E '^test:' Makefile 2>/dev/null

# CI 設定の確認
ls .github/workflows/ .gitlab-ci.yml Jenkinsfile 2>/dev/null

# ハーネススコアカードの確認（前回の実行結果）
test -f .claude/harness-scorecard.md && cat .claude/harness-scorecard.md
```

以下の12項目の状態を判定する（番号は Step 2 の表示・スコアカードと対応。各項目の詳細な受け入れ基準は [references/phase-checklist.md](./references/phase-checklist.md) を参照）:

| # | Component | 判定方法 | ECC 稼働時の充足 |
|---|-----------|----------|------------------|
| 1 | CLAUDE.md | ファイル存在 + pointer-based + 250 行以下か | なし（プロジェクト固有） |
| 2 | PostToolUse auto-format | `.claude/settings.json` に PostToolUse hook があるか | `stop:format-typecheck` / `quality-gate` が完全代替（✳️） |
| 3 | Linter config protection | `.claude/scripts/hooks/lint-config-guard.sh` があるか | `pre:config-protection` が完全代替（✳️・**二重導入注意**） |
| 4 | ADR directory | `docs/adr/` 等が存在し最初の ADR があるか | なし（プロジェクト固有） |
| 5 | Repo hygiene | audit 記録があるか（`grep -qi hygiene .claude/harness-scorecard.md`） | なし |
| 6 | Stop Hook (test gate) | `.claude/settings.json` に Stop hook があるか | `verification-loop` は部分代替（⬜ のまま） |
| 7 | Session startup routine | SessionStart hook があるか、または CLAUDE.md にセッション開始手順があるか | `session:start` は部分代替（⬜ のまま） |
| 8 | Pre-commit hooks | `lefthook.yml` または `.husky/` が存在するか | なし（git hook は ECC 対象外） |
| 9 | Custom lint rules | プロジェクト固有 lint ルールの有無 | なし |
| 10 | Periodic audit schedule | スコアカードに次回監査日があるか | `config-gc` は個人環境側のみ（部分） |
| 11 | Safety gates | `permissions.deny` または PreToolUse hook の有無 | `safety-guard` 等が代替（✳️ になり得る） |
| 12 | ECC 運用への接続 | スコアカードに harness-audit 導線があるか | ECC 環境のみ対象（非 ECC は N/A） |

判定ルール:

- **✳️ グローバル充足は「完全代替」のみ**。「部分代替」の項目は ⬜ のままにし、スコアカードの Details に部分代替の旨を記す
- ECC が有効（`"ecc@ecc": true`）な場合、**Step 2 の表示前に**「このプロジェクトはチームで共有しますか」を確認する。チーム共有なら ✳️ を使わず全項目を ⬜/✅ で判定する（他メンバーの環境に ECC はない前提。詳細は [references/ecc-coexistence.md](./references/ecc-coexistence.md)）

### Step 2: Phase Selection

分析結果をフェーズ別に表示し、ユーザーに選択させる。

表示フォーマット:

```
## Current Harness Status

### Week 1 -- Foundation
1. [✅] CLAUDE.md (120 lines, pointer-based) / AGENTS.md 層化は未設定
2. [✳️] PostToolUse auto-format -- ECC quality-gate で充足（チーム共有するなら /auto-format-hook）
3. [✳️] Linter config protection -- ECC pre:config-protection で充足
4. [⬜] ADR-0001 (harness engineering decision)

### Week 2-4 -- Reinforcement
5. [⬜] Repo hygiene audit -- Run /repo-hygiene-audit
6. [⬜] Stop Hook (test gate before completion)
7. [⬜] Session startup routine
8. [⬜] Pre-commit hooks (Lefthook / Husky)

### Month 2-3 -- Advanced
9.  [⬜] Custom lint rules
10. [⬜] Periodic audit schedule
11. [⬜] Safety gates (permissions.deny / PreToolUse)
12. [⬜] ECC 運用への接続（ECC 環境のみ）

Which items would you like to set up? (e.g., "1-4" for all Week 1, or "2,3,6")
```

### Step 3: Execute Selected Items

選択された各項目を順に実行する。

#### Item 1: CLAUDE.md Generation (+ AGENTS.md 層化)

**既存スキルに委譲する。**

ユーザーに伝える: "Run `/claude-md-generator` to create a lean, pointer-based CLAUDE.md."

判定基準: **pointer-based かつ 250 行以下**なら OK（常時ロードされるためコンテキスト予算を意識する。生成時は claude-md-generator の lean 方針＝50 行前後を目標にしつつ、既存ファイルの受け入れ上限は 250 行）。250 行超なら slim 化を提案する。

**AGENTS.md 層化（オプション）**: Claude Code 以外のエージェント（Codex 等）も使うプロジェクトでは、エージェント共通ルールを `AGENTS.md` に置き、CLAUDE.md には Claude 固有の内容とポインタのみを残す層化を提案する。既に AGENTS.md がある場合は重複記述がないか確認する。層化はスコア外のオプションで、Item 1 の ✅/⬜ は CLAUDE.md のみで判定する。

#### Item 2: PostToolUse Auto-Format

**既存スキルに委譲する。** ECC 稼働時はスキップ可（`quality-gate` / `stop:format-typecheck` が既にグローバルで動作）。**チームでフォーマット強制を共有したい場合のみ**プロジェクト版を導入する。

ユーザーに伝える: "Run `/auto-format-hook` to detect your stack and set up auto-formatting hooks."

#### Item 3: Linter Config Protection

**既存スキルに委譲する。** ECC 稼働時は `pre:config-protection` が既に同じ保護を提供しているため、プロジェクト導入すると**二重ガード**になる。原則スキップし「✳️ グローバル充足」とする。チーム共有が要件の場合のみ導入する。

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
completion gates.

Without a harness, agents drift: they forget to format, weaken lint rules to silence
errors, skip tests, and produce inconsistent output across sessions.

## Decision

We adopt harness engineering as a core development practice for this project:

1. **CLAUDE.md** -- lean, pointer-based, no prose duplication
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

**現行仕様の要点**: ブロックは **exit 2**（stderr の内容がフィードバックとして Claude に渡る）。exit 1 は「エラーだが処理続行」でありブロックにならない。入力 JSON の `stop_hook_active` を確認して無限ループを防ぐこと。詳細と JSON 出力による代替はテンプレート参照。

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
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/scripts/hooks/stop-test-gate.sh"
          }
        ]
      }
    ]
  }
}
```

**高度な代替**: hooks は `command` 以外に `prompt`（モデル1回評価）/ `agent`（ツール付きサブエージェント判定）型も使える。「テストが通ったか」を越えて「タスクの完了条件を満たしたか」を判定させたい場合は `agent` 型を検討する（設定は公式 hooks リファレンス参照）。

**重要**: 既存の `settings.json` がある場合はマージする。

#### Item 7: Session Startup Routine

**直接生成する。** テンプレートは [references/startup-routine-template.md](./references/startup-routine-template.md) を参照。2通りの実装があり、ユーザーに選ばせる:

- **A. SessionStart hook 版（推奨）**: `.claude/settings.json` の SessionStart hook でスクリプトを自動実行し、結果をコンテキストへ注入する。強制力があり、エージェントが手順を忘れない
- **B. CLAUDE.md 記述版**: CLAUDE.md に手順を書く。設定が単純で人間も読めるが、実行はエージェント任せ

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

#### Items 9-12: Advanced (Month 2-3)

これらは高度な項目。ユーザーが選択した場合はガイダンスを提供するが、自動生成はしない:

- **Item 9: Custom lint rules** -- プロジェクト固有のルールを作成するガイダンスを提供。`/custom-lint-rules` スキルがあれば委譲。ESLint custom rules, Ruff custom rules, clippy lints 等
- **Item 10: Periodic audit schedule** -- `.claude/harness-scorecard.md` に次回監査日を記録し、CLAUDE.md に定期監査のリマインダーを追加。自動化手段として Claude Code 本体の `/skill-doctor`（スキル・プラグイン診断。提供されていない環境では `ecc:skill-health` で代替）、ECC 環境では `config-gc`（`~/.claude` の定期掃除）も案内する
- **Item 11: Safety gates** -- 破壊的コマンドの防止。**第一候補は `settings.json` の `permissions.deny` ルール**（宣言的でメンテが楽）。パターンでは表せない判定が必要な場合のみ PreToolUse hook を書く。ECC 環境では `safety-guard` 等が既に同役割を担っていないか確認し、重複するなら「✳️ グローバル充足」とする
- **Item 12: ECC 運用への接続（ECC 環境のみ）** -- セットアップ完了後の継続運用を ECC 側へ引き継ぐ。`/ecc:harness-audit`（42 チェックの決定論採点。本スキルのスコアカードより計測が厳密）を定期実行に据え、コンテキスト予算の監査（ECC context-budget スキル）も案内する

### Step 4: Generate Harness Scorecard

全項目の実行後、スコアカードを生成して `.claude/harness-scorecard.md` に保存する。

```bash
mkdir -p .claude
```

ステータスは3値: ✅ Done / ⬜ Not set / ✳️ Global（ECC 等のグローバル hooks で充足。プロジェクト成果物としては存在しない）。

スコアカードのフォーマット:

```markdown
# Harness Scorecard

Generated: <date>
Project: <project name from package.json or directory name>

## Status

| # | Component | Phase | Status | Details |
|---|-----------|-------|--------|---------|
| 1 | CLAUDE.md (pointer-based, <=250 lines) | Week 1 | ✅ Done | 120 lines |
| 2 | PostToolUse auto-format | Week 1 | ✳️ Global | ECC quality-gate |
| 3 | Linter config protection | Week 1 | ✳️ Global | ECC pre:config-protection |
| 4 | ADR directory | Week 1 | ✅ Done | ADR-0001 created |
| 5 | Repo hygiene audit | Week 2-4 | ⬜ Not audited | Run /repo-hygiene-audit |
| 6 | Stop Hook (test gate) | Week 2-4 | ⬜ Not set | Needs test command |
| 7 | Session startup routine | Week 2-4 | ⬜ Not set | SessionStart hook 推奨 |
| 8 | Pre-commit hooks | Week 2-4 | ✅ Done | Lefthook configured |
| 9 | Custom lint rules | Month 2-3 | ⬜ Not set | Advanced |
| 10 | Periodic audit schedule | Month 2-3 | ⬜ Not set | Advanced |
| 11 | Safety gates | Month 2-3 | ⬜ Not set | permissions.deny 推奨 |
| 12 | ECC 運用への接続 | Month 2-3 | ⬜ Not set | ECC 環境のみ |

## Score

- **Week 1 (Foundation)**: 4/4 (うちグローバル充足 2)
- **Week 2-4 (Reinforcement)**: 1/4
- **Month 2-3 (Advanced)**: 0/4
- **Total**: 5/12

## Next Steps

1. Set up Stop Hook after configuring test command
2. Add SessionStart startup hook
3. Run /repo-hygiene-audit

## Audit History

- <date>: Initial MVH setup (score 5/12)
```

✳️ Global はスコア上「充足」として数えるが、Details にグローバル充足である旨を必ず残す（チーム共有が必要になったときの見直し対象）。部分代替（`verification-loop` / `session:start` 等）は ⬜ のままにし、Details に「ECC が部分代替」と記す。**非 ECC 環境では Item 12 を N/A** とし、分母を 11 で表記する（例: `Total: 5/11`）。

**ECC 環境では**、このスコアカードに加えて `/ecc:harness-audit` の実行を案内する（rubric 固定の決定論チェックで、本スキルの判定より厳密。役割分担: mvh-setup=導入ウィザード、harness-audit=採点器）。

**重要**: 既存のスコアカードがある場合は、Audit History に前回の記録を残しつつ更新する。

## File Output Summary

このスキルが直接生成する可能性のあるファイル:

| File | Purpose | When |
|------|---------|------|
| `docs/adr/ADR-0001-adopt-harness-engineering.md`（既存 ADR があれば次番号で同形式に命名） | First ADR | Item 4 selected |
| `.claude/scripts/hooks/stop-test-gate.sh` | Stop Hook script | Item 6 selected |
| `.claude/scripts/hooks/session-startup.sh` | SessionStart script | Item 7-A selected |
| `.claude/settings.json` (updated) | Hook registration | Items 6, 7 |
| `CLAUDE.md` (updated) | Startup routine section | Item 7-B selected |
| `AGENTS.md` (new/updated) | エージェント共通ルール | Item 1 で層化選択時 |
| `lefthook.yml` | Pre-commit hook config | Item 8 selected |
| `.claude/harness-scorecard.md` | Progress tracking | Always (Step 4) |

## References

- [Phase checklist with acceptance criteria](./references/phase-checklist.md)
- [Stop Hook script template](./references/stop-hook-template.md)
- [Session startup routine template](./references/startup-routine-template.md)
- [ECC 共存ガイド（検出・充足判定・GateGuard 対処）](./references/ecc-coexistence.md)

## Important Notes

- スコアカードは `.claude/harness-scorecard.md` に永続化される。次回セッションでの進捗確認に使用する
- 委譲先スキルの具体的な実装内容はそのスキルの SKILL.md を参照すること。このスキルはオーケストレーションのみを担当する
- 既存の設定ファイルは必ずマージする。上書きは禁止
- ✳️ グローバル充足の判定は環境依存（その個人環境でしか成立しない）。チーム開発のプロジェクトでは、グローバル充足に頼らずプロジェクト成果物を優先するようユーザーに確認する
- ユーザーが「全部やって」と言った場合は Week 1 (Items 1-4) から開始し、完了後に Week 2-4 へ進むか確認する
