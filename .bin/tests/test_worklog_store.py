"""wl_config and wl_store: settings merge and state files."""
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from worklog_fixtures import BASE, sample, stored

import wl_config
import wl_store


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.shared = self.tmp / "config.json"
        self.shared.write_text(json.dumps({"timezone": "Asia/Tokyo"}), encoding="utf-8")
        self.local = self.tmp / "local.json"

    def test_local_values_override_defaults(self):
        self.local.write_text(json.dumps({"account": "me@example.com"}), encoding="utf-8")
        cfg = wl_config.load_config(self.shared, self.local)
        self.assertEqual(cfg["timezone"], "Asia/Tokyo")
        self.assertEqual(cfg["account"], "me@example.com")
        self.assertEqual(cfg["calendar_id"], "")
        self.assertEqual(cfg["project_colors"], {})

    def test_missing_local_file_gives_empty_personal_values(self):
        cfg = wl_config.load_config(self.shared, self.local)
        self.assertEqual(cfg["account"], "")

    def test_unknown_local_key_is_rejected(self):
        self.local.write_text(json.dumps({"acount": "typo"}), encoding="utf-8")
        with self.assertRaises(wl_config.ConfigError):
            wl_config.load_config(self.shared, self.local)

    def test_require_names_missing_keys(self):
        with self.assertRaisesRegex(wl_config.ConfigError, "calendar_id"):
            wl_config.require({"account": "a", "calendar_id": ""}, "account", "calendar_id")


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_samples_round_trip_across_midnight(self):
        before = sample(-11)  # 2026-10-05 09:49
        late = dict(stored(sample(0)), ts="2026-10-04T23:59:05+09:00")
        wl_store.append_sample(late, self.dir)
        wl_store.append_sample(stored(before), self.dir)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()),
                         ["samples-2026-10-04.jsonl", "samples-2026-10-05.jsonl"])
        loaded, errors = wl_store.load_samples(BASE - timedelta(days=1), self.dir)
        self.assertEqual(errors, [])
        self.assertEqual([s["ts"] for s in loaded], [late["ts"], before["ts"]])
        self.assertEqual(loaded[1]["_ts"], before["_ts"])

    def test_samples_before_since_are_skipped(self):
        for m in (0, 10):
            wl_store.append_sample(stored(sample(m)), self.dir)
        loaded, _ = wl_store.load_samples(BASE + timedelta(minutes=5), self.dir)
        self.assertEqual(len(loaded), 1)

    def test_broken_lines_are_reported_and_skipped(self):
        wl_store.append_sample(stored(sample(0)), self.dir)
        with open(self.dir / "samples-2026-10-05.jsonl", "a", encoding="utf-8") as f:
            f.write('{"ts": "2026-10-05T10:01\n42\n')
        loaded, errors = wl_store.load_samples(BASE, self.dir)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(len(errors), 2)
        self.assertIn("samples-2026-10-05.jsonl:2", errors[0])

    def test_ledger_round_trip_and_missing_file(self):
        self.assertEqual(wl_store.load_ledger(self.dir), {})
        ledger = {"human|dotfiles2|x": {"id": "ev1", "start": "s", "end": "e", "description": ""}}
        wl_store.save_ledger(ledger, self.dir)
        self.assertEqual(wl_store.load_ledger(self.dir), ledger)

    def test_prune_samples_deletes_old_days_only(self):
        for day in ("2026-09-01", "2026-10-05"):
            (self.dir / f"samples-{day}.jsonl").write_text("", encoding="utf-8")
        wl_store.prune_samples(date(2026, 9, 5), self.dir)
        self.assertEqual([p.name for p in self.dir.iterdir()], ["samples-2026-10-05.jsonl"])

    def test_log_error_appends_with_timestamp(self):
        wl_store.log_error("first", BASE, self.dir)
        wl_store.log_error("second", BASE, self.dir)
        lines = (self.dir / "errors.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, ["2026-10-05T10:00:00+09:00 first", "2026-10-05T10:00:00+09:00 second"])


if __name__ == "__main__":
    unittest.main()
