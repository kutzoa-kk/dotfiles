# CLAUDE.md Output Template

This is the structure to follow when generating CLAUDE.md. Only include sections that have actual content from the project analysis. Never include empty sections or placeholders.

## Template

```markdown
# CLAUDE.md

## Commands

{{Only include commands that exist. Group by purpose.}}

```bash
# Build
{{build_command}}

# Test
{{test_command}}

# Lint & Format
{{lint_command}}
{{format_command}}

# Type Check
{{typecheck_command}}
```

## Architecture

{{Only if ADRs, schemas, or structural decisions exist. Use pointers.}}

- ADRs: `docs/adr/` — read before proposing architectural changes
- Schema: `{{schema_path}}` — source of truth for data model
- API spec: `{{api_spec_path}}` — source of truth for endpoints

## Conventions

{{Only prohibitions that can't be enforced by linters. Each must have a reason.}}

- Do NOT {{prohibition}}. Why: {{reason or ADR link}}

## Key Paths

{{Only if the project layout isn't obvious from convention.}}

| Purpose | Path |
|---------|------|
| {{purpose}} | `{{path}}` |
```

## Guidelines

- Target: 30-50 lines. Treat 50 as a hard ceiling, not a goal.
- Every command must be copy-pasteable — no pseudo-commands.
- File paths must be relative to project root.
- If a Makefile/Justfile exists with clear targets, prefer `make <target>` over raw commands.
- Monorepos: include workspace-level commands, then note per-package commands exist in their own CLAUDE.md.
