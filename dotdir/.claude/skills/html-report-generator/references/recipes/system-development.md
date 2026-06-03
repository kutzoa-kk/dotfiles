# System Development Report Structure

Use for architecture overviews, design documents, technical investigations,
RFCs, post-mortems, technology evaluation reports.

The reader is an engineer or technical lead who needs to make or validate a
decision. They want context, alternatives considered, and the rationale — not
just a recommendation.

## Canonical section order

```
1. Header                — title, status (Draft / Review / Approved), authors, date
2. Summary               — 3–5 sentences. The decision and why.
3. Context / Background  — why this matters now. Problem statement.
4. Goals & non-goals     — explicit scope. Bullet lists are fine here.
5. Current state         — architecture diagram of what exists today.
6. Proposed change       — architecture diagram of the target state.
7. Alternatives considered — what else was evaluated and why rejected.
8. Detailed design       — components, data flows, interfaces.
9. Operational concerns  — observability, rollout plan, rollback, on-call impact.
10. Risks & open questions — accordion of risks with severity badges.
11. Decision & next steps — what's approved, who owns what, dates.
12. Appendix             — interface specs, sample payloads, references.
```

Section 7 (Alternatives) is what separates a real design doc from a
proposal-as-conclusion. Don't skip it. If only one approach was considered,
say so and explain why (e.g. "constrained to current vendor").

## Status

Display prominently in the header. Use a pip + label:

```html
<dd><span class="pip pip--warning"></span> In Review</dd>
```

| Status   | Pip color    | Meaning                                |
|----------|--------------|----------------------------------------|
| Draft    | `pip--info`  | Author is still iterating              |
| In Review| `pip--warning`| Open for comments                      |
| Approved | `pip--success`| Decision locked, implementation can start |
| Superseded | `pip--low` | Replaced by a newer doc — link to it   |
| Archived | `pip--low`   | Historical; kept for context           |

## Components typically used

| Section            | Components                                          |
|--------------------|-----------------------------------------------------|
| Goals & non-goals  | Two-column compare grid                             |
| Current / Proposed | `architecture` block with Mermaid                   |
| Alternatives       | `tabs` (one per alternative) or vertical sections   |
| Detailed design    | Mermaid sequence diagrams, code blocks              |
| Operational        | Timeline for rollout, `accordion` for runbooks      |
| Risks              | `accordion` with severity `badge`s                  |
| Appendix           | Sortable table of interfaces / endpoints            |

## Mermaid diagram conventions

Pick one diagram style per concept and stick with it. Use:

- `flowchart LR` — high-level system component diagrams.
- `sequenceDiagram` — request flows, async interactions, retries.
- `erDiagram` — data model with relationships.
- `stateDiagram-v2` — state machines (job lifecycles, order status).
- `gantt` — only if dates matter; otherwise a timeline is lighter.

Keep diagrams under ~12 nodes. Larger diagrams stop being readable and become
decoration; split into multiple smaller ones (overview + zoomed-in views).

Always label edges with what flows over them (`HTTPS`, `gRPC`, `Kafka topic
xxx`). An unlabeled arrow doesn't tell the reader anything.

## Common mistakes

- **No "non-goals" section.** Without it, every reviewer asks "what about X?"
  Pre-empt by listing what is intentionally out of scope.
- **Skipping the current-state diagram.** Readers can't evaluate a delta if
  they don't know the baseline.
- **One alternative described in detail, others dismissed in one sentence.**
  Treat alternatives seriously — show the tradeoffs.
- **Mermaid used as Visio.** Don't try to fully art-direct mermaid for hero
  diagrams; if you need pixel-perfect, author the SVG in a real tool and embed.
- **No rollback plan.** Every operational change needs a rollback — and saying
  "we can deploy the previous version" is not a plan; specify what triggers it
  and who decides.

## Example skeleton

```html
<section id="summary" data-toc="サマリー">
  <h2 class="mt-0 pt-0 border-0">サマリー</h2>
  <p class="lead">認証バックエンドをAuth0からCognitoへ移行する。SLA要件と単一クラウド集約のため。期間: 2026Q3。</p>
</section>

<section id="context" data-toc="背景">
  <h2>背景</h2>
  <p>現状の課題、なぜ今、なぜこの方針。</p>
</section>

<section id="goals" data-toc="ゴールと非ゴール">
  <h2>ゴールと非ゴール</h2>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
    <div class="card">
      <h3 class="chart-card__title">Goals</h3>
      <ul><li>…</li></ul>
    </div>
    <div class="card">
      <h3 class="chart-card__title">Non-goals</h3>
      <ul><li>…</li></ul>
    </div>
  </div>
</section>

<section id="current" data-toc="現状アーキテクチャ">
  <h2>現状アーキテクチャ</h2>
  <div class="architecture"><pre class="mermaid">flowchart LR
    Web --> Auth0 --> User_DB
  </pre></div>
</section>

<section id="proposed" data-toc="提案アーキテクチャ">
  <h2>提案アーキテクチャ</h2>
  <div class="architecture"><pre class="mermaid">flowchart LR
    Web --> Cognito --> User_DB
    Web --> APIGW --> Lambda
  </pre></div>
</section>

<section id="alternatives" data-toc="代替案">
  <h2>代替案</h2>
  <div class="my-6" data-tabs>
    <ul class="tabs__list" role="tablist">
      <li role="presentation"><button class="tabs__trigger" role="tab" aria-selected="true"  aria-controls="alt-a" id="alt-trig-a">A: 自社実装</button></li>
      <li role="presentation"><button class="tabs__trigger" role="tab" aria-selected="false" aria-controls="alt-b" id="alt-trig-b">B: 別ベンダー継続</button></li>
    </ul>
    <div class="tabs__panel" id="alt-a" role="tabpanel" aria-labelledby="alt-trig-a" aria-hidden="false">…</div>
    <div class="tabs__panel" id="alt-b" role="tabpanel" aria-labelledby="alt-trig-b" aria-hidden="true">…</div>
  </div>
</section>
```

## ADR variant

Architecture Decision Records (ADRs) are a smaller, tighter cousin. Use this
shorter structure:

```
Status — Context — Decision — Consequences
```

ADRs live in `docs/adr/` in many repos. An HTML ADR can use the same base
template with most sections hidden — just header + four short sections + footer
referencing the previous ADR if this one supersedes one.
