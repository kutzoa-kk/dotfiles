# Compliance Requirements -- AFib Classification

## Data Handling

- All personally identifiable information must be removed or pseudonymized before model training.
- Raw data access is restricted to `src/data_access.py`.
- `record_id` is a pseudonymized code, not a real patient identifier.

## Regulatory Framework

### Research Context
- Ethics committee approval number: (TBD)
- Data use agreement reference: (TBD)
- Data collection facility: (TBD)

### Data Privacy
- ECG data contains cardiac measurement values -- health-related personal data
- Dataset contains no direct identifiers (names, addresses)
- `record_id` is a pseudonymized identifier
- Age and other demographics are quasi-identifiers -- published results must ensure k-anonymity >= 5

### Clinical Validity
- AF diagnosis labels are assumed to be clinician-verified
- Model predictions are NOT intended for clinical diagnosis without validation
- Any deployment requires additional regulatory review (e.g., FDA, PMDA)

## Audit Trail

- All data transformations are recorded with reproducible seeds
- Split assignments are saved to `data/processed/split_index.json` and `data/processed/holdout_split.json`
- Feature availability schema is enforced by `src/schema/leakage_check.py`
- All experimental runs are preserved (never delete unfavorable results)

## Reproducibility

- All random seeds are fixed and documented
- CV split seed: 42
- Hold-out split seed: 123
- Model random state: 42
- Python environment: requirements tracked in project pyproject.toml
