# Stop Hook Template -- Test Gate

Agent がタスク完了を宣言する前にテストスイートを実行し、失敗があれば完了をブロックする Stop Hook。

## 現行仕様の要点（重要）

- **ブロックは exit 2**。stderr に書いた内容がフィードバックとして Claude に渡り、作業が継続される
- **exit 1 はブロックにならない**（「エラーだが処理続行」扱い）。旧テンプレートは exit 1 を使っており機能しなかった
- Stop hook は stdin から入力 JSON を受け取る。`stop_hook_active: true` のときは「既に Stop hook のブロックによって継続中」を意味するので、**exit 0 で通過させて無限ループを防ぐ**
- exit 2 の代替として、exit 0 + stdout への JSON 出力（`{"decision": "block", "reason": "..."}`）でもブロックできる（後述）

## Script Template

以下を `.claude/scripts/hooks/stop-test-gate.sh` として保存する。

```bash
#!/usr/bin/env bash
# Stop Hook: Test Gate
# Runs the project's test suite before allowing the agent to declare "done".
# Exit 0 = allow stop. Exit 2 = block stop (stderr is fed back to the agent).

set -uo pipefail

##############################################################################
# Loop prevention
##############################################################################

# Hook input JSON arrives on stdin. If stop_hook_active is true, a previous
# run of this hook already blocked once and the agent is continuing because
# of it -- allow the stop now to avoid an infinite block loop.
HOOK_INPUT=$(cat 2>/dev/null || true)
if printf '%s' "$HOOK_INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

##############################################################################
# Configuration -- adjust these for your project
##############################################################################

# Auto-detect test command based on project files
detect_test_command() {
  if [ -f "package.json" ]; then
    # Check for test script in package.json
    if grep -q '"test"' package.json 2>/dev/null; then
      echo "npm test"
      return
    fi
    # Check for vitest
    if grep -q '"vitest"' package.json 2>/dev/null; then
      echo "npx vitest run"
      return
    fi
    # Check for jest
    if grep -q '"jest"' package.json 2>/dev/null; then
      echo "npx jest"
      return
    fi
  fi

  if [ -f "pyproject.toml" ]; then
    if grep -q 'pytest' pyproject.toml 2>/dev/null; then
      echo "python -m pytest"
      return
    fi
  fi

  if [ -f "go.mod" ]; then
    echo "go test ./..."
    return
  fi

  if [ -f "Cargo.toml" ]; then
    echo "cargo test"
    return
  fi

  if [ -f "Makefile" ] && grep -q '^test:' Makefile 2>/dev/null; then
    echo "make test"
    return
  fi

  # No test command found
  echo ""
}

# Override: set TEST_CMD environment variable to skip auto-detection
TEST_CMD="${TEST_CMD:-$(detect_test_command)}"

# Maximum time for tests (seconds). Prevents infinite hangs.
TEST_TIMEOUT="${TEST_TIMEOUT:-300}"

##############################################################################
# Main
##############################################################################

# If no test command was detected, warn but allow stop
if [ -z "$TEST_CMD" ]; then
  cat <<'MSG'
WARNING: No test command detected.
Configure by either:
  1. Adding a "test" script to package.json / Makefile / pyproject.toml
  2. Setting TEST_CMD environment variable
  3. Editing this script directly

Allowing stop without running tests.
MSG
  exit 0
fi

echo "Running test gate: $TEST_CMD"
echo "Timeout: ${TEST_TIMEOUT}s"
echo "---"

# Run tests with timeout when available, capture output.
# (Stock macOS lacks GNU timeout; without this guard "command not found"
#  would be misreported as a test failure and wrongly block the stop.)
TEST_EXIT=0
if command -v timeout >/dev/null 2>&1; then
  TEST_OUTPUT=$(timeout "$TEST_TIMEOUT" bash -c "$TEST_CMD" 2>&1) || TEST_EXIT=$?
else
  TEST_OUTPUT=$(bash -c "$TEST_CMD" 2>&1) || TEST_EXIT=$?
fi

if [ "$TEST_EXIT" -eq 0 ]; then
  echo "All tests passed. OK to complete."
  exit 0
fi

# Tests failed -- block stop (exit 2) and feed the failure back via stderr
cat >&2 <<MSG
BLOCKED: Tests are failing. Fix them before completing the task.

Test command: $TEST_CMD
Exit code: $TEST_EXIT

Output (last 50 lines):
---
$(echo "$TEST_OUTPUT" | tail -50)
---

Fix the failing tests, then try completing again.
MSG

exit 2
```

