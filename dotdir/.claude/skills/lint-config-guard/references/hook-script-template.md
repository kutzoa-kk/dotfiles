# Hook Script Template

PreToolUse フックスクリプトのテンプレート。

## スクリプト

以下の内容を `.claude/scripts/hooks/lint-config-guard.sh` として配置する。

```bash
#!/usr/bin/env bash
# lint-config-guard: Prevent AI agents from modifying linter/formatter config files.
# PreToolUse hook - reads tool input from $1 (JSON string) or stdin.
# Exit codes:
#   0 = allow (not a protected file)
#   2 = block (protected file, sends explanation to stderr)

set -euo pipefail

# --- Read tool input JSON ---
if [[ -n "${1:-}" ]]; then
  INPUT="$1"
else
  INPUT="$(cat)"
fi

# Extract file_path from tool input JSON
# Supports both Edit and Write tool schemas
FILE_PATH="$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*"file_path"\s*:\s*"//;s/"$//')"

if [[ -z "$FILE_PATH" ]]; then
  # No file_path found - not a file edit operation, allow
  exit 0
fi

# --- Extract basename and resolve relative path ---
BASENAME="$(basename "$FILE_PATH")"

# --- Protected exact filenames ---
PROTECTED_EXACT=(
  ".eslintrc"
  ".eslintignore"
  "biome.json"
  "biome.jsonc"
  ".prettierrc"
  "oxlint.json"
  "ruff.toml"
  ".ruff.toml"
  ".pylintrc"
  "pylintrc"
  "mypy.ini"
  ".mypy.ini"
  ".golangci.yml"
  ".golangci.yaml"
  ".golangci.json"
  ".golangci.toml"
  "clippy.toml"
  ".clippy.toml"
  "tsconfig.json"
  "lefthook.yml"
  "lefthook.yaml"
  "lefthook-local.yml"
  "lefthook-local.yaml"
  "pyproject.toml"
  "setup.cfg"
  "Cargo.toml"
)

# --- Check exact filename matches ---
for protected in "${PROTECTED_EXACT[@]}"; do
  if [[ "$BASENAME" == "$protected" ]]; then
    cat >&2 <<MSG
BLOCKED: Cannot modify linter configuration '$FILE_PATH'
WHY: Modifying linter rules to suppress errors leads to accumulated technical debt.
     The lint rule exists for a reason -- fix the code instead.
FIX: Address the lint violation in the source file.
     If the rule is genuinely wrong for this project, ask the user to modify the config.
MSG
    exit 2
  fi
done

# --- Check glob pattern matches (basename only) ---

# .eslintrc.*
if [[ "$BASENAME" == .eslintrc.* ]]; then
  cat >&2 <<MSG
BLOCKED: Cannot modify ESLint configuration '$FILE_PATH'
WHY: Modifying linter rules to suppress errors leads to accumulated technical debt.
     The lint rule exists for a reason -- fix the code instead.
FIX: Address the lint violation in the source file.
     If the rule is genuinely wrong for this project, ask the user to modify the config.
MSG
  exit 2
fi

# eslint.config.*
if [[ "$BASENAME" == eslint.config.* ]]; then
  cat >&2 <<MSG
BLOCKED: Cannot modify ESLint configuration '$FILE_PATH'
WHY: Modifying linter rules to suppress errors leads to accumulated technical debt.
     The lint rule exists for a reason -- fix the code instead.
FIX: Address the lint violation in the source file.
     If the rule is genuinely wrong for this project, ask the user to modify the config.
MSG
  exit 2
fi

# .prettierrc.*
if [[ "$BASENAME" == .prettierrc.* ]]; then
  cat >&2 <<MSG
BLOCKED: Cannot modify Prettier configuration '$FILE_PATH'
WHY: Modifying formatter rules to suppress errors leads to inconsistent code style.
     The formatting rule exists for a reason -- fix the code instead.
FIX: Address the formatting issue in the source file.
     If the rule is genuinely wrong for this project, ask the user to modify the config.
MSG
  exit 2
fi

# prettier.config.*
if [[ "$BASENAME" == prettier.config.* ]]; then
  cat >&2 <<MSG
BLOCKED: Cannot modify Prettier configuration '$FILE_PATH'
WHY: Modifying formatter rules to suppress errors leads to inconsistent code style.
     The formatting rule exists for a reason -- fix the code instead.
FIX: Address the formatting issue in the source file.
     If the rule is genuinely wrong for this project, ask the user to modify the config.
MSG
  exit 2
fi

# oxlint.* and .oxlintrc.*
if [[ "$BASENAME" == oxlint.* || "$BASENAME" == .oxlintrc.* ]]; then
  cat >&2 <<MSG
BLOCKED: Cannot modify Oxlint configuration '$FILE_PATH'
WHY: Modifying linter rules to suppress errors leads to accumulated technical debt.
     The lint rule exists for a reason -- fix the code instead.
FIX: Address the lint violation in the source file.
     If the rule is genuinely wrong for this project, ask the user to modify the config.
MSG
  exit 2
fi

# tsconfig.*.json (but not tsconfig.json itself, already caught above)
if [[ "$BASENAME" == tsconfig.*.json ]]; then
  cat >&2 <<MSG
BLOCKED: Cannot modify TypeScript configuration '$FILE_PATH'
WHY: Modifying TypeScript compiler options to suppress type errors leads to weaker type safety.
     The type error exists for a reason -- fix the code instead.
FIX: Address the type error in the source file.
     If the configuration change is genuinely needed, ask the user to modify the config.
MSG
  exit 2
fi

# --- Check directory-based matches ---

# .husky/ directory
if [[ "$FILE_PATH" == */.husky/* || "$FILE_PATH" == .husky/* ]]; then
  cat >&2 <<MSG
BLOCKED: Cannot modify Git hook '$FILE_PATH'
WHY: Git hooks are quality gates that enforce standards before commits.
     Modifying them undermines the project's code quality process.
FIX: Fix the issue that the Git hook is catching.
     If the hook configuration needs updating, ask the user to modify it.
MSG
  exit 2
fi

# --- Not a protected file, allow ---
exit 0
```

