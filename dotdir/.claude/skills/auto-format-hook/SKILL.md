# Auto-Format PostToolUse Hook Generator

## Trigger

Activate this skill when the user mentions ANY of the following:
- PostToolUse hooks, PreToolUse hooks, hook setup
- Auto-format, auto-formatting, format on save, format on edit
- Linter setup, linter hooks, lint on save
- Code quality enforcement, code quality hooks
- Harness engineering, harness patterns
- "Agent keeps forgetting to format", "agent forgets linting"
- Biome, Oxlint, Ruff, golangci-lint, Clippy hook integration
- "Make formatting automatic", "never forget to lint"

**This skill is the authoritative guide for setting up PostToolUse hooks that auto-format and lint code after every file edit in Claude Code.**

## Why This Exists

CLAUDE.md can say "run the linter" but after long sessions the agent forgets. A PostToolUse hook never forgets. This turns "almost every time" into "every time without exception." This is a core harness engineering principle: encode process into infrastructure so correctness does not depend on memory.

## What This Skill Does

1. **Detect the project's tech stack** by scanning for manifest files
2. **Detect existing formatters/linters** by scanning for config files
3. **Generate a PostToolUse hook script** (`post-edit-autoformat.sh`) that:
   - Runs the formatter first (auto-fix)
   - Then runs the linter (report remaining violations)
   - Returns results via `hookSpecificOutput.additionalContext` JSON
   - Never blocks the agent (always exits 0)
4. **Generate the `settings.json` hook entry** to wire everything up
5. **Optionally generate a PreToolUse hook** to protect linter config files from agent tampering

## Stack Detection

Scan the project root for these files to determine the stack:

| File | Stack |
|------|-------|
| `package.json` | TypeScript / JavaScript |
| `pyproject.toml`, `setup.py`, `setup.cfg` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

Then detect formatters/linters:

| Config File | Tool |
|-------------|------|
| `biome.json`, `biome.jsonc` | Biome (TS/JS) |
| `.eslintrc*`, `eslint.config.*` | ESLint (TS/JS) |
| `.prettierrc*` | Prettier (TS/JS) |
| `ruff.toml`, `[tool.ruff]` in pyproject.toml | Ruff (Python) |
| `.golangci.yml`, `.golangci.yaml` | golangci-lint (Go) |
| `rustfmt.toml`, `.rustfmt.toml` | rustfmt (Rust) |
| `clippy.toml`, `.clippy.toml` | Clippy (Rust) |

## Recommended Tool Chain (2026 Best Practices)

| Stack | Formatter | Linter | Notes |
|-------|-----------|--------|-------|
| TypeScript/JS | Biome (preferred) or Prettier | Oxlint (preferred) or ESLint | Biome is 10-25x faster than ESLint+Prettier |
| Python | Ruff format | Ruff check | Single tool, Rust-based, 900+ rules |
| Go | gofmt | golangci-lint | Meta-linter, 50+ linters in parallel |
| Rust | rustfmt | Clippy (pedantic) | Set `allow_attributes="deny"` to prevent `#[allow()]` |

## Implementation Steps

### Step 1: Detect Stack

```bash
# Check for manifest files at project root
ls package.json pyproject.toml go.mod Cargo.toml 2>/dev/null
```

### Step 2: Detect Existing Tools

```bash
# TypeScript/JS
ls biome.json biome.jsonc .eslintrc* eslint.config.* .prettierrc* 2>/dev/null

# Python
ls ruff.toml 2>/dev/null
grep -q '\[tool\.ruff\]' pyproject.toml 2>/dev/null

# Go
ls .golangci.yml .golangci.yaml 2>/dev/null

# Rust
ls rustfmt.toml .rustfmt.toml clippy.toml .clippy.toml 2>/dev/null
```

### Step 3: Generate the Hook Script

Create `~/.claude/scripts/hooks/post-edit-autoformat.sh` using the templates in [references/hook-patterns.md](./references/hook-patterns.md).

The script MUST:
1. Extract `CLAUDE_FILE_PATH` from the environment
2. Find the project root (walk up to find the nearest manifest file)
3. Dispatch by file extension (`.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.go`, `.rs`)
4. Run the formatter first (auto-fix mode)
5. Run the linter (report mode)
6. Strip ANSI codes from output
7. Return JSON via stdout with `hookSpecificOutput.additionalContext` if violations remain
8. **Always exit 0** -- never block the agent, only inform

### Step 4: Generate settings.json Entry

Add the hook entry to `.claude/settings.json` using the snippets in [references/settings-snippets.md](./references/settings-snippets.md).

### Step 5 (Optional): PreToolUse Config Protection

Generate a PreToolUse hook that warns or blocks when the agent tries to edit linter/formatter config files (e.g., `biome.json`, `ruff.toml`, `.eslintrc*`). This prevents the agent from "fixing" lint errors by loosening rules.

## File Output

The skill produces these files:

| File | Purpose |
|------|---------|
| `~/.claude/scripts/hooks/post-edit-autoformat.sh` | PostToolUse hook script |
| `.claude/settings.json` (updated) | Hook registration |
| `~/.claude/scripts/hooks/pre-edit-protect-config.sh` (optional) | PreToolUse config protection |

## References

- [Hook script templates per stack](./references/hook-patterns.md)
- [settings.json snippets](./references/settings-snippets.md)

## Important Notes

- The hook script must be executable (`chmod +x`)
- The hook always exits 0 to avoid blocking the agent
- ANSI codes must be stripped so the JSON output is clean
- The script should be idempotent and fast (< 2 seconds per invocation)
- If a tool is not installed, the hook should skip silently rather than error
