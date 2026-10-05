"""worklog.py: sample and sync end to end with a fake calendar."""
import fcntl
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from worklog_fixtures import CFG, WORKLOG_DIR, FakeGog, at, sample, stored

import wl_store

spec = importlib.util.spec_from_file_location("worklog", WORKLOG_DIR / "worklog.py")
worklog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worklog)


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        agents = [{"project": "proj-b", "type": "codex"}]
        for m in range(10):
            wl_store.append_sample(stored(sample(m, agents=agents)), self.dir)

    def test_first_sync_creates_human_and_agent_events(self):
        gog = FakeGog()
        self.assertEqual(worklog.cmd_sync(at(30), CFG, gog, self.dir), 2)
        self.assertEqual(sorted(call[1] for call in gog.calls), ["AI｜proj-b", "人｜dotfiles2"])
        self.assertEqual(len(wl_store.load_ledger(self.dir)), 2)

    def test_second_sync_changes_nothing(self):
        worklog.cmd_sync(at(30), CFG, FakeGog(), self.dir)
        gog = FakeGog()
        self.assertEqual(worklog.cmd_sync(at(45), CFG, gog, self.dir), 0)
        self.assertEqual(gog.calls, [])

    def test_failures_go_to_error_log(self):
        worklog.cmd_sync(at(30), CFG, FakeGog(fail_on={"create"}), self.dir)
        self.assertEqual(wl_store.load_ledger(self.dir), {})
        log = (self.dir / "errors.log").read_text(encoding="utf-8")
        self.assertEqual(log.count("create failed"), 2)

    def test_concurrent_sync_is_skipped(self):
        with open(self.dir / "sync.lock", "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            gog = FakeGog()
            self.assertEqual(worklog.cmd_sync(at(30), CFG, gog, self.dir), 0)
        self.assertEqual(gog.calls, [])
        self.assertEqual(wl_store.load_ledger(self.dir), {})

    def test_sample_appends_one_line(self):
        with mock.patch.object(worklog.wl_probe, "collect_sample", return_value=stored(sample(10))):
            worklog.cmd_sample(at(10), self.dir)
        loaded, _ = wl_store.load_samples(at(-1), self.dir)
        self.assertEqual(len(loaded), 11)


if __name__ == "__main__":
    unittest.main()
