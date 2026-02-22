# Multiple Comparison Correction Methods

Detailed implementation reference for statistical corrections applied in the final report.

---

## When to Apply Corrections

Corrections are REQUIRED when:
- Testing more than one hypothesis (confirmatory or exploratory)
- Comparing more than two models or configurations
- Evaluating the same model on multiple metrics with significance tests

Corrections are NOT needed when:
- Reporting descriptive statistics only (mean, std, etc.)
- Single pre-registered hypothesis with single metric
- Exploratory analyses explicitly labeled as such

---

## Method 1: Bonferroni Correction

**When to use**: Conservative correction. Best when hypotheses are independent or when false positives are costly (e.g., medical/clinical).

**Formula**:
```
adjusted_α = α / n_comparisons
adjusted_p = min(raw_p * n_comparisons, 1.0)
```

**Python implementation**:
```python
def bonferroni_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[dict[str, float | bool]]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    adjusted_alpha = alpha / n
    results = []
    for p in p_values:
        adjusted_p = min(p * n, 1.0)
        results.append({
            "raw_p": p,
            "adjusted_p": adjusted_p,
            "adjusted_alpha": adjusted_alpha,
            "significant": adjusted_p < alpha,
        })
    return results
```

**Pros**: Simple, controls family-wise error rate (FWER)
**Cons**: Very conservative, may miss true effects

---

## Method 2: Benjamini-Hochberg FDR

**When to use**: Less conservative. Best when testing many hypotheses and some false positives are acceptable (e.g., feature selection, exploratory analysis).

**Formula**:
```
1. Sort p-values: p(1) ≤ p(2) ≤ ... ≤ p(n)
2. For each i, compute threshold: (i / n) * α
3. Find largest i where p(i) ≤ threshold
4. Reject all hypotheses with rank ≤ i
```

**Python implementation**:
```python
def benjamini_hochberg_correction(
    p_values: list[float],
    alpha: float = 0.05,
) -> list[dict[str, float | bool]]:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])

    # Compute adjusted p-values (step-up)
    adjusted = [0.0] * n
    prev_adj = 0.0
    for rank_minus_1 in range(n - 1, -1, -1):
        orig_idx, raw_p = indexed[rank_minus_1]
        rank = rank_minus_1 + 1
        adj_p = min(raw_p * n / rank, 1.0)
        if rank_minus_1 < n - 1:
            adj_p = min(adj_p, prev_adj)
        adjusted[orig_idx] = adj_p
        prev_adj = adj_p

    results = []
    for i, p in enumerate(p_values):
        results.append({
            "raw_p": p,
            "adjusted_p": adjusted[i],
            "significant": adjusted[i] < alpha,
        })
    return results
```

**Pros**: More powerful than Bonferroni, controls false discovery rate
**Cons**: Does not control FWER, assumes tests are independent or positively correlated

---

## Method Selection Guide

| Scenario | Recommended Method |
|----------|-------------------|
| Medical/clinical trial | Bonferroni |
| ≤ 5 comparisons | Bonferroni |
| > 5 comparisons | Benjamini-Hochberg |
| Exploratory analysis | Benjamini-Hochberg (or no correction, but label as exploratory) |
| Independent hypotheses | Either method |
| Correlated hypotheses | Bonferroni (more conservative) |

---

## Integration with Report Generator

The `generate_report.py` script applies corrections as follows:

1. Parse `02_METRICS.md` to determine correction method and α
2. If no method specified, default to Bonferroni for ≤ 5 comparisons, BH-FDR for > 5
3. Collect raw p-values from run metrics (if available)
4. Apply correction and include table in report
5. Update hypothesis status based on corrected significance

---

## Reporting Requirements (R10)

The report MUST include:
- [ ] Which correction method was used and why
- [ ] Number of comparisons (n)
- [ ] Original significance level (α)
- [ ] Raw AND adjusted p-values for each comparison
- [ ] Whether each comparison remains significant after correction
- [ ] Note if no correction was applied and rationale
