"""wl_calendar: event shape, reconciliation with the ledger, gog command lines."""
import subprocess
import unittest
from collections import Counter
from types import SimpleNamespace

from worklog_fixtures import CFG, FakeGog, at

import wl_calendar
from wl_timeline import OTHER


def interval(kind="human", project="dotfiles2", start=0, end=10, details=None):
    return {"kind": kind, "project": project, "start": at(start), "end": at(end),
            "details": [] if details is None else details}


def ledger_entry(iv, event_id="ev1"):
    return {"id": event_id, "start": iv["start"].isoformat(), "end": iv["end"].isoformat(),
            "description": wl_calendar.describe(iv)}


class ShapeTest(unittest.TestCase):
    def test_summary(self):
        self.assertEqual(wl_calendar.summary(interval()), "人｜dotfiles2")
        self.assertEqual(wl_calendar.summary(interval(project=OTHER)), "人｜その他")
        self.assertEqual(wl_calendar.summary(interval(kind="agent", project="proj-b")), "AI｜proj-b")

    def test_color(self):
        self.assertEqual(wl_calendar.color("dotfiles2", CFG), "9")
        self.assertEqual(wl_calendar.color(OTHER, CFG), "8")
        auto = wl_calendar.color("proj-b", CFG)
        self.assertIn(auto, wl_calendar.AUTO_COLORS)
        self.assertEqual(auto, wl_calendar.color("proj-b", CFG))

    def test_describe_agent_peak_concurrency(self):
        iv = interval(kind="agent", details=[Counter(claude=1), Counter(claude=2, codex=1)])
        self.assertEqual(wl_calendar.describe(iv), "claude ×2, codex ×1")

    def test_describe_human_top_windows(self):
        iv = interval(details=["Chrome: paper", "Chrome: paper", None, "Preview: a.pdf"])
        self.assertEqual(wl_calendar.describe(iv), "Chrome: paper（2分）\nPreview: a.pdf（1分）")

    def test_key(self):
        self.assertEqual(wl_calendar.interval_key(interval()), "human|dotfiles2|2026-10-05T10:00:00+09:00")


class PlanTest(unittest.TestCase):
    window_start = at(-60)

    def test_new_interval_is_created(self):
        iv = interval()
        self.assertEqual(wl_calendar.plan_actions([iv], {}, self.window_start),
                         [("create", wl_calendar.interval_key(iv), iv)])

    def test_unchanged_interval_needs_nothing(self):
        iv = interval()
        ledger = {wl_calendar.interval_key(iv): ledger_entry(iv)}
        self.assertEqual(wl_calendar.plan_actions([iv], ledger, self.window_start), [])

    def test_longer_interval_is_updated(self):
        old, new = interval(end=10), interval(end=20)
        ledger = {wl_calendar.interval_key(old): ledger_entry(old)}
        self.assertEqual(wl_calendar.plan_actions([new], ledger, self.window_start),
                         [("update", wl_calendar.interval_key(new), new)])

    def test_vanished_interval_is_deleted(self):
        iv = interval()
        ledger = {wl_calendar.interval_key(iv): ledger_entry(iv)}
        self.assertEqual(wl_calendar.plan_actions([], ledger, self.window_start),
                         [("delete", wl_calendar.interval_key(iv), None)])

    def test_outside_window_is_left_alone(self):
        old = interval(start=-120, end=-110)
        ledger = {wl_calendar.interval_key(old): ledger_entry(old)}
        self.assertEqual(wl_calendar.plan_actions([old], {}, self.window_start), [])
        self.assertEqual(wl_calendar.plan_actions([], ledger, self.window_start), [])


