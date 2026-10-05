"""Settings: shared defaults in config.json (git) plus per-PC local.json."""
import json
from pathlib import Path

REPO_CONFIG = Path(__file__).resolve().parent / "config.json"
LOCAL_CONFIG = Path.home() / ".config/worklog/local.json"
# The dotfiles repo is public: personal values live only in local.json.
LOCAL_DEFAULTS = {"account": "", "calendar_id": "", "project_colors": {}}


class ConfigError(Exception):
    pass


def load_config(repo_path=REPO_CONFIG, local_path=LOCAL_CONFIG):
    shared = json.loads(Path(repo_path).read_text(encoding="utf-8"))
    local_path = Path(local_path)
    local = json.loads(local_path.read_text(encoding="utf-8")) if local_path.exists() else {}
    unknown = sorted(set(local) - set(LOCAL_DEFAULTS))
    if unknown:
        raise ConfigError(f"unknown keys in {local_path}: {unknown}")
    return {**shared, **LOCAL_DEFAULTS, **local}


def require(cfg, *keys):
    missing = [key for key in keys if not cfg.get(key)]
    if missing:
        raise ConfigError(f"set {', '.join(missing)} in {LOCAL_CONFIG}")
