"""Files under ~/.local/state/worklog: samples, event ledger, error log."""
import json
from datetime import datetime
from pathlib import Path

STATE_DIR = Path.home() / ".local/state/worklog"
SAMPLE_PREFIX = "samples-"
LEDGER_NAME = "events.json"
PRIVATE_DIR_MODE = 0o700


def _sample_day(path):
    return path.stem[len(SAMPLE_PREFIX):]


def _ensure_private_dir(state_dir):
    # Samples hold window titles (mail subjects, document names): owner only.
    state_dir.mkdir(parents=True, exist_ok=True)
    state_dir.chmod(PRIVATE_DIR_MODE)


def append_sample(sample, state_dir=STATE_DIR):
    _ensure_private_dir(state_dir)
    line = json.dumps(sample, ensure_ascii=False) + "\n"
    # One write per line keeps a concurrent reader from seeing half a record.
    with open(state_dir / f"{SAMPLE_PREFIX}{sample['ts'][:10]}.jsonl", "a", encoding="utf-8") as f:
        f.write(line)


def load_samples(since, state_dir=STATE_DIR):
    """Return (samples at or after `since` sorted by time, messages for broken lines)."""
    samples, errors = [], []
    first_day = since.date().isoformat()
    for path in sorted(state_dir.glob(f"{SAMPLE_PREFIX}*.jsonl")):
        if _sample_day(path) < first_day:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                raw = json.loads(line)
                ts = datetime.fromisoformat(raw["ts"])
            except (ValueError, KeyError, TypeError) as exc:
                errors.append(f"{path.name}:{number}: {exc!r}")
                continue
            if ts >= since:
                samples.append({**raw, "_ts": ts})
    return sorted(samples, key=lambda s: s["_ts"]), errors


def load_ledger(state_dir=STATE_DIR):
    path = state_dir / LEDGER_NAME
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_ledger(ledger, state_dir=STATE_DIR):
    _ensure_private_dir(state_dir)
    tmp = state_dir / (LEDGER_NAME + ".tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(state_dir / LEDGER_NAME)


def log_error(message, now, state_dir=STATE_DIR):
    _ensure_private_dir(state_dir)
    with open(state_dir / "errors.log", "a", encoding="utf-8") as f:
        f.write(f"{now.isoformat(timespec='seconds')} {message}\n")


def prune_samples(before_day, state_dir=STATE_DIR):
    """Delete sample files dated before `before_day`."""
    for path in state_dir.glob(f"{SAMPLE_PREFIX}*.jsonl"):
        if _sample_day(path) < before_day.isoformat():
            path.unlink()
