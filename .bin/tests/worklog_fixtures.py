"""Shared builders for worklog tests."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKLOG_DIR = Path(__file__).resolve().parents[1] / "worklog"
sys.path.insert(0, str(WORKLOG_DIR))

JST = timezone(timedelta(hours=9))
BASE = datetime(2026, 10, 5, 10, 0, tzinfo=JST)
ORCA = "com.stablyai.orca"
CHROME = "com.google.Chrome"
VSCODE = "com.microsoft.VSCode"

CFG = {
    "timezone": "Asia/Tokyo",
    "calendar_name": "作業ログ",
    "project_apps": [ORCA, CHROME],
    "other_apps": [VSCODE],
    "exclude_title_patterns": ["YouTube"],
    "thresholds": {
        "active_idle_sec": 60, "reading_max_min": 30, "grace_min": 2,
        "sample_gap_sec": 120, "merge_gap_min": 5, "min_event_min": 3,
        "window_hours": 48, "retention_days": 30,
    },
    "account": "me@example.com",
    "calendar_id": "cal@example.com",
    "project_colors": {"dotfiles2": "9"},
}


def at(minute):
    return BASE + timedelta(minutes=minute)


def sample(minute, idle=0, locked=False, bundle=ORCA, app="Orca", title="Orca",
           project="dotfiles2", agents=()):
    ts = at(minute) + timedelta(seconds=5)
    return {"ts": ts.isoformat(), "_ts": ts, "idle_sec": idle, "locked": locked,
            "front_bundle": bundle, "front_app": app, "window_title": title,
            "orca_project": project, "agents": list(agents)}


def idle_run(first, last, since_minute, **kw):
    """Idle samples for minutes first..last; the last input was at since_minute."""
    return [sample(m, idle=(m - since_minute) * 60, **kw) for m in range(first, last + 1)]


def stored(s):
    """The sample as written to disk (without the parsed _ts)."""
    return {k: v for k, v in s.items() if k != "_ts"}


class FakeGog:
    """Records calls instead of talking to Google; fails on the named operations."""

    def __init__(self, fail_on=()):
        self.calls, self.fail_on, self.created = [], set(fail_on), 0

    def _record(self, name, *args):
        self.calls.append((name,) + args)
        if name in self.fail_on:
            from wl_calendar import GogError
            raise GogError(f"{name} failed")

    def create(self, summary, start, end, description, color, key):
        self._record("create", summary, start, end, description, color, key)
        self.created += 1
        return f"ev{self.created}"

    def update(self, event_id, end, description):
        self._record("update", event_id, end, description)

    def delete(self, event_id):
        self._record("delete", event_id)
