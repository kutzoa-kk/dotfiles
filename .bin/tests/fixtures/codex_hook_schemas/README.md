# Codex hook output contracts

These five JSON schemas were extracted on 2026-09-23 from the installed
`/Applications/ChatGPT.app/Contents/Resources/codex` binary. The exact embedded
JSON was also found in Codex CLI 0.156.1
(`/opt/homebrew/Caskroom/codex/0.156.1/bin/codex`). Both copies were parsed and
compared before writing these fixtures. Files add a final newline to the
embedded JSON; SHA-256 values below describe the original embedded bytes.

| Event | App byte offset | CLI byte offset | Bytes | SHA-256 |
|---|---:|---:|---:|---|
| SessionStart | 180119953 | 182409827 | 1061 | f375e6de1c59ecbabd8c1aff05a67976d0f3aa2ef061808838de4c7c20be1c71 |
| UserPromptSubmit | 180127899 | 182417773 | 1390 | 5e290303db710f3ccc12f4a2744e8586e7749b3ca2b6bf9f57781ed75bf17b2b |
| PostToolUse | 180107202 | 182397076 | 1441 | a823d0e2c941e98d7d3af825dfdb0b1dfa6a935696ff8b8529e8e83232a1b0c8 |
| Stop | 180130567 | 182420441 | 963 | dc2b30e84c97beca5825aa64ca46e1337e402781dc5a9142b67111d10523f15c |
| SubagentStop | 180125632 | 182415506 | 972 | 8ba2cd7899ae4544193764e67e988235edebe984abe5788634d123bbf13e3e3a |

The tests validate the schema keywords used by these fixtures with the Python
standard library. They also check semantics not expressed in JSON Schema:
`decision: block` requires a nonempty reason; synchronous PostToolUse,
UserPromptSubmit, Stop, and SubagentStop hooks with exit code 2 must write their
feedback to stderr, because Codex ignores stdout on that path.

Official implementation references, checked on 2026-09-23:

- [Wire output schemas](https://github.com/openai/codex/blob/main/codex-rs/hooks/src/schema.rs)
- [PostToolUse result handling](https://github.com/openai/codex/blob/main/codex-rs/hooks/src/events/post_tool_use.rs)
- [Stop and SubagentStop result handling](https://github.com/openai/codex/blob/main/codex-rs/hooks/src/events/stop.rs)
- [UserPromptSubmit result handling](https://github.com/openai/codex/blob/main/codex-rs/hooks/src/events/user_prompt_submit.rs)

These are pinned fixtures for the installed runtime, not a claim that upstream
`main` will remain unchanged. Refresh the fixtures when the supported hook
protocol changes. Tests never invoke the real reviewer or SDK bootstrap.
