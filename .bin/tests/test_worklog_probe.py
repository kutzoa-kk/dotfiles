"""wl_probe: parsing command output and assembling one sample."""
import json
import plistlib
import unittest

from worklog_fixtures import BASE, CHROME

import wl_probe

ASN = "ASN:0x0-0x2c02c:"
ORCA_PS = {"result": {"worktrees": [
    {"repo": "dotfiles2", "isActive": True, "agents": [
        {"agentType": "claude", "state": "working"},
        {"agentType": "claude", "state": "done"}]},
    {"repo": "proj-b", "isActive": False, "agents": [
        {"agentType": "codex", "state": "working"}]},
    {"repo": "proj-c", "isActive": False},
]}}
WINDOWS = {"result": {"windows": [
    {"index": 1, "isMinimized": False, "title": "Background"},
    {"index": 2, "isMinimized": True, "title": "Minimized"},
    {"index": 0, "isMinimized": False, "title": "paper - Google Scholar"},
]}}


def fake_runner(orca_up=True):
    outputs = {
        ("ioreg", "-c", "IOHIDSystem"): b'    | |   "HIDIdleTime" = 13231015208\n',
        ("ioreg", "-n", "Root", "-d1", "-a"): plistlib.dumps({"IOConsoleUsers": [{"kCGSSessionOnConsoleKey": True}]}),
        ("lsappinfo", "front"): (ASN + "\n").encode(),
        ("lsappinfo", "info", "-only", "bundleid", ASN): b'"CFBundleIdentifier"="com.google.Chrome"\n',
        ("lsappinfo", "info", "-only", "name", ASN): b'"LSDisplayName"="Google Chrome"\n',
        ("orca", "worktree", "ps", "--json"): json.dumps(ORCA_PS).encode() if orca_up else None,
        ("orca", "computer", "list-windows", "--app", CHROME, "--json"):
            json.dumps(WINDOWS).encode() if orca_up else None,
    }
    return lambda cmd: outputs[tuple(cmd)]


class ParseTest(unittest.TestCase):
    def test_idle_is_whole_seconds(self):
        self.assertEqual(wl_probe.parse_idle_sec(b'"HIDIdleTime" = 13231015208'), 13)

    def test_idle_missing_raises(self):
        with self.assertRaises(wl_probe.ProbeError):
            wl_probe.parse_idle_sec(b"nothing")

    def test_locked_only_when_flag_present(self):
        locked = plistlib.dumps({"IOConsoleUsers": [{"CGSSessionScreenIsLocked": True}]})
        unlocked = plistlib.dumps({"IOConsoleUsers": [{"kCGSSessionOnConsoleKey": True}]})
        self.assertTrue(wl_probe.parse_locked(locked))
        self.assertFalse(wl_probe.parse_locked(unlocked))

    def test_lsappinfo_pairs(self):
        self.assertEqual(wl_probe.parse_lsappinfo(b'"LSDisplayName"="Google Chrome"\n'),
                         {"LSDisplayName": "Google Chrome"})

    def test_orca_ps_active_project_and_working_agents(self):
        project, agents = wl_probe.parse_orca_ps(json.dumps(ORCA_PS).encode())
        self.assertEqual(project, "dotfiles2")
        self.assertEqual(agents, [{"project": "dotfiles2", "type": "claude"},
                                  {"project": "proj-b", "type": "codex"}])

    def test_window_title_is_front_visible_window(self):
        self.assertEqual(wl_probe.parse_window_title(json.dumps(WINDOWS).encode()),
                         "paper - Google Scholar")

    def test_empty_title_becomes_none(self):
        out = json.dumps({"result": {"windows": [{"index": 0, "isMinimized": False, "title": ""}]}})
        self.assertIsNone(wl_probe.parse_window_title(out.encode()))


class CollectTest(unittest.TestCase):
    def test_collects_one_sample(self):
        s = wl_probe.collect_sample(BASE, fake_runner())
        self.assertEqual(s, {
            "ts": "2026-10-05T10:00:00+09:00", "idle_sec": 13, "locked": False,
            "front_bundle": CHROME, "front_app": "Google Chrome",
            "window_title": "paper - Google Scholar", "orca_project": "dotfiles2",
            "agents": [{"project": "dotfiles2", "type": "claude"},
                       {"project": "proj-b", "type": "codex"}],
        })

    def test_orca_down_leaves_orca_fields_empty(self):
        s = wl_probe.collect_sample(BASE, fake_runner(orca_up=False))
        self.assertEqual((s["orca_project"], s["agents"], s["window_title"]), (None, [], None))
        self.assertEqual(s["front_bundle"], CHROME)

    def test_missing_system_output_raises(self):
        def broken(cmd):
            return None if cmd[0] == "ioreg" else fake_runner()(cmd)
        with self.assertRaises(wl_probe.ProbeError):
            wl_probe.collect_sample(BASE, broken)


if __name__ == "__main__":
    unittest.main()
