# ADR Template

Architecture Decision Record（ADR）のテンプレートと運用ガイド。

## Template

```markdown
# ADR-NNN: Title

- **Status**: Accepted | Superseded by ADR-NNN | Deprecated
- **Date**: YYYY-MM-DD
- **Deciders**: [who was involved]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

### Positive

- ...

### Negative

- ...

### Neutral

- ...
```

## Status Lifecycle

```
Proposed -> Accepted -> [Superseded by ADR-NNN | Deprecated]
```

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion, not yet decided |
| **Accepted** | Decision made and in effect |
| **Superseded by ADR-NNN** | Replaced by a newer decision |
| **Deprecated** | No longer relevant (e.g., feature removed) |

**Rule**: ADR は編集しない。新しい決定をしたら新しい ADR を作成し、古い ADR の Status を `Superseded by ADR-NNN` に更新する。

## File Naming Convention

```
docs/adr/
├── 0001-record-architecture-decisions.md
├── 0002-use-postgresql-for-primary-database.md
├── 0003-adopt-hexagonal-architecture.md
└── 0004-migrate-to-redis-for-caching.md
```

- 連番は 4桁ゼロパディング
- ファイル名はケバブケースで決定内容を要約
- ディレクトリは `docs/adr/` を推奨

## Prose -> ADR 変換例

### Before (prose that rots)

```markdown
## Caching Strategy

We decided to use Redis instead of Memcached because Redis supports
data structures we need for our leaderboard feature. The connection
pool is configured with 50 max connections.
```

### After (ADR that self-documents)

```markdown
# ADR-0004: Use Redis for Caching Layer

- **Status**: Accepted
- **Date**: 2025-03-15
- **Deciders**: Backend team

## Context

The application needs a caching layer that supports sorted sets for
the leaderboard feature. Memcached only supports simple key-value
pairs.

## Decision

Use Redis as the caching layer.

## Consequences

### Positive
- Native sorted set support for leaderboards
- Pub/sub for real-time features
- Persistence options for cache warming

### Negative
- Single-threaded model may bottleneck under extreme write load
- More memory overhead than Memcached for simple k/v caching

### Neutral
- Connection pool configuration: see `config/redis.yml`
```

**Key difference**: ADR は Date と Status を持つため、agent が「これは 2025-03-15 時点の決定」と判断できる。prose はいつ書かれたか不明。

## Bootstrap: First ADR

リポジトリに ADR を初めて導入する場合、最初の ADR は「ADR を使うことにした」という決定自体を記録する：

```markdown
# ADR-0001: Record Architecture Decisions

- **Status**: Accepted
- **Date**: YYYY-MM-DD
- **Deciders**: [team/individual]

## Context

Architecture decisions are currently scattered across Slack threads,
PR comments, and undated Markdown files. AI agents treat all
repository text as equally authoritative, making stale documentation
actively harmful.

## Decision

Record significant architecture decisions using Architecture Decision
Records (ADRs) in `docs/adr/`.

Each ADR must include:
- Sequential number
- Status (Accepted / Superseded / Deprecated)
- Date
- Context, Decision, Consequences sections

## Consequences

### Positive
- Decisions are discoverable and timestamped
- AI agents can assess recency and validity
- New team members understand historical context

### Negative
- Small overhead for each decision
- Requires discipline to create ADRs for significant changes

### Neutral
- Old decisions remain readable even when superseded
```

## Agent-Friendly Properties of ADRs

ADR が agent にとって安全な理由：

| Property | Why it helps agents |
|----------|-------------------|
| **Status field** | Agent は `Superseded` や `Deprecated` を無視できる |
| **Date field** | Agent は情報の鮮度を判断できる |
| **Immutable history** | 古い ADR は編集されないため、git blame が正確 |
| **Structured format** | パースしやすく、意味を正確に抽出できる |
| **Explicit scope** | 1つの決定 = 1つのファイル。混在しない |
