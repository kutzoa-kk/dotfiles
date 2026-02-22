# Experiment Configuration Templates

## Hydra + MLflow (Default)

### conf/config.yaml

```yaml
defaults:
  - model: baseline
  - features: default
  - split: group_kfold
  - _self_

project_name: {{project_name}}
seed: 42
run_name: ${model.name}_${features.name}_${split.name}_seed${seed}

mlflow:
  tracking_uri: mlruns
  experiment_name: ${project_name}

data:
  raw_dir: data/raw
  processed_dir: data/processed
  schema_path: src/schema/feature_availability.yaml

hydra:
  run:
    dir: outputs/${now:%Y-%m-%d}/${now:%H-%M-%S}_${run_name}
  sweep:
    dir: outputs/sweeps/${now:%Y-%m-%d}
    subdir: ${run_name}
```

### conf/model/baseline.yaml

```yaml
name: baseline
type: lightgbm
params:
  n_estimators: 100
  learning_rate: 0.1
  max_depth: 6
  random_state: ${seed}
```

### conf/features/default.yaml

```yaml
name: default
source: src/schema/feature_availability.yaml
subset: inference_available
```

### conf/split/group_kfold.yaml

```yaml
name: group_kfold
method: GroupKFold
n_splits: 5
group_key: {{subject_id_field}}
```

### Artifact Logging Pattern

```python
import mlflow
from omegaconf import OmegaConf

def log_experiment(cfg, model, split_index, pipeline):
    mlflow.set_experiment(cfg.mlflow.experiment_name)
    with mlflow.start_run(run_name=cfg.run_name):
        mlflow.log_dict(OmegaConf.to_container(cfg), "hydra_config.yaml")
        mlflow.log_dict(split_index, "split_index.json")
        mlflow.sklearn.log_model(model, "model")
        mlflow.sklearn.log_model(pipeline, "preprocessing_pipeline")
```

## Weights & Biases Alternative

### conf/config.yaml (W&B variant)

```yaml
defaults:
  - model: baseline
  - features: default
  - split: group_kfold
  - _self_

project_name: {{project_name}}
seed: 42
run_name: ${model.name}_${features.name}_${split.name}_seed${seed}

wandb:
  project: ${project_name}
  entity: {{wandb_entity}}
```

### Artifact Logging Pattern (W&B)

```python
import wandb
from omegaconf import OmegaConf

def log_experiment(cfg, model, split_index, pipeline):
    wandb.init(
        project=cfg.wandb.project,
        name=cfg.run_name,
        config=OmegaConf.to_container(cfg),
    )
    artifact = wandb.Artifact("split_index", type="dataset")
    artifact.add(wandb.Table(dataframe=split_index), "split_index")
    wandb.log_artifact(artifact)
    wandb.finish()
```

## src/data_access.py Template

```python
"""Centralized data access layer.

All raw data reads MUST go through this module.
Direct reads from data/raw/ in any other file are prohibited.
"""

from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def load_raw(filename: str) -> pd.DataFrame:
    """Load a raw data file. Read-only access."""
    filepath = RAW_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Raw data not found: {filepath}")

    suffix = filepath.suffix.lower()
    loaders = {
        ".parquet": pd.read_parquet,
        ".csv": pd.read_csv,
        ".feather": pd.read_feather,
    }
    loader = loaders.get(suffix)
    if loader is None:
        raise ValueError(f"Unsupported format: {suffix}")
    return loader(filepath)


def save_processed(df: pd.DataFrame, filename: str, fmt: str = "parquet") -> Path:
    """Save processed data to data/processed/."""
    filepath = PROCESSED_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "parquet":
        df.to_parquet(filepath, index=False)
    elif fmt == "csv":
        df.to_csv(filepath, index=False)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    return filepath
```
