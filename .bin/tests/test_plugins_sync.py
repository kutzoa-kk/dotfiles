"""plugins-sync.py を偽物の claude コマンドで動かし、実行する命令の順番を確かめる。本物の claude は呼ばない。"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".bin/plugins-sync.py"

# 偽物の claude。状態は FAKE_STATE の JSON、受け取った引数は FAKE_LOG に1行ずつ書く。
FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys
state_p, log_p = os.environ["FAKE_STATE"], os.environ["FAKE_LOG"]
state = json.load(open(state_p))
args = sys.argv[1:]
if args[-1] == "--json":
    key = "marketplaces" if args[1] == "marketplace" else "plugins"
    print(json.dumps(state[key]))
    sys.exit(0)
with open(log_p, "a") as f:
    f.write(" ".join(args) + "\\n")
if args[1:3] == ["marketplace", "add"]:
    name = state["add_names"].get(args[3])
    if name:
        state["marketplaces"].append({"name": name})
        json.dump(state, open(state_p, "w"))
"""


def plugin(pid, enabled=True):
    return {"id": pid, "enabled": enabled, "scope": "user"}


class PluginsSyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.claude = self.tmp / "claude"
        self.claude.write_text(FAKE_CLAUDE)
        self.claude.chmod(0o755)
        self.state = self.tmp / "state.json"
        self.log = self.tmp / "log.txt"
        self.git = self.tmp / "git.json"
        self.runtime = self.tmp / "runtime.json"

    def run_sync(self, git, runtime, state, *flags):
        self.git.write_text(json.dumps(git))
        self.runtime.write_text(json.dumps(runtime))
        self.state.write_text(json.dumps(state))
        env = {**os.environ, "FAKE_STATE": str(self.state), "FAKE_LOG": str(self.log)}
        cmd = [sys.executable, str(SCRIPT), "--git", str(self.git), "--runtime", str(self.runtime),
               "--claude", str(self.claude), *flags]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        calls = self.log.read_text().splitlines() if self.log.exists() else []
        return result, calls

    def test_new_machine_adds_marketplaces_then_installs_and_enables(self):
        git = {
            "enabledPlugins": {
                "ecc@ecc": True,
                "pubmed@anthropic-plugin-directory": True,
                "data@knowledge-work-plugins": True,
                "superpowers@claude-plugins-official": True,
                "context7@claude-plugins-official": False,
            },
            "extraKnownMarketplaces": {
                "ecc": {"source": {"source": "git", "url": "https://example.com/ecc.git"}},
                "knowledge-work-plugins": {
                    "source": {"source": "github", "repo": "anthropics/knowledge-work-plugins"},
                    "autoUpdate": True,
                },
            },
        }
        state = {
            "marketplaces": [{"name": "claude-plugins-official"}, {"name": "local-only"}],
            "plugins": [plugin("superpowers@claude-plugins-official", False), plugin("foo@local-only")],
            "add_names": {"https://example.com/ecc.git": "ecc", "anthropics/knowledge-work-plugins": "knowledge-work-plugins"},
        }
        result, calls = self.run_sync(git, {"model": "keep-me"}, state, "--yes")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [
            "plugin marketplace add https://example.com/ecc.git",
            "plugin marketplace add anthropics/knowledge-work-plugins",
            "plugin install ecc@ecc -y",
            "plugin install pubmed -y",
            "plugin install data@knowledge-work-plugins -y",
            "plugin enable superpowers@claude-plugins-official",
        ])
        runtime = json.loads(self.runtime.read_text())
        self.assertEqual(runtime["model"], "keep-me")
        self.assertIs(runtime["extraKnownMarketplaces"]["knowledge-work-plugins"]["autoUpdate"], True)
        self.assertIn("このマシンにだけあるプラグイン: foo@local-only", result.stdout)
        self.assertIn("このマシンにだけある取得元: local-only", result.stdout)

    def test_disables_when_git_says_false(self):
        git = {"enabledPlugins": {"context7@claude-plugins-official": False}}
        state = {"marketplaces": [{"name": "claude-plugins-official"}],
                 "plugins": [plugin("context7@claude-plugins-official", True)], "add_names": {}}
        result, calls = self.run_sync(git, {}, state, "--yes")
        self.assertEqual(calls, ["plugin disable context7@claude-plugins-official"])

    def test_synced_machine_does_nothing(self):
        git = {
            "enabledPlugins": {"ecc@ecc": True},
            "extraKnownMarketplaces": {"ecc": {"source": {"source": "git", "url": "u"}, "autoUpdate": True}},
        }
        runtime = {"extraKnownMarketplaces": {"ecc": {"source": {"source": "git", "url": "u"}, "autoUpdate": True}}}
        state = {"marketplaces": [{"name": "ecc"}, {"name": "claude-plugins-official"}],
                 "plugins": [plugin("ecc@ecc")], "add_names": {}}
        result, calls = self.run_sync(git, runtime, state, "--yes")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertIn("差分なし", result.stdout)

    def test_dry_run_changes_nothing(self):
        git = {"enabledPlugins": {"ecc@ecc": True},
               "extraKnownMarketplaces": {"ecc": {"source": {"source": "git", "url": "u"}, "autoUpdate": True}}}
        state = {"marketplaces": [{"name": "claude-plugins-official"}], "plugins": [], "add_names": {"u": "ecc"}}
        result, calls = self.run_sync(git, {}, state, "--dry-run")
        self.assertEqual(calls, [])
        self.assertEqual(json.loads(self.runtime.read_text()), {})
        self.assertIn("導入: ecc@ecc", result.stdout)

    def test_skips_plugins_when_marketplace_did_not_register(self):
        git = {"enabledPlugins": {"x@broken": True},
               "extraKnownMarketplaces": {"broken": {"source": {"source": "github", "repo": "o/broken"}}}}
        state = {"marketplaces": [{"name": "claude-plugins-official"}], "plugins": [], "add_names": {}}
        result, calls = self.run_sync(git, {}, state, "--yes")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(calls, ["plugin marketplace add o/broken"])
        self.assertIn("飛ばしました（取得元 broken がありません）", result.stdout)


if __name__ == "__main__":
    unittest.main()
