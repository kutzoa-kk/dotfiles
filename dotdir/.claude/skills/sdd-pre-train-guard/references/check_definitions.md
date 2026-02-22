# Pre-Train Guard: Check Definitions

Five automated checks that must ALL pass before training begins. Each check enforces one or more SDD prime rules (R3 Leakage, R4 Validation, R6 Split).

---

## Check 1: Feature Leakage (R3)

**Rule enforced**: No inference-unavailable feature may reach the training pipeline.

**How it works**:
1. Parse `src/schema/feature_availability.yaml` to get `inference_unavailable` + `auxiliary_targets` lists
2. Extract column names from the training script's data-loading call (AST or regex)
3. Compute `leaked = forbidden ∩ actual_columns`

**Pass condition**: `len(leaked) == 0`

**Fail output**:
```
[FAIL] Feature Leakage: LEAKED variables found: ['future_label', 'post_treatment_score']
```

**Fix procedure**:
1. Open `feature_availability.yaml` and verify lists are correct
2. Remove leaked columns from training script's feature selection
3. If a leaked column is actually available at inference, move it to `inference_available`
4. Re-run check

---

## Check 2: Split Policy Consistency (R6)

**Rule enforced**: The CV splitter used in code must match the documented split policy.

**How it works**:
1. Parse `docs/specs/05_SPLIT_POLICY.md` to extract:
   - CV strategy name (e.g., `GroupKFold`, `StratifiedKFold`)
   - Number of folds
   - Split unit / group column
2. AST-parse the training script to find splitter instantiation:
   - Look for imports from `sklearn.model_selection`
   - Match class name and constructor arguments
3. Compare documented vs actual

**Pass condition**: Splitter class name and key parameters match.

**Fail output**:
```
[FAIL] Split Policy Consistency: Expected GroupKFold(n_splits=5) but found KFold(n_splits=10)
```

**Fix procedure**:
1. If the code is wrong: update the splitter to match `05_SPLIT_POLICY.md`
2. If the spec is outdated: update `05_SPLIT_POLICY.md` and record deviation in `00_HYPOTHESES.md`
3. Never silently change both

---

## Check 3: Preprocessing Inside Folds (R3, R4)

**Rule enforced**: Data-dependent preprocessing (fit/transform) must occur INSIDE cross-validation folds via Pipeline or equivalent.

**How it works**:
1. AST-parse the training script
2. Collect all `.fit()` and `.fit_transform()` calls on known preprocessors:
   - `StandardScaler`, `MinMaxScaler`, `RobustScaler`
   - `LabelEncoder`, `OrdinalEncoder`, `OneHotEncoder`
   - `SimpleImputer`, `KNNImputer`
   - `PCA`, `TruncatedSVD`
   - Custom transformers with `fit` method
3. Check if each call is inside a `Pipeline` or `ColumnTransformer` context
4. Flag any `.fit()` call at module level or before the CV loop

**Pass condition**: All `.fit()` calls are inside Pipeline/ColumnTransformer or inside the CV loop body.

**Fail output**:
```
[FAIL] Preprocessing Inside Folds: StandardScaler.fit() called at line 45 outside Pipeline
```

**Fix procedure**:
1. Wrap the preprocessor in a `sklearn.pipeline.Pipeline`
2. Move fit calls inside the cross-validation loop
3. Use `Pipeline([('scaler', StandardScaler()), ('model', model)])` pattern

---

## Check 4: Validation Artifact (R4)

**Rule enforced**: A validation report must exist before training can proceed.

**How it works**:
1. Check for `data/processed/validation_report.json` existence
2. Verify the file is valid JSON
3. Verify it contains required keys: `timestamp`, `schema_version`, `checks`
4. Verify `checks` array is non-empty and all checks have `passed: true`

**Pass condition**: File exists, is valid JSON, contains required keys, all checks passed.

**Fail output**:
```
[FAIL] Validation Artifact: data/processed/validation_report.json not found
```
or
```
[FAIL] Validation Artifact: 2 of 5 checks failed in validation_report.json
```

**Fix procedure**:
1. Run the data validation pipeline: `python src/schema/data_validation.py`
2. Fix any schema violations
3. Re-generate validation_report.json
4. Re-run check

---

## Check 5: Feature Schema Exists (R3, R4)

**Rule enforced**: The feature availability schema must exist and be non-empty.

**How it works**:
1. Check `src/schema/feature_availability.yaml` exists
2. Parse YAML and verify structure:
   - Top-level `features` key exists
   - `inference_available` list is non-empty
   - `inference_unavailable` list exists (may be empty)

**Pass condition**: File exists, valid YAML, `inference_available` is non-empty.

**Fail output**:
```
[FAIL] Feature Schema: feature_availability.yaml missing or empty inference_available list
```

**Fix procedure**:
1. Run `sdd-ml-init` skill to generate the schema
2. Or manually create `feature_availability.yaml` with the required structure
3. Populate `inference_available` with features that will be available at inference time

---

## Exit Code Summary

| Scenario | Exit Code |
|----------|-----------|
| All 5 checks pass | 0 |
| Any check fails | 1 |
| Invalid arguments / missing required files | 1 |
