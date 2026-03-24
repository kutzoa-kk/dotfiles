# CLAUDE.md Anti-Patterns

Common mistakes when writing CLAUDE.md files and how to fix them. Reference this when auditing existing files in Slim mode.

## Anti-Pattern 1: System Description

**Bad:**
```markdown
This is a Next.js 14 application with App Router that uses PostgreSQL for data storage,
Redis for caching, and Tailwind CSS for styling. The project follows a feature-based
directory structure with shared components in src/components/shared/.
```

**Why it's bad:** All of this is already in `package.json`, `next.config.js`, and the directory structure itself. When these change, the CLAUDE.md description becomes a lie that the agent trusts equally.

**Fix:** Delete entirely. If there's something non-obvious about the setup, write a one-line pointer:
```markdown
- Non-standard: Redis used for session storage, not just caching. See `docs/adr/003-redis-sessions.md`
```

## Anti-Pattern 2: Coding Style Guide Inline

**Bad:**
```markdown
## Coding Standards
- Use camelCase for variables
- Use PascalCase for components
- Maximum line length: 100 characters
- Always use const over let
- Prefer arrow functions
```

**Why it's bad:** This is what linters enforce. If a linter catches it, it doesn't belong in CLAUDE.md. If a linter doesn't catch it, write a linter rule.

**Fix:** Delete and ensure linter config covers these rules. In CLAUDE.md, just point to the lint command:
```markdown
# Lint & Format
npx biome check --write .
```

## Anti-Pattern 3: Massive File (>80 lines)

**Bad:** Any CLAUDE.md over 80 lines. Research shows performance degrades past ~150 instructions total (system prompt + CLAUDE.md).

**Fix:** Apply the pointer principle ruthlessly:
1. Delete system descriptions (Anti-Pattern 1)
2. Delete linter-enforceable rules (Anti-Pattern 2)
3. Convert remaining descriptions to file pointers
4. What's left should be commands + pointers + prohibitions

## Anti-Pattern 4: Duplicating CI

**Bad:**
```markdown
Before pushing, make sure to:
1. Run all tests
2. Check TypeScript types
3. Run the linter
4. Check for unused imports
```

**Why it's bad:** This is what CI does. And if hooks are set up, PostToolUse does it automatically.

**Fix:** One line:
```markdown
# Verify (same as CI)
make check
```

## Anti-Pattern 5: API Documentation

**Bad:**
```markdown
## API Endpoints
- POST /api/users - Create a new user
- GET /api/users/:id - Get user by ID
- PUT /api/users/:id - Update user
...
```

**Why it's bad:** OpenAPI spec or route files are the source of truth. This copy will drift.

**Fix:**
```markdown
- API spec: `openapi.yaml` — source of truth for all endpoints
```

## Anti-Pattern 6: Prohibition Without Reason

**Bad:**
```markdown
- Do NOT use default exports
- Do NOT use any type
- Do NOT use console.log
```

**Why it's bad:** Without a reason, the agent can't judge edge cases. And these should probably be linter rules anyway.

**Fix:** Either add to linter, or if there's a real reason the linter can't catch:
```markdown
- Do NOT bypass rate limiting middleware. Why: see `docs/adr/007-rate-limit-incident.md`
```

## Slim Mode Checklist

When auditing an existing CLAUDE.md:

1. [ ] Delete every line that describes what config files already say
2. [ ] Delete every line that linters already enforce
3. [ ] Delete every line that duplicates CI checks
4. [ ] Convert remaining descriptions to pointers (file path + what to look for)
5. [ ] Add `Why:` to every prohibition
6. [ ] Verify line count < 50 (warn), < 80 (hard stop)
7. [ ] Test every file path pointer exists