class ApplyTest(unittest.TestCase):
    def test_create_records_event_id(self):
        iv = interval()
        key = wl_calendar.interval_key(iv)
        gog = FakeGog()
        ledger, errors = wl_calendar.apply_actions([("create", key, iv)], {}, gog, CFG)
        self.assertEqual(errors, [])
        self.assertEqual(ledger[key]["id"], "ev1")
        self.assertEqual(gog.calls[0], ("create", "人｜dotfiles2", iv["start"].isoformat(),
                                        iv["end"].isoformat(), "", "9", key))

    def test_failed_update_keeps_ledger_and_continues(self):
        old, other = interval(end=10), interval(project="proj-b")
        ledger = {wl_calendar.interval_key(old): ledger_entry(old)}
        actions = [("update", wl_calendar.interval_key(old), interval(end=20)),
                   ("create", wl_calendar.interval_key(other), other)]
        result, errors = wl_calendar.apply_actions(actions, ledger, FakeGog(fail_on={"update"}), CFG)
        self.assertEqual(result[wl_calendar.interval_key(old)], ledger[wl_calendar.interval_key(old)])
        self.assertIn(wl_calendar.interval_key(other), result)
        self.assertEqual(len(errors), 1)

    def test_delete_removes_entry_without_touching_input(self):
        iv = interval()
        key = wl_calendar.interval_key(iv)
        ledger = {key: ledger_entry(iv)}
        result, _ = wl_calendar.apply_actions([("delete", key, None)], ledger, FakeGog(), CFG)
        self.assertEqual(result, {})
        self.assertIn(key, ledger)

    def test_prune_ledger_by_start(self):
        old, new = interval(start=-100, end=-90), interval()
        ledger = {"old": ledger_entry(old), "new": ledger_entry(new)}
        self.assertEqual(list(wl_calendar.prune_ledger(ledger, at(-50))), ["new"])


class GogTest(unittest.TestCase):
    def make(self, stdout='{"id": "ev9"}', returncode=0):
        calls = []

        def runner(cmd, **kwargs):
            calls.append(cmd)
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="boom")
        return wl_calendar.Gog("me@example.com", "cal@example.com", runner), calls

    def test_create_command_line(self):
        gog, calls = self.make()
        event_id = gog.create("人｜dotfiles2", "s", "e", "d", "9", "human|dotfiles2|s")
        self.assertEqual(event_id, "ev9")
        self.assertEqual(calls[0], [
            "gog", "calendar", "create", "cal@example.com", "--summary=人｜dotfiles2",
            "--from=s", "--to=e", "--description=d", "--event-color=9",
            "--private-prop=worklog_key=human|dotfiles2|s", "--transparency=transparent",
            "--account=me@example.com", "--json", "--no-input"])

    def test_nested_id_is_found(self):
        gog, _ = self.make(stdout='{"event": {"id": "ev7"}}')
        self.assertEqual(gog.create("t", "s", "e", "d", "1", "k"), "ev7")

    def test_missing_id_raises(self):
        gog, _ = self.make(stdout="{}")
        with self.assertRaises(wl_calendar.GogError):
            gog.create("t", "s", "e", "d", "1", "k")

    def test_nonzero_exit_raises(self):
        gog, _ = self.make(returncode=1)
        with self.assertRaisesRegex(wl_calendar.GogError, "boom"):
            gog.delete("ev1")

    def test_timeout_becomes_gog_error(self):
        def runner(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 60)
        gog = wl_calendar.Gog("me@example.com", "cal@example.com", runner)
        with self.assertRaises(wl_calendar.GogError):
            gog.delete("ev1")

    def test_non_json_output_becomes_gog_error(self):
        gog, _ = self.make(stdout="not json")
        with self.assertRaises(wl_calendar.GogError):
            gog.create("t", "s", "e", "d", "1", "k")

    def test_update_and_delete_command_lines(self):
        gog, calls = self.make(stdout="")
        gog.update("ev1", "e", "d")
        gog.delete("ev1")
        self.assertEqual(calls[0][:6], ["gog", "calendar", "update", "cal@example.com", "ev1", "--to=e"])
        self.assertEqual(calls[1][:6], ["gog", "calendar", "delete", "cal@example.com", "ev1", "--force"])


if __name__ == "__main__":
    unittest.main()
