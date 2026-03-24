# settings.json Hook Snippets

This file contains the JSON snippets to add to `.claude/settings.json` for wiring up the auto-format hooks.

## PostToolUse Hook Entry

Add this to your project's `.claude/settings.json` under the `hooks` key:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/scripts/hooks/post-edit-autoformat.sh"
          }
        ]
      }
    ]
  }
}
```

### With Environment Variables

If you need to pass extra configuration:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "LINT_SEVERITY=error bash ~/.claude/scripts/hooks/post-edit-autoformat.sh"
          }
        ]
      }
    ]
  }
}
```

## PreToolUse Config Protection Hook Entry (Optional)

Add this alongside the PostToolUse hook to prevent linter config tampering:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/scripts/hooks/pre-edit-protect-config.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/scripts/hooks/post-edit-autoformat.sh"
          }
        ]
      }
    ]
  }
}
```

## Full Example: Combined settings.json

A complete `.claude/settings.json` with both hooks and typical permissions:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run format)",
      "Bash(ruff check *)",
      "Bash(ruff format *)",
      "Bash(gofmt *)",
      "Bash(golangci-lint run *)",
      "Bash(cargo fmt *)",
      "Bash(cargo clippy *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/scripts/hooks/pre-edit-protect-config.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/scripts/hooks/post-edit-autoformat.sh"
          }
        ]
      }
    ]
  }
}
```

## Per-Project Overrides

If a project uses a different formatter, override at the project level in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/scripts/hooks/post-edit-autoformat.sh"
          }
        ]
      }
    ]
  }
}
```

## User-Level vs Project-Level Installation

| Location | File | Scope |
|----------|------|-------|
| `~/.claude/settings.json` | User global | All projects |
| `<project>/.claude/settings.json` | Project | This project only |
| `<project>/.claude/settings.local.json` | Project local (gitignored) | This project, this machine |

**Recommendation**: Install the hook script at the user level (`~/.claude/scripts/hooks/`) and the settings.json entry at the project level so each project opts in explicitly.

## Hook Environment Variables

The following environment variables are available inside hook scripts:

| Variable | Description | Example |
|----------|-------------|---------|
| `CLAUDE_FILE_PATH` | Absolute path to the file being edited | `/home/user/project/src/index.ts` |
| `CLAUDE_TOOL_NAME` | Name of the tool that was invoked | `Edit`, `Write`, `MultiEdit` |

## Verifying the Hook Works

After installation, test by editing a file with intentional formatting issues:

1. Open a Claude Code session in your project
2. Ask Claude to write a file with bad formatting (e.g., wrong indentation, missing semicolons)
3. Check that the hook output appears in the conversation showing format/lint results
4. Verify the file was auto-formatted on disk

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Hook not firing | Matcher does not match tool name | Verify matcher regex: `Edit\|Write\|MultiEdit` |
| Permission denied | Script not executable | `chmod +x ~/.claude/scripts/hooks/post-edit-autoformat.sh` |
| Tool not found | Formatter/linter not in PATH | Install the tool or check PATH in hook script |
| No output | File extension not handled | Add the extension to the case statement in the hook script |
| ANSI codes in output | strip_ansi not working | Verify sed command; on macOS may need `gsed` |
