"""worklog.py: sample and sync end to end with a fake calendar."""
import fcntl
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from worklog_fixtures import CFG, WORKLOG_DIR, FakeGog, at, fake_gogs, sample, stored

import wl_store

spec = importlib.util.spec_from_file_location("worklog", WORKLOG_DIR / "worklog.py")
worklog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worklog)


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        agents = [{"project": "proj-b", "type": "codex", "task": "設計"}]
        for m in range(10):
            wl_store.append_sample(stored(sample(m, agents=agents)), self.dir)

    def test_first_sync_writes_each_kind_to_its_calendar(self):
        gogs = fake_gogs()
        self.assertEqual(worklog.cmd_sync(at(30), CFG, gogs, self.dir), 2)
        self.assertEqual([call[1] for call in gogs["human"].calls], ["dotfiles2"])
        self.assertEqual([call[1] for call in gogs["agent"].calls], ["設計"])
        self.assertEqual(len(wl_store.load_ledger(self.dir)), 2)

    def test_second_sync_changes_nothing(self):
        worklog.cmd_sync(at(30), CFG, fake_gogs(), self.dir)
        gogs = fake_gogs()
        self.assertEqual(worklog.cmd_sync(at(45), CFG, gogs, self.dir), 0)
        self.assertEqual(gogs["human"].calls + gogs["agent"].calls, [])

    def test_failures_go_to_error_log(self):
        worklog.cmd_sync(at(30), CFG, fake_gogs(fail_on={"create"}), self.dir)
        self.assertEqual(wl_store.load_ledger(self.dir), {})
        log = (self.dir / "errors.log").read_text(encoding="utf-8")
        self.assertEqual(log.count("create failed"), 2)

    def test_concurrent_sync_is_skipped(self):
        with open(self.dir / "sync.lock", "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            gogs = fake_gogs()
            self.assertEqual(worklog.cmd_sync(at(30), CFG, gogs, self.dir), 0)
        self.assertEqual(gogs["human"].calls + gogs["agent"].calls, [])
        self.assertEqual(wl_store.load_ledger(self.dir), {})

    def test_sample_appends_one_line(self):
        with mock.patch.object(worklog.wl_probe, "collect_sample", return_value=stored(sample(10))):
            worklog.cmd_sample(at(10), self.dir)
        loaded, _ = wl_store.load_samples(at(-1), self.dir)
        self.assertEqual(len(loaded), 11)


class InitCalendarTest(unittest.TestCase):
    def test_creates_only_missing_calendars(self):
        gog = FakeGog()
        created = worklog.cmd_init_calendar(at(0), {**CFG, "agent_calendar_id": ""}, gog)
        self.assertEqual(created, {"agent_calendar_id": "作業ログ（AI）@group.calendar.google.com"})
        self.assertEqual(gog.calls, [("create_calendar", "作業ログ（AI）", "Asia/Tokyo")])

    def test_nothing_missing_is_an_error(self):
        with self.assertRaises(worklog.wl_config.ConfigError):
            worklog.cmd_init_calendar(at(0), CFG, FakeGog())


if __name__ == "__main__":
    unittest.main()
