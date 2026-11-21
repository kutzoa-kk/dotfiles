"""Exercise sharing detection in isolated directories; never change live skills."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "dotdir/.claude/skills/share-claude-skills/scripts/check_sharing.py"
SPEC = importlib.util.spec_from_file_location("check_sharing", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SkillSharingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.home = self.root / "home"
        self.codex = self.root / "custom-codex"
        self.sources = self.repo / "dotdir/.claude/skills"
        self.sources.mkdir(parents=True)
        self.user_skills = self.home / ".agents/skills"
        self.user_skills.mkdir(parents=True)
        self.repo_skills = self.repo / ".agents/skills"
        self.repo_skills.mkdir(parents=True)
        (self.codex / "skills").mkdir(parents=True)

    def skill(self, name):
        source = self.sources / name
        source.mkdir()
        (source / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n")
        return source

    def check(self):
        return MODULE.check_sharing(self.repo, self.home, self.codex)

    def test_shared_means_same_directory_not_identical_content(self):
        source = self.skill("linked")
        (self.user_skills / source.name).symlink_to(source)
        self.skill("copy")
        copy = self.user_skills / "copy"
        copy.mkdir()
        (copy / "SKILL.md").write_bytes((self.sources / "copy/SKILL.md").read_bytes())
        report = self.check()
        self.assertEqual(report["shared"], ["linked"])
        self.assertEqual(report["unshared"], ["copy"])
        self.assertEqual(report["conflicts"][0]["reason"], "different_entry")

    def test_relative_repository_link_and_legacy_only(self):
        self.skill("local")
        (self.repo_skills / "local").symlink_to("../../dotdir/.claude/skills/local")
        source = self.skill("old")
        (self.codex / "skills/old").symlink_to(source)
        report = self.check()
        self.assertEqual(report["shared"], ["local"])
        self.assertEqual(report["legacy_only"], ["old"])

    def test_conflicts_survive_a_valid_link_in_another_scope(self):
        source = self.skill("mixed")
        (self.user_skills / "mixed").symlink_to(source)
        (self.codex / "skills/mixed").write_text("preserve me")
        report = self.check()
        self.assertEqual(report["shared"], ["mixed"])
        self.assertEqual(report["conflicts"][0]["scope"], "legacy")
        self.assertEqual((self.codex / "skills/mixed").read_text(), "preserve me")

    def test_broken_and_cyclic_links_are_reported_without_mutation(self):
        self.skill("broken")
        self.skill("cycle")
        broken = self.user_skills / "broken"
        broken.symlink_to(self.root / "absent")
        cycle = self.user_skills / "cycle"
        cycle.symlink_to("cycle")
        (self.sources / "bad-source").symlink_to("absent")
        report = self.check()
        self.assertEqual(report["broken_sources"], ["bad-source"])
        self.assertEqual(report["unshared"], ["broken", "cycle"])
        self.assertEqual([entry["reason"] for entry in report["conflicts"]],
                         ["broken_link", "broken_link"])
        self.assertEqual(os.readlink(cycle), "cycle")
        self.assertTrue(broken.is_symlink())

    def test_helper_and_hidden_directories_are_ignored(self):
        (self.sources / "learned").mkdir()
        self.skill(".system")
        self.skill("candidate")
        report = self.check()
        self.assertEqual(report["unshared"], ["candidate"])
        self.assertEqual(report["counts"]["unshared"], 1)

    def test_cli_respects_codex_home_and_errors_for_missing_source(self):
        source = self.skill("custom")
        (self.codex / "skills/custom").symlink_to(source)
        command = [sys.executable, str(SCRIPT), "--repo", str(self.repo),
                   "--home", str(self.home)]
        env = {**os.environ, "CODEX_HOME": str(self.codex)}
        result = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["legacy_only"], ["custom"])
        result = subprocess.run(command + ["--repo", str(self.root / "absent")],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("共有状況を確認できません", result.stderr)


if __name__ == "__main__":
    unittest.main()
