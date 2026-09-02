# Session Startup Routine Template

セッション開始時のチェックを実装するテンプレート。実装は2通りあり、ユーザーに選ばせる:

- **A. SessionStart hook 版（推奨）**: hook がスクリプトを自動実行し、stdout がコンテキストへ注入される。強制力があり、エージェントが手順を忘れない
- **B. CLAUDE.md 記述版**: CLAUDE.md に手順を書く。設定が単純で人間も読めるが、実行はエージェント任せ

選択基準: 確実性を取るなら A。チームの人間メンバーにも手順を見せたい・設定を最小にしたいなら B（併用も可）。

## A. SessionStart Hook 版（推奨）

以下を `.claude/scripts/hooks/session-startup.sh` として保存する（stdout がそのままコンテキストに入るため、出力は簡潔に保つ）:

```bash
#!/usr/bin/env bash
# SessionStart Hook: inject session startup context.
# stdout is added to the session context. Keep it short and fast (<10s).
set -uo pipefail

echo "## Session Startup Context"

echo "### Recent commits"
git log --oneline -5 2>/dev/null || echo "(not a git repo)"

echo "### Uncommitted changes"
git status --short 2>/dev/null | head -20

if [ -f .claude/harness-scorecard.md ]; then
  echo "### Harness scorecard"
  grep -E '^\- \*\*|^Generated' .claude/harness-scorecard.md | head -6
fi

# Project-specific quick checks (adjust per stack, keep fast):
# npm run typecheck --silent 2>&1 | tail -3
# python -m pytest --co -q 2>&1 | tail -1

exit 0
```

`.claude/settings.json` への登録（既存エントリとマージすること）:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/scripts/hooks/session-startup.sh"
          }
        ]
      }
    ]
  }
}
```

`$CLAUDE_PROJECT_DIR` はプロジェクトルートの絶対パスを指す環境変数。hook の実行時カレントディレクトリに依存しないよう、相対パスでの登録は避ける。

```bash
chmod +x .claude/scripts/hooks/session-startup.sh
```

## B. CLAUDE.md Section Template

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
