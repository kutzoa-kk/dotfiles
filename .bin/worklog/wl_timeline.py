"""Decide which minutes count as work and turn them into intervals (no side effects).

Rules: docs/superpowers/specs/2026-10-04-worklog-calendar-design.md
"""
from collections import Counter, defaultdict
from datetime import timedelta

OTHER = "その他"
ORCA_BUNDLE = "com.stablyai.orca"
ONE_MIN = timedelta(minutes=1)


def _minute(sample):
    return sample["_ts"].replace(second=0, microsecond=0)


def _context(sample):
    return sample.get("front_bundle"), sample.get("window_title")


def _is_active(sample, cfg):
    return sample["idle_sec"] < cfg["thresholds"]["active_idle_sec"] and not sample["locked"]


def classify(sample, cfg):
    """Return (bucket, detail) when the front window counts as work, else None."""
    title = sample.get("window_title") or ""
    if any(pattern.lower() in title.lower() for pattern in cfg["exclude_title_patterns"]):
        return None
    bundle = sample.get("front_bundle")
    app = sample.get("front_app") or bundle
    detail = f"{app}: {title}" if title else app
    if bundle in cfg["other_apps"]:
        return OTHER, detail
    if bundle in cfg["project_apps"] and sample.get("orca_project"):
        return sample["orca_project"], (None if bundle == ORCA_BUNDLE else detail)
    return None


def _idle_run_credits(last_active, run, resumed, cfg):
    """Credit an idle stretch: all of it when reading resumed in the same window, else a grace."""
    if last_active is None or not run:
        return []
    bucket = classify(last_active, cfg)
    if bucket is None:
        return []
    t = cfg["thresholds"]
    last_input = run[0]["_ts"] - timedelta(seconds=run[0]["idle_sec"])
    reading = (resumed is not None
               and not any(s["locked"] for s in run)
               and _context(resumed) == _context(last_active)
               and resumed["_ts"] - last_input <= timedelta(minutes=t["reading_max_min"]))
    limit = None if reading else last_input + timedelta(minutes=t["grace_min"])
    return [(_minute(s),) + bucket for s in run if limit is None or s["_ts"] <= limit]


def human_minutes(samples, cfg):
    gap = timedelta(seconds=cfg["thresholds"]["sample_gap_sec"])
    credits, last_active, run, previous = [], None, [], None
    for s in samples:
        if previous is not None and s["_ts"] - previous > gap:
            credits += _idle_run_credits(last_active, run, None, cfg)
            last_active, run = None, []
        previous = s["_ts"]
        if _is_active(s, cfg):
            credits += _idle_run_credits(last_active, run, s, cfg)
            bucket = classify(s, cfg)
            if bucket is not None:
                credits.append((_minute(s),) + bucket)
            last_active, run = s, []
        else:
            run = run + [s]
    return credits + _idle_run_credits(last_active, run, None, cfg)


def agent_minutes(samples):
    credits = []
    for s in samples:
        per_task = defaultdict(Counter)
        for agent in s.get("agents", []):
            # Samples taken before task names were recorded have no "task".
            per_task[(agent["project"], agent.get("task"))][agent["type"]] += 1
        credits += [(_minute(s), bucket, counts) for bucket, counts in per_task.items()]
    return credits


def build_intervals(kind, credits, cfg):
    t = cfg["thresholds"]
    merge_gap = timedelta(minutes=t["merge_gap_min"])
    min_length = timedelta(minutes=t["min_event_min"])
    by_bucket = defaultdict(lambda: defaultdict(list))
    for minute, bucket, detail in credits:
        by_bucket[bucket][minute].append(detail)
    intervals = []
    for bucket, minutes in by_bucket.items():
        # Agents are counted per (project, task); people per project only.
        project, task = bucket if kind == "agent" else (bucket, None)
        groups = []
        for minute in sorted(minutes):
            if groups and minute - (groups[-1][-1] + ONE_MIN) < merge_gap:
                groups[-1].append(minute)
            else:
                groups.append([minute])
        for group in groups:
            start, end = group[0], group[-1] + ONE_MIN
            if end - start < min_length:
                continue
            details = [detail for minute in group for detail in minutes[minute]]
            intervals.append({"kind": kind, "project": project, "task": task,
                              "start": start, "end": end, "details": details})
    return sorted(intervals, key=lambda i: (i["start"], i["project"], i["task"] or ""))
