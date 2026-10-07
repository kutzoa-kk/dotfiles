"""Observe the desk right now: input idle time, screen lock, front app, Orca state."""
import json
import plistlib
import re
import subprocess

IDLE_RE = re.compile(rb'"HIDIdleTime" = (\d+)')
LSAPPINFO_RE = re.compile(r'"(\w+)"="([^"]*)"')
NANOS_PER_SEC = 1_000_000_000
# Claude Code starts its terminal title with this while waiting for input
# (a spinner glyph while working). Orca's own state can stay "working" after the turn ends.
IDLE_TITLE_MARK = "✳"


class ProbeError(Exception):
    pass


def run(cmd, timeout=10):
    """Return stdout, or None when the command fails (e.g. Orca is not running)."""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _required(runner, cmd):
    out = runner(cmd)
    if out is None:
        raise ProbeError(f"command failed: {' '.join(cmd)}")
    return out


def parse_idle_sec(ioreg_out):
    match = IDLE_RE.search(ioreg_out)
    if not match:
        raise ProbeError("HIDIdleTime not found in ioreg output")
    return int(match.group(1)) // NANOS_PER_SEC


def parse_locked(root_plist):
    # The lock flag only appears while the screen is locked.
    users = plistlib.loads(root_plist).get("IOConsoleUsers", [])
    return any(user.get("CGSSessionScreenIsLocked") for user in users)


def parse_lsappinfo(out):
    return dict(LSAPPINFO_RE.findall(out.decode("utf-8")))


def parse_idle_panes(out):
    """Pane keys (tabId:leafId, as in Orca's agent paneKey) whose title says waiting for input."""
    return {f"{t['tabId']}:{t['leafId']}" for t in json.loads(out)["result"]["terminals"]
            if (t.get("title") or "").startswith(IDLE_TITLE_MARK)}


def parse_orca_ps(out, idle_panes=frozenset()):
    """Return (selected project, working agents) from `orca worktree ps --json`."""
    active, agents = None, []
    for worktree in json.loads(out)["result"]["worktrees"]:
        if worktree.get("isActive"):
            active = worktree["repo"]
        agents += [{"project": worktree["repo"], "type": agent.get("agentType") or "unknown"}
                   for agent in worktree.get("agents", [])
                   if agent.get("state") == "working" and agent.get("paneKey") not in idle_panes]
    return active, agents


def parse_window_title(out):
    """Title of the front window: the lowest index that is not minimized."""
    windows = [w for w in json.loads(out)["result"]["windows"] if not w.get("isMinimized")]
    if not windows:
        return None
    return min(windows, key=lambda w: w.get("index", 0)).get("title") or None


def collect_sample(now, runner=run):
    idle_sec = parse_idle_sec(_required(runner, ["ioreg", "-c", "IOHIDSystem"]))
    locked = parse_locked(_required(runner, ["ioreg", "-n", "Root", "-d1", "-a"]))
    asn = _required(runner, ["lsappinfo", "front"]).decode("utf-8").strip()
    bundle = parse_lsappinfo(_required(runner, ["lsappinfo", "info", "-only", "bundleid", asn])).get("CFBundleIdentifier")
    app = parse_lsappinfo(_required(runner, ["lsappinfo", "info", "-only", "name", asn])).get("LSDisplayName")
    ps = runner(["orca", "worktree", "ps", "--json"])
    # Unreadable titles are no evidence of idleness: fall back to Orca's state alone.
    terminals = runner(["orca", "terminal", "list", "--json"]) if ps else None
    idle_panes = parse_idle_panes(terminals) if terminals else frozenset()
    project, agents = parse_orca_ps(ps, idle_panes) if ps else (None, [])
    windows = runner(["orca", "computer", "list-windows", "--app", bundle, "--json"]) if ps and bundle else None
    return {
        "ts": now.isoformat(timespec="seconds"),
        "idle_sec": idle_sec,
        "locked": locked,
        "front_bundle": bundle,
        "front_app": app,
        "window_title": parse_window_title(windows) if windows else None,
        "orca_project": project,
        "agents": agents,
    }
