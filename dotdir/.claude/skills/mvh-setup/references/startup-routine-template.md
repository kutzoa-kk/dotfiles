# Session Startup Routine Template

セッション開始時に agent が実行すべきチェックリスト。CLAUDE.md に追加するセクションのテンプレート。

## CLAUDE.md Section Template

以下を CLAUDE.md の適切な位置に追加する。プロジェクトに合わせてコマンドを調整すること。

```markdown
## Session Startup

Run these checks at the start of every session before doing any work:

1. `git log --oneline -5` -- review recent changes
2. `git status` -- check for uncommitted work
3. `cat .claude/harness-scorecard.md` -- verify harness status
4. Verify build: `<build command>`
5. Review in-progress notes: `ls docs/wip/ TODO.md 2>/dev/null`
```

## Stack-Specific Templates

### TypeScript / JavaScript

```markdown
## Session Startup

Run these checks at the start of every session:

1. `git log --oneline -5` -- review recent changes
2. `git status` -- check for uncommitted work
3. `cat .claude/harness-scorecard.md` -- verify harness status
4. `npm run build` or `npm run typecheck` -- verify types
5. `npm test -- --run` -- quick test pass
6. Review in-progress notes: `ls docs/wip/ TODO.md 2>/dev/null`
```

### Python

```markdown
## Session Startup

Run these checks at the start of every session:

1. `git log --oneline -5` -- review recent changes
2. `git status` -- check for uncommitted work
3. `cat .claude/harness-scorecard.md` -- verify harness status
4. `python -m pytest --co -q` -- verify test collection (no execution)
5. `ruff check .` -- quick lint check
6. Review in-progress notes: `ls docs/wip/ TODO.md 2>/dev/null`
```

### Go

```markdown
## Session Startup

Run these checks at the start of every session:

1. `git log --oneline -5` -- review recent changes
2. `git status` -- check for uncommitted work
3. `cat .claude/harness-scorecard.md` -- verify harness status
4. `go build ./...` -- verify compilation
5. `go vet ./...` -- quick static analysis
6. Review in-progress notes: `ls docs/wip/ TODO.md 2>/dev/null`
```

### Rust

```markdown
## Session Startup

Run these checks at the start of every session:

1. `git log --oneline -5` -- review recent changes
2. `git status` -- check for uncommitted work
3. `cat .claude/harness-scorecard.md` -- verify harness status
4. `cargo check` -- verify compilation
5. `cargo clippy -- -D warnings` -- quick lint check
6. Review in-progress notes: `ls docs/wip/ TODO.md 2>/dev/null`
```

## Why Each Step Matters

| Step | Purpose |
|------|---------|
| `git log` | Agent が前回のセッション以降の変更を把握する。コンテキスト喪失を防ぐ |
| `git status` | 未コミットの変更がある場合、それを踏まえて作業する |
| Harness scorecard | セットアップ状況を把握し、未完了項目を意識する |
| Build / typecheck | 壊れた状態から作業を始めないことを保証する |
| Test (optional) | 既存のテスト失敗を把握してから新しい作業を始める |
| In-progress notes | 前回のセッションで中断した作業の引き継ぎ |

## Customization Guidelines

- **Dev server の確認が必要なプロジェクト**: `curl -s http://localhost:3000/health` 等を追加
- **Docker ベースのプロジェクト**: `docker compose ps` でサービス状態を確認
- **Monorepo**: 変更があったパッケージのみ確認する条件分岐を追加
- **CI との連携**: `gh run list --limit 3` で最近の CI 結果を確認

## Anti-Patterns

- **実行に時間がかかるコマンドを入れない** -- startup routine は 10 秒以内に完了すべき
- **全テストを実行しない** -- test collection (`--co`) や quick smoke test のみ。フルテストは Stop Hook に任せる
- **出力が膨大なコマンドを入れない** -- context window を圧迫する。`--quiet` フラグを活用