## Installation

```bash
mkdir -p .claude/scripts/hooks
cp stop-test-gate.sh .claude/scripts/hooks/stop-test-gate.sh
chmod +x .claude/scripts/hooks/stop-test-gate.sh
```

## settings.json Registration

`.claude/settings.json` に以下を追加（既存エントリとマージすること）:

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

`$CLAUDE_PROJECT_DIR` はプロジェクトルートの絶対パスを指す環境変数。hook の実行時カレントディレクトリはプロジェクトルートである保証がないため、相対パスでの登録は避ける。

## JSON 出力によるブロック（代替方式）

exit code の代わりに、exit 0 のまま stdout へ JSON を出力して構造化された判断を返すこともできる:

```json
{
  "decision": "block",
  "reason": "Tests are failing: npm test exited with code 1. Fix before completing."
}
```

`jq` 等で複雑な理由文を組み立てたい場合や、他の hook 出力（`continue` / `stopReason` / `systemMessage`）と組み合わせたい場合はこちらを使う。単純なテストゲートなら exit 2 + stderr で十分。

## Customization

### Test Command Override

環境変数でテストコマンドを上書きできる:

```bash
export TEST_CMD="npm run test:ci"
```

### Timeout

デフォルトは 300 秒（5 分）。変更する場合:

```bash
export TEST_TIMEOUT=600
```

### Specific Test Suites

特定のテストスイートのみ実行したい場合は、スクリプト内の `detect_test_command` を編集するか、`TEST_CMD` を設定する:

```bash
# Unit tests only (faster feedback)
export TEST_CMD="npm run test:unit"

# Type check + lint + test
export TEST_CMD="npm run typecheck && npm run lint && npm test"
```

### prompt / agent 型 hook による高度なゲート

「テストが通ったか」を越えて「タスクの完了条件を満たしたか」まで判定させたい場合は、`type: "command"` の代わりに `type: "prompt"`（モデル1回評価）や `type: "agent"`（Read/Grep 等のツールを使えるサブエージェント判定）を Stop hook に使える。設定方法は公式 hooks リファレンス（code.claude.com/docs/en/hooks）を参照。決定論的に判定できるもの（テスト・lint）は command 型、判断が要るものだけ prompt/agent 型にするのがコスト面で妥当。

## Design Decisions

1. **`stop_hook_active` チェックを最初に置く** -- ブロック後の継続でも再度テストが失敗する場合、チェックがないと永遠にブロックし続ける。1回ブロックして直らなければ人間に返す設計。
2. **Always exit 0 when no test command is detected** -- テストが設定されていないプロジェクトでは agent をブロックしない。警告のみ出力する。
3. **Timeout で無限ループを防止** -- watch mode のテストランナーが暴走しないよう、タイムアウトを設定する。
4. **最後の 50 行のみ表示** -- テスト出力が膨大な場合、context window を圧迫しないよう末尾のみ表示する。
5. **exit 2 + stderr でブロック** -- 現行仕様でブロックとして扱われるのは exit 2（または JSON の `"decision": "block"`）。stderr に書いた内容だけが agent へのフィードバックになる。
6. **`set -e` を使わない** -- テスト失敗（非ゼロ exit）を自前でハンドリングするため、`-e` があると意図しない箇所でスクリプトが即死する。
