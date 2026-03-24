---
name: claude-md-generator
description: "Use when the user mentions CLAUDE.md in any context: creating, generating, writing, setting up, slimming down, optimizing, auditing, or asking how to structure one — including Japanese (CLAUDE.mdを作成/生成/設定/書く/スリム化/最適化). Also use when the user says their CLAUDE.md is too long, bloated, not working well, or wants to initialize a project for Claude Code. Trigger for 'harness engineering' or 'pointer-based CLAUDE.md' mentions. Analyzes the codebase and produces a lean, pointer-based CLAUDE.md under 50 lines following harness engineering best practices. Do NOT trigger for AGENTS.md, README, settings.json, hooks configuration, or other non-CLAUDE.md files."
---

# CLAUDE.md Generator

Generate a lean, pointer-based CLAUDE.md that follows harness engineering best practices.

## Why This Matters

Research shows harness quality causes 22-point benchmark swings while model swaps cause only 1 point. A bloated CLAUDE.md (150+ instructions) triggers primacy bias and buries critical directives. This skill produces CLAUDE.md files that are pointers to executable truth, not prose descriptions of the system.

## Core Principles

These come from the harness engineering literature and should guide every decision:

1. **Pointers, not prose** — Point to `package.json`, test commands, ADRs. Never describe what the code already says.
2. **50 lines or fewer** — Claude's system prompt already uses ~50 instruction slots. Your CLAUDE.md gets the remaining budget before primacy bias kicks in.
3. **Executable truth only** — If a pointer's target disappears, it fails loudly (like a 404). Prose descriptions rot silently.
4. **Route, don't explain** — Tell the agent WHERE to look and WHAT commands to run, not HOW the system works.

## Workflow

### Mode Detection

Determine which mode to operate in:

- **Generate mode**: No CLAUDE.md exists, or user explicitly wants a fresh one
- **Slim mode**: Existing CLAUDE.md is too long or contains prose that should be pointers

### Step 1: Project Analysis

Scan the project to build a fact sheet. Do this systematically — don't guess.

**Stack detection** (check in order, stop at first match per category):

| Category | Files to check | What to extract |
|----------|---------------|-----------------|
| Language/Runtime | `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `Gemfile`, `build.gradle.kts`, `Package.swift` | Language, version constraints |
| Build | `Makefile`, `Justfile`, `Taskfile.yml`, `package.json scripts`, `Cargo.toml` | Build commands |
| Test | Same as build + `jest.config.*`, `vitest.config.*`, `pytest.ini`, `setup.cfg` | Test runner, coverage commands |
| Lint | `biome.json`, `oxlint.*`, `.eslintrc.*`, `ruff.toml`, `pyproject.toml [tool.ruff]`, `.golangci.yml`, `clippy.toml` | Lint/format commands |
| CI | `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile` | What CI enforces (tests, lint, type check) |
| Type check | `tsconfig.json`, `mypy.ini`, `pyproject.toml [tool.mypy]` | Type check commands |

**Architecture detection:**

| Signal | What to look for |
|--------|-----------------|
| ADRs | `docs/adr/`, `docs/decisions/`, `adr/` |
| Schema files | `*.prisma`, `schema.graphql`, `openapi.yaml`, `*.proto` |
| Hooks config | `.claude/settings.json`, `.husky/`, `lefthook.yml` |
| Monorepo | `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turborepo.json` |

### Step 2: Generate (or Rewrite) CLAUDE.md

Use the template structure from `references/template.md`. Fill in only what the analysis found — omit sections with no data rather than leaving placeholders.

**In Slim mode**, read the existing CLAUDE.md and:
1. Delete any line that describes what the code/config already says (e.g., "This project uses React 18" when `package.json` has it)
2. Convert descriptions to pointers (e.g., "Our API follows REST conventions with..." → point to the OpenAPI spec)
3. Remove duplicates of what linters already enforce
4. Keep only: commands, pointers, prohibitions with ADR references

### Step 3: Validate

After generating, verify every pointer target exists:

```bash
# For each file path mentioned in the generated CLAUDE.md
test -f <path> || echo "BROKEN POINTER: <path>"
```

Also check:
- Line count is under 50 (warn if over, hard stop at 80)
- No section describes what a config file already declares
- Every prohibition references an ADR or has a `Why:` annotation

### Step 4: Present and Iterate

Show the user:
1. The generated CLAUDE.md
2. Line count
3. Any broken pointers found
4. Suggestions for hooks that could enforce rules mechanically (reference `references/hooks-recommendations.md`)

Ask: "Want me to write this, or adjust anything first?"

## What NOT to Include in CLAUDE.md

This is as important as what to include. Omit these — they rot:

- **System description** ("This is a Next.js app that...") — `package.json` is the source of truth
- **Tech stack listing** ("We use PostgreSQL, Redis, ...") — config files declare this
- **Coding style guides** — linters enforce this; see `references/hooks-recommendations.md`
- **API documentation** — OpenAPI specs or type definitions are the source
- **Architecture overview** — if needed, write an ADR; don't put it inline

## Reference Files

- `references/template.md` — The CLAUDE.md output template with section structure
- `references/hooks-recommendations.md` — Suggested PostToolUse/PreToolUse hooks by stack
- `references/anti-patterns.md` — Common CLAUDE.md mistakes and how to fix them
