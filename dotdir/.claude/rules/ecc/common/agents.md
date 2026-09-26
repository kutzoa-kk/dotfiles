# Agent Orchestration

## Available Agents

ECC agents ship with the `ecc@ecc` plugin, not in `~/.claude/agents/`.
They are invoked through the Agent tool with a plugin-scoped `subagent_type`:

```text
Agent(subagent_type: "ecc:planner", prompt: "...")
```

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| ecc:planner | Implementation planning | Complex features, refactoring |
| ecc:architect | System design | Architectural decisions |
| ecc:tdd-guide | Test-driven development | New features, bug fixes |
| ecc:code-reviewer | Code review | After writing code |
| ecc:security-reviewer | Security analysis | Before commits |
| ecc:build-error-resolver | Fix build errors | When build fails |
| ecc:e2e-runner | E2E testing | Critical user flows |
| ecc:refactor-cleaner | Dead code cleanup | Code maintenance |
| ecc:doc-updater | Documentation | Updating docs |
| ecc:rust-reviewer | Rust code review | Rust projects |
| ecc:harmonyos-app-resolver | HarmonyOS app development | HarmonyOS/ArkTS projects |

For the full roster of 68 agents, see `/ecc:ecc-guide`.

## When to Delegate

Subagents multiply cost and time: each one re-establishes context and reports back. Use them for independent, sizeable tracks (a wide multi-file investigation, a separate review pass), not for work you can finish directly in a few tool calls. When fanning out across genuinely independent items, launch them in one message so they run concurrently.

## Delegation Completion Contract

Applies to every agent at every depth (parent, child, grandchild):

1. **Your final message IS the deliverable.** Never end your turn with "waiting for background agents" — a spawned task is not a completed task. Ending your turn while children are running orphans their results (completed children cannot notify a parent whose turn has ended).
2. **If you delegate, you own collection.** Wait for results, integrate them, then return. Fire-and-forget delegation is forbidden.
3. **Decompose only when the work cannot fit in one context.** Do not re-delegate a task already sized for a single agent — depth is an outcome, not a plan.

> Rationale: observed failure mode — research agents spawned children in parallel, and returned "waiting" as their final answer. All children completed successfully but their results were orphaned. The parallel rule without a completion contract produces zombie tasks.

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
