# Stop Hook Template -- Test Gate

Agent がタスク完了を宣言する前にテストスイートを実行し、失敗があれば完了をブロックする Stop Hook。

## Script Template

以下を `.claude/scripts/hooks/stop-test-gate.sh` として保存する。

```bash
#!/usr/bin/env bash
# Stop Hook: Test Gate
# Runs the project's test suite before allowing the agent to declare "done".
# Exit 0 = allow stop, non-zero = block stop with feedback.

set -euo pipefail

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

# Run tests with timeout, capture output
TEST_OUTPUT=$(timeout "$TEST_TIMEOUT" bash -c "$TEST_CMD" 2>&1) || TEST_EXIT=$?
TEST_EXIT="${TEST_EXIT:-0}"

if [ "$TEST_EXIT" -eq 0 ]; then
  echo "All tests passed. OK to complete."
  exit 0
fi

# Tests failed -- block stop and show output
cat <<MSG
BLOCKED: Tests are failing. Fix them before completing the task.

Test command: $TEST_CMD
Exit code: $TEST_EXIT

Output (last 50 lines):
---
$(echo "$TEST_OUTPUT" | tail -50)
---

Fix the failing tests, then try completing again.
MSG

exit 1
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
            "command": ".claude/scripts/hooks/stop-test-gate.sh"
          }
        ]
      }
    ]
  }
}
```

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

## Design Decisions

1. **Always exit 0 when no test command is detected** -- テストが設定されていないプロジェクトでは agent をブロックしない。警告のみ出力する。
2. **Timeout で無限ループを防止** -- watch mode のテストランナーが暴走しないよう、タイムアウトを設定する。
3. **最後の 50 行のみ表示** -- テスト出力が膨大な場合、context window を圧迫しないよう末尾のみ表示する。
4. **exit 1 でブロック** -- テスト失敗時は agent の完了宣言をブロックし、修正を促す。
