# Hook Script Templates

This file contains the complete shell script templates for the PostToolUse auto-format hook and the optional PreToolUse config protection hook.

## PostToolUse Hook: post-edit-autoformat.sh

```bash
#!/usr/bin/env bash
# post-edit-autoformat.sh — PostToolUse hook for auto-formatting after file edits
# Install to: ~/.claude/scripts/hooks/post-edit-autoformat.sh
# chmod +x this file after creation
#
# This hook:
#   1. Runs after every Edit/Write tool invocation
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
    # Escape for JSON
    local escaped
    escaped=$(echo "$violations" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '""')
    cat <<JSON
{
  "hookSpecificOutput": {
    "additionalContext": "Lint violations after auto-format:\n" + ${escaped}
  }
}
JSON
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

    # Format: Biome > Prettier
    if [[ -f biome.json || -f biome.jsonc ]] && has_cmd npx; then
      npx --yes @biomejs/biome format --write "$FILE_PATH" 2>/dev/null || true
    elif has_cmd npx && [[ -f .prettierrc* || -f prettier.config.* ]] 2>/dev/null; then
      npx --yes prettier --write "$FILE_PATH" 2>/dev/null || true
    fi

    # Lint: Oxlint > Biome lint > ESLint
    if has_cmd oxlint; then
      VIOLATIONS=$(oxlint "$FILE_PATH" 2>&1 | strip_ansi || true)
    elif [[ -f biome.json || -f biome.jsonc ]] && has_cmd npx; then
      VIOLATIONS=$(npx --yes @biomejs/biome lint "$FILE_PATH" 2>&1 | strip_ansi || true)
    elif has_cmd npx && [[ -f .eslintrc* || -f eslint.config.* ]] 2>/dev/null; then
      VIOLATIONS=$(npx --yes eslint --no-fix "$FILE_PATH" 2>&1 | strip_ansi || true)
    fi
    ;;

  # ── Python ───────────────────────────────────────────────────────
  py|pyi)
    cd "$PROJECT_ROOT"

    if has_cmd ruff; then
      # Format first
      ruff format "$FILE_PATH" 2>/dev/null || true
      # Then lint with auto-fix, report remaining
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

    # Format: gofmt is always available with Go
    if has_cmd gofmt; then
      gofmt -w "$FILE_PATH" 2>/dev/null || true
    fi

    # Also run goimports if available
    if has_cmd goimports; then
      goimports -w "$FILE_PATH" 2>/dev/null || true
    fi

    # Lint: golangci-lint
    if has_cmd golangci-lint; then
      VIOLATIONS=$(golangci-lint run --no-fix "$FILE_PATH" 2>&1 | strip_ansi || true)
    elif has_cmd go; then
      VIOLATIONS=$(go vet "$FILE_PATH" 2>&1 | strip_ansi || true)
    fi
    ;;

  # ── Rust ─────────────────────────────────────────────────────────
  rs)
    cd "$PROJECT_ROOT"

    # Format
    if has_cmd rustfmt; then
      rustfmt "$FILE_PATH" 2>/dev/null || true
    elif has_cmd cargo; then
      cargo fmt -- "$FILE_PATH" 2>/dev/null || true
    fi

    # Lint: clippy (runs on the whole crate, but we report)
    if has_cmd cargo; then
      VIOLATIONS=$(cargo clippy --message-format=short 2>&1 | strip_ansi | head -50 || true)
    fi
    ;;

  # ── Unknown extension: skip silently ─────────────────────────────
  *)
    exit 0
    ;;
esac

# ── Output ───────────────────────────────────────────────────────────
# Only output if there are actual violations (non-empty, non-whitespace)
VIOLATIONS=$(echo "$VIOLATIONS" | sed '/^$/d' | head -30)
if [[ -n "$VIOLATIONS" ]]; then
  output_result "$VIOLATIONS"
fi

exit 0
```

## Simplified Per-Stack Variants

If you prefer a single-stack hook instead of the universal one above, use these minimal variants.

### TypeScript/JavaScript Only

```bash
#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${CLAUDE_FILE_PATH:-}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

case "$TOOL_NAME" in Edit|Write|MultiEdit) ;; *) exit 0 ;; esac
[[ -z "$FILE_PATH" || ! -f "$FILE_PATH" ]] && exit 0

EXT="${FILE_PATH##*.}"
case "$EXT" in ts|tsx|js|jsx|mjs|cjs|mts|cts) ;; *) exit 0 ;; esac

strip_ansi() { sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'; }

# Format with Biome
npx --yes @biomejs/biome format --write "$FILE_PATH" 2>/dev/null || true

# Lint with Oxlint (fallback: Biome lint)
if command -v oxlint &>/dev/null; then
  VIOLATIONS=$(oxlint "$FILE_PATH" 2>&1 | strip_ansi || true)
else
  VIOLATIONS=$(npx --yes @biomejs/biome lint "$FILE_PATH" 2>&1 | strip_ansi || true)
fi

VIOLATIONS=$(echo "$VIOLATIONS" | sed '/^$/d' | head -30)
if [[ -n "$VIOLATIONS" ]]; then
  escaped=$(echo "$VIOLATIONS" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
  echo "{\"hookSpecificOutput\":{\"additionalContext\":${escaped}}}"
fi

exit 0
```

### Python Only

