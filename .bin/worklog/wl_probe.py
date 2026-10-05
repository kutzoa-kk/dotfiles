"""Observe the desk right now: input idle time, screen lock, front app, Orca state."""
import json
import plistlib
import re
import subprocess

IDLE_RE = re.compile(rb'"HIDIdleTime" = (\d+)')
LSAPPINFO_RE = re.compile(r'"(\w+)"="([^"]*)"')
NANOS_PER_SEC = 1_000_000_000


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


def parse_orca_ps(out):
    """Return (selected project, working agents) from `orca worktree ps --json`."""
    active, agents = None, []
    for worktree in json.loads(out)["result"]["worktrees"]:
        if worktree.get("isActive"):
            active = worktree["repo"]
        agents += [{"project": worktree["repo"], "type": agent.get("agentType") or "unknown"}
                   for agent in worktree.get("agents", []) if agent.get("state") == "working"]
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
    project, agents = parse_orca_ps(ps) if ps else (None, [])
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
