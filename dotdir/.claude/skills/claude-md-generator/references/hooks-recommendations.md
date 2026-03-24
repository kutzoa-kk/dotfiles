# Hooks Recommendations by Stack

When generating CLAUDE.md, suggest these hooks to the user based on detected stack. Hooks enforce rules mechanically — they turn "please do X" into "X happens automatically".

## Why Hooks Matter

A PostToolUse hook runs after every file edit. It catches violations immediately, before they accumulate. CLAUDE.md says "run the linter" — but after a long debugging session, the agent forgets. A hook never forgets.

## TypeScript / JavaScript

### Recommended: Oxlint + Biome (fast, Rust-based)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx @biomejs/biome format --write $CLAUDE_FILE_PATH 2>/dev/null; npx oxlint $CLAUDE_FILE_PATH 2>&1 | head -20"
          }
        ]
      }
    ]
  }
}
```

### Alternative: ESLint + Prettier (slower, more plugins)

Use in pre-commit only. Too slow for PostToolUse.

## Python

### Recommended: Ruff (single tool, Rust-based)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "ruff format $CLAUDE_FILE_PATH 2>/dev/null; ruff check --fix $CLAUDE_FILE_PATH 2>&1 | head -20"
          }
        ]
      }
    ]
  }
}
```

## Go

### Recommended: golangci-lint

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "gofmt -w $CLAUDE_FILE_PATH 2>/dev/null; golangci-lint run $CLAUDE_FILE_PATH 2>&1 | head -20"
          }
        ]
      }
    ]
  }
}
```

## Rust

### Recommended: Clippy (pedantic)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "cargo fmt -- $CLAUDE_FILE_PATH 2>/dev/null; cargo clippy -- -W clippy::pedantic 2>&1 | head -30"
          }
        ]
      }
    ]
  }
}
```

## Safety Hooks (All Stacks)

### Protect linter configs from agent tampering

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "echo $CLAUDE_FILE_PATH | grep -qE '(\\.eslintrc|eslint\\.config|biome\\.json|pyproject\\.toml|ruff\\.toml|\\.golangci|clippy\\.toml)' && echo 'BLOCKED: Do not modify linter configuration files' >&2 && exit 2 || exit 0"
          }
        ]
      }
    ]
  }
}
```

### Block destructive commands

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$CLAUDE_BASH_COMMAND\" | grep -qE '(rm -rf|drop table|--no-verify|--force)' && echo 'BLOCKED: Destructive command requires user approval' >&2 && exit 2 || exit 0"
          }
        ]
      }
    ]
  }
}
```

## Presentation to User

When suggesting hooks, explain:
1. What the hook does (in plain language)
2. Why it's better than a CLAUDE.md instruction (mechanical enforcement vs. request)
3. How to install it (which settings.json to edit)

Don't dump all hooks at once. Suggest the most impactful 1-2 based on what the project actually needs.
