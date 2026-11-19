"""skills-upstream.py を偽物の gh コマンドで動かし、記録との比較と置き換えを確かめる。本物の gh は呼ばない。"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".bin/skills-upstream.py"

# 偽物の gh。`gh api [-H ...] <endpoint>` だけを受け、FAKE_STATE の JSON から答える。
# state["files"]["<repo>|<commit>"] がその版のファイル一覧（パス→中身）。内容の指紋は中身から作る。
FAKE_GH = """#!/usr/bin/env python3
import hashlib, json, os, re, sys
from urllib.parse import unquote
state = json.load(open(os.environ["FAKE_STATE"]))
args = [a for a in sys.argv[2:] if not a.startswith("-H") and not a.startswith("Accept:")]
ep = unquote(args[-1])
m = re.match(r"repos/([^/]+/[^/]+)/(.*)", ep)
repo, rest = m.group(1), m.group(2)
if rest.startswith("commits?"):
    path = re.search(r"path=([^&]+)", rest).group(1)
    print(json.dumps([{"sha": state["latest"][repo + "|" + path]}]))
elif rest.startswith("git/trees/"):
    sha = rest[len("git/trees/"):].split("?")[0]
    files = state["files"][f"{repo}|{sha}"]
    tree = [{"path": p, "type": "blob", "sha": hashlib.sha1(c.encode()).hexdigest()} for p, c in files.items()]
    print(json.dumps({"tree": tree}))
elif rest.startswith("contents/"):
    path, ref = rest[len("contents/"):].split("?ref=")
    sys.stdout.write(state["files"][f"{repo}|{ref}"][path])
else:
    sys.exit("unknown endpoint: " + ep)
"""

OLD, NEW = "a" * 40, "b" * 40


class SkillsUpstreamTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / ".bin").mkdir()
        self.config = self.root / ".bin/skills-upstream.json"
        self.gh = self.root / "gh"
        self.gh.write_text(FAKE_GH)
        self.gh.chmod(0o755)
        self.state = self.root / "state.json"

    def write(self, skills, state):
        self.config.write_text(json.dumps({"skills": skills}))
        self.state.write_text(json.dumps(state))

    def run_script(self, *args):
        env = {**os.environ, "FAKE_STATE": str(self.state)}
        cmd = [sys.executable, str(SCRIPT), "--config", str(self.config), "--gh", str(self.gh), *args]
        return subprocess.run(cmd, env=env, capture_output=True, text=True)

    def mirror(self):
        return {"name": "swd", "repo": "o/r", "path": "Skills/swd", "commit": OLD, "mode": "mirror",
                "dest": "dotdir/skills/swd", "license": "LICENSE"}

    def adapted(self):
        return {"name": "slop", "repo": "o/s", "path": "references/ANTI.md", "commit": OLD, "mode": "adapted",
                "dest": "dotdir/skills/x/references/checklist.md"}

    def test_check_reports_current_when_latest_matches(self):
        self.write([self.mirror()], {"latest": {"o/r|Skills/swd": OLD}})
        result = self.run_script("check", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report[0]["status"], "current")
        self.assertEqual(report[0]["files"], [])

    def test_check_shows_only_content_diff_under_recorded_path(self):
        files = {
            f"o/r|{OLD}": {"Skills/swd/SKILL.md": "old line\n", "Skills/swd/same.md": "same\n",
                           "Skills/swd/gone.md": "bye\n", "Skills/other/SKILL.md": "x\n"},
            f"o/r|{NEW}": {"Skills/swd/SKILL.md": "new line\n", "Skills/swd/same.md": "same\n",
                           "Skills/swd/added.md": "hello\n", "Skills/other/SKILL.md": "unrelated\n"},
        }
        self.write([self.mirror()], {"latest": {"o/r|Skills/swd": NEW}, "files": files})
        report = json.loads(self.run_script("check", "--json").stdout)
        self.assertEqual(report[0]["status"], "behind")
        self.assertEqual(report[0]["latest"], NEW)
        changed = {f["filename"]: f["status"] for f in report[0]["files"]}
        self.assertEqual(changed, {"Skills/swd/SKILL.md": "modified", "Skills/swd/gone.md": "removed",
                                   "Skills/swd/added.md": "added"})

        text = self.run_script("check").stdout
        self.assertIn("-old line", text)
        self.assertIn("+new line", text)
        self.assertNotIn("unrelated", text)

    def test_check_treats_commit_without_content_change_as_current(self):
        same = {"Skills/swd/SKILL.md": "same\n"}
        self.write([self.mirror()], {"latest": {"o/r|Skills/swd": NEW},
                                     "files": {f"o/r|{OLD}": same, f"o/r|{NEW}": same}})
        report = json.loads(self.run_script("check", "--json").stdout)
        self.assertEqual(report[0]["status"], "current")
        self.assertEqual(report[0]["files"], [])

    def test_sync_replaces_mirror_and_advances_record(self):
        dest = self.root / "dotdir/skills/swd"
        dest.mkdir(parents=True)
        (dest / "stale.md").write_text("removed upstream")
        state = {
            "latest": {"o/r|Skills/swd": NEW},
            "files": {f"o/r|{NEW}": {"Skills/swd/SKILL.md": "new skill", "Skills/swd/references/a.md": "ref",
                                     "Skills/other/SKILL.md": "not mine", "LICENSE": "license text"}},
        }
        self.write([self.mirror()], state)
        result = self.run_script("sync", "swd")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((dest / "SKILL.md").read_text(), "new skill")
        self.assertEqual((dest / "references/a.md").read_text(), "ref")
        self.assertEqual((dest / "LICENSE").read_text(), "license text")
        self.assertFalse((dest / "stale.md").exists())
        self.assertFalse((dest / "other").exists())
        self.assertEqual(json.loads(self.config.read_text())["skills"][0]["commit"], NEW)

    def test_sync_with_ref_fetches_that_commit(self):
        state = {"files": {f"o/r|{OLD}": {"Skills/swd/SKILL.md": "pinned", "LICENSE": "l"}}}
        self.write([self.mirror()], state)
        result = self.run_script("sync", "swd", "--ref", OLD)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "dotdir/skills/swd/SKILL.md").read_text(), "pinned")

    def test_sync_refuses_adapted(self):
        dest = self.root / "dotdir/skills/x/references/checklist.md"
        dest.parent.mkdir(parents=True)
        dest.write_text("hand-edited")
        self.write([self.adapted()], {"latest": {"o/s|references/ANTI.md": NEW}})
        result = self.run_script("sync", "slop")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("adapted", result.stderr)
        self.assertEqual(dest.read_text(), "hand-edited")
        self.assertEqual(json.loads(self.config.read_text())["skills"][0]["commit"], OLD)

    def test_check_fails_loudly_when_gh_fails(self):
        self.write([self.mirror()], {"latest": {}})  # 偽物の gh が KeyError で非0終了する
        result = self.run_script("check", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("確認できていません", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_sync_unknown_name_fails(self):
        self.write([self.mirror()], {})
        result = self.run_script("sync", "nope")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
