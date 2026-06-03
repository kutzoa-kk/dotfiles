# Audit / Code Review Report Structure

Use for security audits, code review summaries, compliance findings, technical
debt assessments, third-party dependency reviews.

The reader is a tech lead, security engineer, or auditor who needs to triage:
what's actually critical, what's noise, who owns the fix, what's the deadline.

## Canonical section order

```
1. Header                    — title, scope, auditor, date, status
2. Executive summary         — 3–5 sentences. Overall posture + top 3 issues.
3. Findings summary          — count by severity, KPI cards
4. Findings detail           — one card or accordion item per finding
5. Methodology & scope       — what was audited, what was not
6. Remediation plan          — owner + deadline per finding
7. Out-of-scope observations — noted but not formal findings
8. Appendix                  — tools used, references, full evidence
```

## Severity definitions

Define explicitly in the header or appendix. Don't assume the reader shares
your scale.

| Severity   | Badge class       | Definition                                       |
|------------|-------------------|--------------------------------------------------|
| Critical   | `badge--critical` | Exploitable now, immediate data / system impact  |
| High       | `badge--high`     | Significant impact, exploitable under conditions |
| Medium     | `badge--medium`   | Real risk, defense-in-depth concern              |
| Low        | `badge--low`      | Best practice deviation, minor risk              |
| Info       | `badge--low`      | Observation, no action required                  |

The severity model should be in the Methodology section. Some teams use CVSS;
some use OWASP risk rating; some use internal scales. Pick one, name it,
stick to it.

## Findings summary

KPI cards counting by severity. Number of findings is more useful than %.

```html
<div class="grid gap-4 my-6" style="grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));">
  <div class="kpi">
    <p class="kpi__label">Critical</p>
    <div class="kpi__value text-danger">2</div>
  </div>
  <div class="kpi">
    <p class="kpi__label">High</p>
    <div class="kpi__value text-warning">5</div>
  </div>
  <div class="kpi">
    <p class="kpi__label">Medium</p>
    <div class="kpi__value">11</div>
  </div>
  <div class="kpi">
    <p class="kpi__label">Low / Info</p>
    <div class="kpi__value">18</div>
  </div>
</div>
```

## Finding card structure

Every finding follows the same shape. Predictability lets readers scan.

```html
<details class="accordion">
  <details>
    <summary>
      <span class="font-mono text-sm">SEC-007</span>
      SSRF in image-fetch endpoint
      <span class="badge badge--critical">Critical</span>
    </summary>
    <div class="accordion__body">
      <dl class="grid grid-cols-[8rem_1fr] gap-x-4 gap-y-2 text-sm mb-4">
        <dt class="text-faint">影響</dt>           <dd>Internal metadata service reachable from user input.</dd>
        <dt class="text-faint">場所</dt>           <dd><code>src/handlers/image.ts:42</code></dd>
        <dt class="text-faint">再現手順</dt>       <dd>下記コードブロック参照</dd>
        <dt class="text-faint">推奨対応</dt>       <dd>URL ホワイトリスト + メタデータ IP 範囲ブロック</dd>
        <dt class="text-faint">担当</dt>           <dd>@security-team</dd>
        <dt class="text-faint">期限</dt>           <dd>2026-05-20</dd>
        <dt class="text-faint">参考</dt>           <dd><a href="https://owasp.org/...">OWASP SSRF</a></dd>
      </dl>
      <pre><code>// reproduction snippet</code></pre>
    </div>
  </details>
</details>
```

Fields every finding should have:
- ID (short, sortable — e.g. `SEC-001`, `PERF-014`)
- Title (one line, no jargon)
- Severity badge
- Affected location (file + line, or service / endpoint)
- Reproduction or evidence
- Recommended remediation
- Owner
- Target date
- References / CVE / standard violated (if applicable)

## Findings table for triage

When there are many findings, give readers a sortable / filterable table to
triage. Detailed cards still go below.

```html
<div class="my-6" data-sortable-table>
  <div class="table-toolbar no-print">
    <input type="search" placeholder="検索…" data-table-search>
    <select data-table-filter="severity">
      <option value="">Severity: All</option>
      <option value="critical">Critical</option>
      <option value="high">High</option>
    </select>
  </div>
  <table class="data-table">
    <thead>
      <tr>
        <th data-sort="string">ID</th>
        <th data-sort="string">Title</th>
        <th data-sort="string">Severity</th>
        <th data-sort="string">Owner</th>
        <th data-sort="date">Due</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>SEC-001</td><td>Stored XSS in comments</td><td><span class="badge badge--critical">Critical</span></td><td>@web</td><td>2026-05-18</td></tr>
      <tr><td>SEC-002</td><td>Missing CSRF on /transfer</td><td><span class="badge badge--high">High</span></td><td>@payments</td><td>2026-05-25</td></tr>
    </tbody>
  </table>
</div>
```

## Remediation plan section

Group findings by owner so each team gets a clear list. Show the timeline.

```html
<section id="plan" data-toc="対応計画">
  <h2>対応計画</h2>
  <div class="my-6" data-tabs>
    <ul class="tabs__list" role="tablist">
      <li role="presentation"><button class="tabs__trigger" role="tab" aria-selected="true"  aria-controls="plan-web" id="plan-trig-web">@web (4)</button></li>
      <li role="presentation"><button class="tabs__trigger" role="tab" aria-selected="false" aria-controls="plan-api" id="plan-trig-api">@api (7)</button></li>
    </ul>
    <div class="tabs__panel" id="plan-web" role="tabpanel" aria-labelledby="plan-trig-web" aria-hidden="false">
      <ol class="timeline">
        <li>
          <p class="timeline__date">2026-05-18</p>
          <p class="timeline__title">SEC-001 Stored XSS — 修正PR</p>
          <p>サニタイズ漏れの修正と回帰テスト追加。</p>
        </li>
      </ol>
    </div>
  </div>
</section>
```

## Common mistakes

- **No severity scale defined.** "Critical" means different things in different
  reports. Always include the definitions.
- **Severity inflation.** Mark only what's actually critical critical. Everything-critical
  reports get ignored.
- **No reproduction steps.** "There's an XSS somewhere" is not actionable.
- **No owner / no date.** Without these, the finding will live forever in the
  backlog.
- **Out-of-scope items mixed in.** Distinguish formal findings (which the team
  is on the hook for) from observations (suggestions). Different sections.
- **No "positive findings".** Note what's already good — e.g. "MFA is enforced
  for all admin accounts" — so the report isn't only criticism. Builds trust.

## Components typically used

| Section              | Components                                          |
|----------------------|-----------------------------------------------------|
| Executive summary    | `lead` paragraph                                    |
| Findings summary     | `grid` of `kpi` (one per severity)                  |
| Findings detail      | `accordion` of finding cards, or `card` per finding |
| Findings triage      | `data-table` sortable + filterable                  |
| Methodology          | description list, code blocks for queries / commands |
| Remediation plan     | `tabs` (by owner) containing `timeline`             |
| Out-of-scope         | `accordion`                                         |
| Appendix             | `data-table` of tools and versions used             |

## Anonymization

If the report will be shared externally, scrub:
- Real user IDs, emails, names from evidence.
- Internal hostnames, IP addresses, service names that reveal architecture.
- Anything covered by a confidentiality agreement.

Replace with synthetic-but-realistic values (`alice@example.com`, `db-prod-3`)
so reproduction steps still make sense.