## 使い方

### 1. スクリプトを配置

```bash
mkdir -p .claude/scripts/hooks
# 上記の内容をコピー
chmod +x .claude/scripts/hooks/lint-config-guard.sh
```

### 2. settings.json に登録

`.claude/settings.json` に以下を追加（既存の hooks とマージすること）:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/scripts/hooks/lint-config-guard.sh \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

### 3. テスト

```bash
# ブロックされるケース
echo '{"file_path":".eslintrc.js","old_string":"a","new_string":"b"}' \
  | .claude/scripts/hooks/lint-config-guard.sh
echo "Exit code: $?"
# Expected: exit code 2, BLOCKED message on stderr

# 許可されるケース
echo '{"file_path":"src/index.ts","old_string":"a","new_string":"b"}' \
  | .claude/scripts/hooks/lint-config-guard.sh
echo "Exit code: $?"
# Expected: exit code 0, no output
```

## カスタマイズ

### プロジェクト固有のファイルを追加保護

`PROTECTED_EXACT` 配列にファイル名を追加:

```bash
PROTECTED_EXACT=(
  # ... existing entries ...
  ".stylelintrc"        # Stylelint
  "deno.json"           # Deno config
  ".markdownlint.json"  # Markdown linting
)
```

### 特定ファイルの保護を解除

対象パターンをスクリプトから削除するか、ファイルの先頭に早期 return を追加:

```bash
# 特定ファイルをホワイトリストに追加
WHITELIST=(
  "tsconfig.test.json"  # テスト用のtsconfigは編集を許可
)
for allowed in "${WHITELIST[@]}"; do
  if [[ "$BASENAME" == "$allowed" ]]; then
    exit 0
  fi
done
```
