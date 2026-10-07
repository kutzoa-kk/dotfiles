#!/usr/bin/env python3
"""Record human and agent working time to Google Calendar.

Design: docs/superpowers/specs/2026-10-04-worklog-calendar-design.md
"""
import argparse
import fcntl
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import wl_calendar  # noqa: E402
import wl_config  # noqa: E402
import wl_probe  # noqa: E402
import wl_store  # noqa: E402
import wl_timeline  # noqa: E402

# Read a little before the window so intervals that start inside it are never truncated.
LOOKBACK_MARGIN = timedelta(hours=2)
LOCK_NAME = "sync.lock"
# Which local.json key holds the calendar for each kind of work.
CALENDAR_KEYS = {"human": "calendar_id", "agent": "agent_calendar_id"}


def cmd_sample(now, state_dir=wl_store.STATE_DIR, runner=wl_probe.run):
    wl_store.append_sample(wl_probe.collect_sample(now, runner), state_dir)


def cmd_sync(now, cfg, gogs, state_dir=wl_store.STATE_DIR):
    # Two syncs reading the same ledger would both create the same events.
    state_dir.mkdir(parents=True, exist_ok=True)
    with open(state_dir / LOCK_NAME, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"{now.isoformat(timespec='seconds')} sync: another sync is running; skipped")
            return 0
        return _sync_locked(now, cfg, gogs, state_dir)


def _sync_locked(now, cfg, gogs, state_dir):
    t = cfg["thresholds"]
    window_start = now - timedelta(hours=t["window_hours"])
    samples, broken = wl_store.load_samples(window_start - LOOKBACK_MARGIN, state_dir)
    intervals = (wl_timeline.build_intervals("human", wl_timeline.human_minutes(samples, cfg), cfg)
                 + wl_timeline.build_intervals("agent", wl_timeline.agent_minutes(samples), cfg))
    ledger = wl_store.load_ledger(state_dir)
    actions = wl_calendar.plan_actions(intervals, ledger, window_start)
    ledger, failed = wl_calendar.apply_actions(actions, ledger, gogs, cfg)
    retention = timedelta(days=t["retention_days"])
    wl_store.save_ledger(wl_calendar.prune_ledger(ledger, now - retention), state_dir)
    wl_store.prune_samples((now - retention).date(), state_dir)
    for message in broken + failed:
        wl_store.log_error(message, now, state_dir)
    print(f"{now.isoformat(timespec='seconds')} sync: {len(actions)} actions, {len(failed)} failed")
    return len(actions)


def cmd_init_calendar(now, cfg, gog):
    """Create only the calendars whose id is not set yet; return {local.json key: new id}."""
    missing = {kind: key for kind, key in CALENDAR_KEYS.items() if not cfg[key]}
    if not missing:
        raise wl_config.ConfigError(f"all calendar ids are already set in {wl_config.LOCAL_CONFIG}")
    created = {}
    for kind, key in missing.items():
        name = cfg["calendar_names"][kind]
        created[key] = gog.create_calendar(name, cfg["timezone"])
        print(f"created {name!r}: {created[key]}")
        print(f'add "{key}": "{created[key]}" to {wl_config.LOCAL_CONFIG}')
    return created


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["sample", "sync", "init-calendar"])
    command = parser.parse_args(argv).command
    now = datetime.now().astimezone()
    try:
        if command == "sample":
            cmd_sample(now)
            return 0
        cfg = wl_config.load_config()
        if command == "sync":
            wl_config.require(cfg, "account", *CALENDAR_KEYS.values())
            gogs = {kind: wl_calendar.Gog(cfg["account"], cfg[key]) for kind, key in CALENDAR_KEYS.items()}
            cmd_sync(now, cfg, gogs)
        else:
            wl_config.require(cfg, "account")
            cmd_init_calendar(now, cfg, wl_calendar.Gog(cfg["account"], ""))
    except Exception as exc:
        # launchd has no terminal: leave a trace in errors.log, then fail loudly.
        wl_store.log_error(f"{command}: {exc!r}", now)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