```bash
#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${CLAUDE_FILE_PATH:-}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

case "$TOOL_NAME" in Edit|Write|MultiEdit) ;; *) exit 0 ;; esac
[[ -z "$FILE_PATH" || ! -f "$FILE_PATH" ]] && exit 0

EXT="${FILE_PATH##*.}"
case "$EXT" in py|pyi) ;; *) exit 0 ;; esac

strip_ansi() { sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'; }

# Format + auto-fix
ruff format "$FILE_PATH" 2>/dev/null || true
ruff check --fix "$FILE_PATH" 2>/dev/null || true

# Report remaining
VIOLATIONS=$(ruff check "$FILE_PATH" 2>&1 | strip_ansi | sed '/^$/d' | head -30 || true)

if [[ -n "$VIOLATIONS" ]]; then
  escaped=$(echo "$VIOLATIONS" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
  echo "{\"hookSpecificOutput\":{\"additionalContext\":${escaped}}}"
fi

exit 0
```

### Go Only

```bash
#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${CLAUDE_FILE_PATH:-}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

case "$TOOL_NAME" in Edit|Write|MultiEdit) ;; *) exit 0 ;; esac
[[ -z "$FILE_PATH" || ! -f "$FILE_PATH" ]] && exit 0

EXT="${FILE_PATH##*.}"
[[ "$EXT" != "go" ]] && exit 0

strip_ansi() { sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'; }

gofmt -w "$FILE_PATH" 2>/dev/null || true
command -v goimports &>/dev/null && goimports -w "$FILE_PATH" 2>/dev/null || true

VIOLATIONS=""
if command -v golangci-lint &>/dev/null; then
  VIOLATIONS=$(golangci-lint run --no-fix "$FILE_PATH" 2>&1 | strip_ansi | sed '/^$/d' | head -30 || true)
fi

if [[ -n "$VIOLATIONS" ]]; then
  escaped=$(echo "$VIOLATIONS" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
  echo "{\"hookSpecificOutput\":{\"additionalContext\":${escaped}}}"
fi

exit 0
```

### Rust Only

```bash
#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${CLAUDE_FILE_PATH:-}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

case "$TOOL_NAME" in Edit|Write|MultiEdit) ;; *) exit 0 ;; esac
[[ -z "$FILE_PATH" || ! -f "$FILE_PATH" ]] && exit 0

EXT="${FILE_PATH##*.}"
[[ "$EXT" != "rs" ]] && exit 0

strip_ansi() { sed 's/\x1b\[[0-9;]*[a-zA-Z]//g'; }

rustfmt "$FILE_PATH" 2>/dev/null || true

VIOLATIONS=$(cargo clippy --message-format=short 2>&1 | strip_ansi | sed '/^$/d' | head -50 || true)

if [[ -n "$VIOLATIONS" ]]; then
  escaped=$(echo "$VIOLATIONS" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')
  echo "{\"hookSpecificOutput\":{\"additionalContext\":${escaped}}}"
fi

exit 0
```

## PreToolUse Hook: pre-edit-protect-config.sh

This optional hook warns or blocks when the agent tries to modify linter/formatter config files. Prevents the agent from "fixing" lint errors by loosening rules.

```bash
#!/usr/bin/env bash
# pre-edit-protect-config.sh — PreToolUse hook to protect linter/formatter configs
# Install to: ~/.claude/scripts/hooks/pre-edit-protect-config.sh
# chmod +x this file after creation

set -euo pipefail

FILE_PATH="${CLAUDE_FILE_PATH:-}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

# Only check file-editing tools
case "$TOOL_NAME" in Edit|Write|MultiEdit) ;; *) exit 0 ;; esac

[[ -z "$FILE_PATH" ]] && exit 0

BASENAME="$(basename "$FILE_PATH")"

# List of protected config files
PROTECTED_CONFIGS=(
  "biome.json"
  "biome.jsonc"
  ".eslintrc"
  ".eslintrc.js"
  ".eslintrc.cjs"
  ".eslintrc.json"
  ".eslintrc.yml"
  ".eslintrc.yaml"
  "eslint.config.js"
  "eslint.config.mjs"
  "eslint.config.cjs"
  "eslint.config.ts"
  ".prettierrc"
  ".prettierrc.js"
  ".prettierrc.cjs"
  ".prettierrc.json"
  ".prettierrc.yml"
  ".prettierrc.yaml"
  "prettier.config.js"
  "prettier.config.cjs"
  "ruff.toml"
  ".golangci.yml"
  ".golangci.yaml"
  "golangci.yml"
  "rustfmt.toml"
  ".rustfmt.toml"
  "clippy.toml"
  ".clippy.toml"
  "oxlint.json"
  ".oxlintrc.json"
)

for config in "${PROTECTED_CONFIGS[@]}"; do
  if [[ "$BASENAME" == "$config" ]]; then
    cat <<JSON
{
  "hookSpecificOutput": {
    "additionalContext": "WARNING: You are about to modify a linter/formatter config file ($BASENAME). Do NOT loosen rules to suppress lint errors. Fix the actual code instead. If you genuinely need to change the config, explain why to the user first."
  }
}
JSON
    # Exit 0 to allow but warn. Change to exit 1 to hard-block.
    exit 0
  fi
done

exit 0
```

## Hook Script Design Principles

1. **Always exit 0**: The hook informs but never blocks. The agent decides what to do with the information.
2. **Fast execution**: Formatters and linters should complete in < 2 seconds for a single file.
3. **Strip ANSI**: Tool output often contains color codes. Strip them so JSON output is clean.
4. **Truncate output**: Use `head -30` or `head -50` to prevent massive lint output from bloating the context.
5. **Graceful degradation**: If a tool is not installed, skip silently. Never error out.
6. **Idempotent**: Running the hook twice on the same file produces the same result.
7. **Project-root aware**: Always `cd` to the project root before running tools, as many tools depend on config discovery from the working directory.
