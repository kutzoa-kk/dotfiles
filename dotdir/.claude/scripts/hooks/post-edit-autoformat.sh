#!/usr/bin/env bash
# post-edit-autoformat.sh — PostToolUse hook for auto-formatting after file edits
# Install to: ~/.claude/scripts/hooks/post-edit-autoformat.sh
# chmod +x this file after creation
#
# This hook:
#   1. Runs after every Edit/Write/MultiEdit tool invocation
#   2. Detects file type from CLAUDE_FILE_PATH
#   3. Runs the appropriate formatter (auto-fix)
#   4. Runs the appropriate linter (report)
#   5. Outputs hookSpecificOutput JSON if violations remain
#   6. Always exits 0 (never blocks the agent)

set -euo pipefail

# ── Environment ──────────────────────────────────────────────────────
FILE_PATH="${CLAUDE_FILE_PATH:-}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

# Only run for file-editing tools
case "$TOOL_NAME" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

# Bail if no file path
[[ -z "$FILE_PATH" ]] && exit 0
[[ -f "$FILE_PATH" ]] || exit 0

# ── Helpers ──────────────────────────────────────────────────────────
strip_ansi() {
  sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'
}

# Find project root by walking up to find a manifest file
find_project_root() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    for manifest in package.json pyproject.toml go.mod Cargo.toml; do
      [[ -f "$dir/$manifest" ]] && echo "$dir" && return 0
    done
    dir="$(dirname "$dir")"
  done
  return 1
}

# Output hook result as JSON
output_result() {
  local violations="$1"
  if [[ -n "$violations" ]]; then
    local escaped
    escaped=$(echo "$violations" | python3 -c 'import sys,json; print(json.dumps("Lint violations after auto-format:\n" + sys.stdin.read()))' 2>/dev/null || echo '""')
    echo "{\"hookSpecificOutput\":{\"additionalContext\":${escaped}}}"
  fi
}

# Check if a command exists
has_cmd() {
  command -v "$1" &>/dev/null
}

# ── Project Root ─────────────────────────────────────────────────────
PROJECT_ROOT="$(find_project_root "$(dirname "$FILE_PATH")")" || exit 0

# ── Dispatch by Extension ────────────────────────────────────────────
EXT="${FILE_PATH##*.}"
VIOLATIONS=""

case "$EXT" in

  # ── TypeScript / JavaScript ──────────────────────────────────────
  ts|tsx|js|jsx|mjs|cjs|mts|cts)
    cd "$PROJECT_ROOT"

    if [[ -f biome.json || -f biome.jsonc ]] && has_cmd npx; then
      npx --yes @biomejs/biome format --write "$FILE_PATH" 2>/dev/null || true
    elif has_cmd npx && ls .prettierrc* prettier.config.* &>/dev/null; then
      npx --yes prettier --write "$FILE_PATH" 2>/dev/null || true
    fi

    if has_cmd oxlint; then
      VIOLATIONS=$(oxlint "$FILE_PATH" 2>&1 | strip_ansi || true)
    elif [[ -f biome.json || -f biome.jsonc ]] && has_cmd npx; then
      VIOLATIONS=$(npx --yes @biomejs/biome lint "$FILE_PATH" 2>&1 | strip_ansi || true)
    elif has_cmd npx && ls .eslintrc* eslint.config.* &>/dev/null; then
      VIOLATIONS=$(npx --yes eslint --no-fix "$FILE_PATH" 2>&1 | strip_ansi || true)
    fi
    ;;

  # ── Python ───────────────────────────────────────────────────────
  py|pyi)
    cd "$PROJECT_ROOT"

    if has_cmd ruff; then
      ruff format "$FILE_PATH" 2>/dev/null || true
      ruff check --fix "$FILE_PATH" 2>/dev/null || true
      VIOLATIONS=$(ruff check "$FILE_PATH" 2>&1 | strip_ansi || true)
    elif has_cmd black; then
      black --quiet "$FILE_PATH" 2>/dev/null || true
      if has_cmd flake8; then
        VIOLATIONS=$(flake8 "$FILE_PATH" 2>&1 | strip_ansi || true)
      fi
    fi
    ;;

  # ── Go ───────────────────────────────────────────────────────────
  go)
    cd "$PROJECT_ROOT"

    if has_cmd gofmt; then
      gofmt -w "$FILE_PATH" 2>/dev/null || true
    fi
    if has_cmd goimports; then
      goimports -w "$FILE_PATH" 2>/dev/null || true
    fi
    if has_cmd golangci-lint; then
      VIOLATIONS=$(golangci-lint run --no-fix "$FILE_PATH" 2>&1 | strip_ansi || true)
    elif has_cmd go; then
      VIOLATIONS=$(go vet "$FILE_PATH" 2>&1 | strip_ansi || true)
    fi
    ;;

  # ── Rust ─────────────────────────────────────────────────────────
  rs)
    cd "$PROJECT_ROOT"

    if has_cmd rustfmt; then
      rustfmt "$FILE_PATH" 2>/dev/null || true
    elif has_cmd cargo; then
      cargo fmt -- "$FILE_PATH" 2>/dev/null || true
    fi
    if has_cmd cargo; then
      VIOLATIONS=$(cargo clippy --message-format=short 2>&1 | strip_ansi | head -50 || true)
    fi
    ;;

  *)
    exit 0
    ;;
esac

# ── Output ───────────────────────────────────────────────────────────
VIOLATIONS=$(echo "$VIOLATIONS" | sed '/^$/d' | head -30)
if [[ -n "$VIOLATIONS" ]]; then
  output_result "$VIOLATIONS"
fi

exit 0
