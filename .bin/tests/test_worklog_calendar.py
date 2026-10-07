"""wl_calendar: event shape, reconciliation with the ledger, gog command lines."""
import subprocess
import unittest
from collections import Counter
from types import SimpleNamespace

from worklog_fixtures import CFG, at, fake_gogs

import wl_calendar
from wl_timeline import OTHER

TASK = "計測記録の修正"


def interval(kind="human", project="dotfiles2", start=0, end=10, details=None, task=None):
    return {"kind": kind, "project": project, "task": task, "start": at(start), "end": at(end),
            "details": [] if details is None else details}


def ledger_entry(iv, event_id="ev1"):
    return {"id": event_id, "calendar": iv["kind"], "start": iv["start"].isoformat(),
            "end": iv["end"].isoformat(), "summary": wl_calendar.summary(iv),
            "description": wl_calendar.describe(iv)}


def legacy_entry(iv, event_id="ev1"):
    """A record written before the calendars were split: no calendar, no summary."""
    return {"id": event_id, "start": iv["start"].isoformat(), "end": iv["end"].isoformat(),
            "description": wl_calendar.describe(iv)}


class ShapeTest(unittest.TestCase):
    def test_summary_names_only_the_work(self):
        self.assertEqual(wl_calendar.summary(interval()), "dotfiles2")
        self.assertEqual(wl_calendar.summary(interval(project=OTHER)), "その他")
        self.assertEqual(wl_calendar.summary(interval(kind="agent", project="proj-b", task=TASK)), TASK)
        self.assertEqual(wl_calendar.summary(interval(kind="agent", project="proj-b")), "proj-b")

    def test_color(self):
        self.assertEqual(wl_calendar.color("dotfiles2", CFG), "9")
        self.assertEqual(wl_calendar.color(OTHER, CFG), "8")
        auto = wl_calendar.color("proj-b", CFG)
        self.assertIn(auto, wl_calendar.AUTO_COLORS)
        self.assertEqual(auto, wl_calendar.color("proj-b", CFG))

    def test_describe_agent_project_and_peak_concurrency(self):
        iv = interval(kind="agent", details=[Counter(claude=1), Counter(claude=2, codex=1)])
        self.assertEqual(wl_calendar.describe(iv), "dotfiles2 / claude ×2, codex ×1")

    def test_describe_human_top_windows(self):
        iv = interval(details=["Chrome: paper", "Chrome: paper", None, "Preview: a.pdf"])
        self.assertEqual(wl_calendar.describe(iv), "Chrome: paper（2分）\nPreview: a.pdf（1分）")

    def test_key(self):
        self.assertEqual(wl_calendar.interval_key(interval()), "human|dotfiles2|2026-10-05T10:00:00+09:00")
        self.assertEqual(wl_calendar.interval_key(interval(kind="agent", task=TASK)),
                         f"agent|dotfiles2|{TASK}|2026-10-05T10:00:00+09:00")
        self.assertEqual(wl_calendar.interval_key(interval(kind="agent")),
                         "agent|dotfiles2||2026-10-05T10:00:00+09:00")


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

    def test_legacy_human_record_gets_new_title(self):
        iv = interval()
        ledger = {wl_calendar.interval_key(iv): legacy_entry(iv)}
        self.assertEqual(wl_calendar.plan_actions([iv], ledger, self.window_start),
                         [("update", wl_calendar.interval_key(iv), iv)])

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
    def test_create_goes_to_the_calendar_of_its_kind(self):
        human, agent = interval(), interval(kind="agent", task=TASK)
        actions = [("create", wl_calendar.interval_key(iv), iv) for iv in (human, agent)]
        gogs = fake_gogs()
        ledger, errors = wl_calendar.apply_actions(actions, {}, gogs, CFG)
        self.assertEqual(errors, [])
        self.assertEqual(gogs["human"].calls, [("create", "dotfiles2", human["start"].isoformat(),
                                                human["end"].isoformat(), "", "9",
                                                wl_calendar.interval_key(human))])
        self.assertEqual([call[1] for call in gogs["agent"].calls], [TASK])
        self.assertEqual(ledger[wl_calendar.interval_key(agent)]["calendar"], "agent")

    def test_update_sends_title(self):
        old, new = interval(end=10), interval(end=20)
        key = wl_calendar.interval_key(old)
        gogs = fake_gogs()
        ledger, _ = wl_calendar.apply_actions([("update", key, new)], {key: legacy_entry(old)}, gogs, CFG)
        self.assertEqual(gogs["human"].calls, [("update", "ev1", new["end"].isoformat(), "", "dotfiles2")])
        self.assertEqual(ledger[key]["summary"], "dotfiles2")

    def test_failed_update_keeps_ledger_and_continues(self):
        old, other = interval(end=10), interval(project="proj-b")
        ledger = {wl_calendar.interval_key(old): ledger_entry(old)}
        actions = [("update", wl_calendar.interval_key(old), interval(end=20)),
                   ("create", wl_calendar.interval_key(other), other)]
        result, errors = wl_calendar.apply_actions(actions, ledger, fake_gogs(fail_on={"update"}), CFG)
        self.assertEqual(result[wl_calendar.interval_key(old)], ledger[wl_calendar.interval_key(old)])
        self.assertIn(wl_calendar.interval_key(other), result)
        self.assertEqual(len(errors), 1)

    def test_delete_removes_entry_without_touching_input(self):
        iv = interval(kind="agent", task=TASK)
        key = wl_calendar.interval_key(iv)
        ledger = {key: ledger_entry(iv)}
        gogs = fake_gogs()
        result, _ = wl_calendar.apply_actions([("delete", key, None)], ledger, gogs, CFG)
        self.assertEqual(result, {})
        self.assertIn(key, ledger)
        self.assertEqual(gogs["agent"].calls, [("delete", "ev1")])

    def test_legacy_agent_event_moves_to_agent_calendar(self):
        # Before the split, agent events lived in the human calendar under "agent|project|start".
        iv = interval(kind="agent", task=TASK)
        legacy_key = f"agent|dotfiles2|{iv['start'].isoformat()}"
        ledger = {legacy_key: legacy_entry(iv, "old1")}
        actions = wl_calendar.plan_actions([iv], ledger, at(-60))
        gogs = fake_gogs()
        result, errors = wl_calendar.apply_actions(actions, ledger, gogs, CFG)
        self.assertEqual(errors, [])
        self.assertEqual(gogs["human"].calls, [("delete", "old1")])
        self.assertEqual([call[0] for call in gogs["agent"].calls], ["create"])
        self.assertEqual(list(result), [wl_calendar.interval_key(iv)])

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
        event_id = gog.create("dotfiles2", "s", "e", "d", "9", "human|dotfiles2|s")
        self.assertEqual(event_id, "ev9")
        self.assertEqual(calls[0], [
            "gog", "calendar", "create", "cal@example.com", "--summary=dotfiles2",
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
        gog.update("ev1", "e", "d", "t")
        gog.delete("ev1")
        self.assertEqual(calls[0][:8], ["gog", "calendar", "update", "cal@example.com", "ev1", "--to=e",
                                        "--description=d", "--summary=t"])
        self.assertEqual(calls[1][:6], ["gog", "calendar", "delete", "cal@example.com", "ev1", "--force"])


if __name__ == "__main__":
    unittest.main()
