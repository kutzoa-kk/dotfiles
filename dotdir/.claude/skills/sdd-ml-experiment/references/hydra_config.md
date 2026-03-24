# Hydra Configuration Templates

## conf/config.yaml (Main)

```yaml
defaults:
  - model: baseline
  - features: default
  - split: group_kfold
  - _self_

project_name: {{project_name}}
experiment_name: {{experiment_name}}
seed: 42
run_name: ${model.name}_${features.name}_${split.name}_seed${seed}

mlflow:
  tracking_uri: mlruns
  experiment_name: ${project_name}_${experiment_name}

data:
  raw_dir: data/raw
  processed_dir: data/processed
  schema_path: src/schema/feature_availability.yaml
  {{For each data source:}}
  # {{source_name}}_path: {{source_path}}

gates:
  phase_a:
    {{For each Phase A gate:}}
    # {{metric_name}}: {{threshold}}
  phase_b:
    {{For each Phase B gate:}}
    # {{metric_name}}: {{threshold}}
  phase_c:
    {{For each Phase C gate:}}
    # {{metric_name}}: {{threshold}}

hydra:
  run:
    dir: outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}_${run_name}
  sweep:
    dir: outputs/sweeps/${now:%Y-%m-%d}
    subdir: ${run_name}
```

## conf/model/baseline.yaml

```yaml
name: baseline
type: {{model_type — e.g., lightgbm}}
params:
  {{For LightGBM:}}
  n_estimators: 100
  learning_rate: 0.1
  max_depth: 6
  num_leaves: 31
  min_child_samples: 20
  subsample: 0.8
  colsample_bytree: 0.8
  random_state: ${seed}
  verbose: -1

  {{For XGBoost:}}
  # n_estimators: 100
  # learning_rate: 0.1
  # max_depth: 6
  # random_state: ${seed}

  {{For Linear:}}
  # alpha: 1.0  # Ridge/Lasso regularization
```

## conf/features/default.yaml

```yaml
name: default
source: src/schema/feature_availability.yaml
subset: inference_available
# Optional: feature groups for ablation studies
# groups:
#   demographic: [gender]
#   gait: [walk_features_*]
#   step: [step_features_*]
```

## conf/split/group_kfold.yaml

```yaml
name: group_kfold
method: GroupKFold
n_splits: 5
group_key: {{subject_id_field}}
# Optional stratification
# stratify_by: {{stratify_column}}
```

## conf/split/temporal.yaml (if temporal holdout)

```yaml
name: temporal
method: temporal_holdout
group_key: {{subject_id_field}}
cutoff_date: "{{cutoff_date}}"
# All data before cutoff → train, after → test
```

## Adding New Model Configs

To add a new model configuration (e.g., for Phase B hyperparameter tuning):

```bash
# Create conf/model/tuned_lgb.yaml
name: tuned_lgb
type: lightgbm
params:
  n_estimators: 500
  learning_rate: 0.05
  max_depth: 8
  num_leaves: 63
  random_state: ${seed}
```

Then run with: `uv run python scripts/run_phase_b.py model=tuned_lgb`

## Hydra Sweep Config (for systematic hyperparameter search)

```yaml
# conf/hydra/sweeper/optuna.yaml
hydra:
  sweeper:
    _target_: hydra_plugins.hydra_optuna_sweeper.OptunaSweeper
    direction: minimize
    n_trials: 50
    params:
      model.params.n_estimators: range(50, 500, 50)
      model.params.learning_rate: interval(0.01, 0.3)
      model.params.max_depth: range(3, 10)
```
