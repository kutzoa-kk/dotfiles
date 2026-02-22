# Experiment Audit: Backend Configurations

API patterns for querying experiment tracking backends. The audit scripts abstract backends via the `RunInfo` immutable class.

---

## RunInfo Abstraction

```python
class RunInfo:
    """Immutable experiment run record."""

    def __init__(
        self,
        run_id: str,
        status: str,
        start_time: str,
        end_time: str | None,
        tags: dict[str, str],
        metrics: dict[str, float],
        is_deleted: bool,
    ):
        self.run_id = run_id
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.tags = tags
        self.metrics = metrics
        self.is_deleted = is_deleted
```

---

## MLflow Backend

### Connection

```python
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType

client = MlflowClient(tracking_uri="http://localhost:5000")
# Or from environment: MLFLOW_TRACKING_URI
```

### Query All Runs (Including Deleted)

```python
all_runs = client.search_runs(
    experiment_ids=[experiment_id],
    run_view_type=ViewType.ALL,
    max_results=10000,
)
```

### Query Active Runs Only

```python
active_runs = client.search_runs(
    experiment_ids=[experiment_id],
    run_view_type=ViewType.ACTIVE_ONLY,
)
```

### Convert to RunInfo

```python
def mlflow_to_run_info(run) -> RunInfo:
    return RunInfo(
        run_id=run.info.run_id,
        status=run.info.status,
        start_time=datetime.fromtimestamp(
            run.info.start_time / 1000
        ).isoformat(),
        end_time=(
            datetime.fromtimestamp(run.info.end_time / 1000).isoformat()
            if run.info.end_time else None
        ),
        tags=dict(run.data.tags),
        metrics=dict(run.data.metrics),
        is_deleted=(run.info.lifecycle_stage == "deleted"),
    )
```

### Detect Deleted Runs

```python
deleted = [r for r in all_runs if r.info.lifecycle_stage == "deleted"]
```

---

## Weights & Biases Backend

### Connection

```python
import wandb

api = wandb.Api()
# Requires WANDB_API_KEY environment variable
```

### Query All Runs

```python
runs = api.runs(
    path=f"{entity}/{project}",
    per_page=1000,
)
```

### Convert to RunInfo

```python
def wandb_to_run_info(run) -> RunInfo:
    return RunInfo(
        run_id=run.id,
        status=run.state,
        start_time=run.created_at,
        end_time=run.heartbeat_at,
        tags=dict(run.config) | {"wandb_tags": ",".join(run.tags)},
        metrics=dict(run.summary),
        is_deleted=(run.state == "deleted"),
    )
```

### Detect Deleted Runs

W&B does not have a direct "deleted" view. Instead:
1. Compare known run IDs against current API results
2. Store run ID manifest in `data/processed/run_manifest.json`
3. Missing IDs indicate deletion

```python
# Save manifest after each audit
manifest_path = project_dir / "data" / "processed" / "run_manifest.json"
```

---

## Neptune Backend

### Connection

```python
import neptune

project = neptune.init_project(
    project="workspace/project-name",
)
```

### Query Runs

```python
runs_table = project.fetch_runs_table().to_pandas()
```

### Convert to RunInfo

```python
def neptune_to_run_info(row) -> RunInfo:
    return RunInfo(
        run_id=row["sys/id"],
        status=row.get("sys/state", "unknown"),
        start_time=str(row.get("sys/creation_time", "")),
        end_time=str(row.get("sys/modification_time", "")),
        tags={"neptune_tags": str(row.get("sys/tags", []))},
        metrics={
            k: v for k, v in row.items()
            if k.startswith("metrics/") and isinstance(v, (int, float))
        },
        is_deleted=row.get("sys/trashed", False),
    )
```

---

## CLI Usage Patterns

### MLflow

```bash
python experiment_audit.py \
    --project-dir . \
    --backend mlflow \
    --tracking-uri http://localhost:5000 \
    --experiment-name my-experiment
```

### W&B

```bash
python experiment_audit.py \
    --project-dir . \
    --backend wandb \
    --entity my-team \
    --wandb-project my-project
```

### Filesystem Fallback

If no backend is available, the audit can check for run metadata in local files:

```bash
python experiment_audit.py \
    --project-dir . \
    --backend local \
    --runs-dir data/processed/runs/
```
