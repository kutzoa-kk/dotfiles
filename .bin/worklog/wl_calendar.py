"""Map intervals to calendar events and reconcile them through the gog CLI."""
import json
import subprocess
import zlib
from collections import Counter
from datetime import datetime

from wl_timeline import OTHER

OTHER_COLOR = "8"  # graphite
AUTO_COLORS = ("1", "2", "3", "4", "5", "6", "7", "9", "10", "11")
MAX_DETAIL_LINES = 5
GOG_TIMEOUT_SEC = 60


class GogError(Exception):
    pass


def interval_key(interval):
    parts = [interval["kind"], interval["project"]]
    if interval["kind"] == "agent":
        parts.append(interval["task"] or "")
    return "|".join(parts + [interval["start"].isoformat()])


def summary(interval):
    # The calendar tells human from agent, so the title only names the work.
    if interval["kind"] == "agent":
        return interval["task"] or interval["project"]
    return interval["project"]


def color(project, cfg):
    if project == OTHER:
        return OTHER_COLOR
    configured = cfg["project_colors"].get(project)
    return configured or AUTO_COLORS[zlib.crc32(project.encode("utf-8")) % len(AUTO_COLORS)]


def describe(interval):
    if interval["kind"] == "agent":
        peak = Counter()
        for counts in interval["details"]:
            for agent_type, n in counts.items():
                peak[agent_type] = max(peak[agent_type], n)
        agents = ", ".join(f"{agent_type} ×{n}" for agent_type, n in sorted(peak.items()))
        return f"{interval['project']} / {agents}"
    windows = Counter(detail for detail in interval["details"] if detail)
    return "\n".join(f"{detail}（{n}分）" for detail, n in windows.most_common(MAX_DETAIL_LINES))


def plan_actions(intervals, ledger, window_start):
    wanted = {interval_key(i): i for i in intervals if i["start"] >= window_start}
    actions = []
    for key, interval in sorted(wanted.items()):
        record = ledger.get(key)
        if record is None:
            actions.append(("create", key, interval))
        elif ((record["end"], record["description"], record.get("summary"))
              != (interval["end"].isoformat(), describe(interval), summary(interval))):
            actions.append(("update", key, interval))
    for key, record in sorted(ledger.items()):
        if key not in wanted and datetime.fromisoformat(record["start"]) >= window_start:
            actions.append(("delete", key, None))
    return actions


def _record(event_id, interval):
    return {"id": event_id, "calendar": interval["kind"], "start": interval["start"].isoformat(),
            "end": interval["end"].isoformat(), "summary": summary(interval),
            "description": describe(interval)}


def _calendar(record):
    # Records written before the calendars were split all live in the human calendar.
    return record.get("calendar", "human")


def apply_actions(actions, ledger, gogs, cfg):
    """Return (new ledger, error messages). A failed action leaves its entry as it was.

    gogs maps "human" / "agent" to the Gog of that calendar.
    """
    result, errors = dict(ledger), []
    for action, key, interval in actions:
        try:
            if action == "create":
                event_id = gogs[interval["kind"]].create(
                    summary(interval), interval["start"].isoformat(), interval["end"].isoformat(),
                    describe(interval), color(interval["project"], cfg), key)
                result[key] = _record(event_id, interval)
            elif action == "update":
                gogs[_calendar(ledger[key])].update(ledger[key]["id"], interval["end"].isoformat(),
                                                    describe(interval), summary(interval))
                result[key] = _record(ledger[key]["id"], interval)
            else:
                gogs[_calendar(ledger[key])].delete(ledger[key]["id"])
                result = {k: v for k, v in result.items() if k != key}
        except GogError as exc:
            errors.append(f"{action} {key}: {exc}")
    return result, errors


def prune_ledger(ledger, before):
    return {k: v for k, v in ledger.items() if datetime.fromisoformat(v["start"]) >= before}


def _find_id(payload, nested):
    for candidate in (payload, payload.get(nested)):
        if isinstance(candidate, dict) and candidate.get("id"):
            return candidate["id"]
    raise GogError(f"no id in gog output (keys: {sorted(payload)})")


class Gog:
    def __init__(self, account, calendar_id, runner=subprocess.run):
        self.account, self.calendar_id, self.runner = account, calendar_id, runner

    def _call(self, *args):
        cmd = ["gog", "calendar", *args, f"--account={self.account}", "--json", "--no-input"]
        try:
            result = self.runner(cmd, capture_output=True, text=True, timeout=GOG_TIMEOUT_SEC, check=False)
            if result.returncode != 0:
                raise GogError(f"{args[0]}: {(result.stderr or result.stdout).strip()}")
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            # Anything else would escape apply_actions and lose the ledger for this run.
            raise GogError(f"{args[0]}: {exc!r}") from exc

    def create(self, summary, start, end, description, color, key):
        payload = self._call("create", self.calendar_id, f"--summary={summary}", f"--from={start}",
                             f"--to={end}", f"--description={description}", f"--event-color={color}",
                             f"--private-prop=worklog_key={key}", "--transparency=transparent")
        return _find_id(payload, "event")

    def update(self, event_id, end, description, summary):
        self._call("update", self.calendar_id, event_id, f"--to={end}", f"--description={description}",
                   f"--summary={summary}")

    def delete(self, event_id):
        self._call("delete", self.calendar_id, event_id, "--force")

    def create_calendar(self, name, timezone):
        return _find_id(self._call("create-calendar", name, f"--timezone={timezone}"), "calendar")
