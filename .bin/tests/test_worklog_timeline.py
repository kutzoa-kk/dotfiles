"""wl_timeline: which minutes count as work, and how they become intervals."""
import unittest
from collections import Counter

from worklog_fixtures import CFG, CHROME, VSCODE, at, idle_run, sample

from wl_timeline import OTHER, agent_minutes, build_intervals, human_minutes


def human_spans(samples):
    return [(i["project"], i["start"], i["end"])
            for i in build_intervals("human", human_minutes(samples, CFG), CFG)]


def active(first, last, **kw):
    return [sample(m, **kw) for m in range(first, last + 1)]


class ReadingGapTest(unittest.TestCase):
    def test_resumed_in_same_window_counts_the_gap(self):
        s = active(0, 4) + idle_run(5, 14, 4) + [sample(15)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(16))])

    def test_gap_of_exactly_30_minutes_counts(self):
        s = [sample(0)] + idle_run(1, 29, 0) + [sample(30)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(31))])

    def test_gap_over_30_minutes_keeps_only_grace(self):
        s = [sample(0)] + idle_run(1, 30, 0) + [sample(31)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(3))])

    def test_lock_keeps_only_grace(self):
        s = active(0, 4) + idle_run(5, 7, 4) + idle_run(8, 20, 4, locked=True) + [sample(21)]
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(7))])

    def test_resume_in_other_window_keeps_only_grace(self):
        s = active(0, 4) + idle_run(5, 14, 4) + active(15, 19, title="Other")
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(7)), ("dotfiles2", at(15), at(20))])

    def test_unresolved_gap_at_end_keeps_only_grace(self):
        s = active(0, 4) + idle_run(5, 12, 4)
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(7))])

    def test_sleep_gap_is_not_counted(self):
        s = active(0, 4) + active(30, 34)
        self.assertEqual(human_spans(s), [("dotfiles2", at(0), at(5)), ("dotfiles2", at(30), at(35))])


class ClassifyTest(unittest.TestCase):
    def test_excluded_title_is_not_counted(self):
        s = active(0, 9, bundle=CHROME, app="Google Chrome", title="Cats - youtube")
        self.assertEqual(human_spans(s), [])

    def test_other_apps_count_without_orca(self):
        s = active(0, 4, bundle=VSCODE, app="Code", title="main.py", project=None)
        intervals = build_intervals("human", human_minutes(s, CFG), CFG)
        self.assertEqual([(i["project"], i["start"], i["end"]) for i in intervals], [(OTHER, at(0), at(5))])
        self.assertEqual(set(intervals[0]["details"]), {"Code: main.py"})

    def test_project_app_needs_orca_project(self):
        self.assertEqual(human_spans(active(0, 9, bundle=CHROME, project=None)), [])

    def test_unlisted_app_is_not_counted(self):
        self.assertEqual(human_spans(active(0, 9, bundle="com.apple.Terminal")), [])

    def test_orca_minutes_have_no_detail_but_other_windows_do(self):
        s = active(0, 2) + active(3, 5, bundle=CHROME, app="Google Chrome", title="paper")
        details = build_intervals("human", human_minutes(s, CFG), CFG)[0]["details"]
        self.assertEqual(Counter(details), Counter({None: 3, "Google Chrome: paper": 3}))


class MergeTest(unittest.TestCase):
    def test_gap_under_5_minutes_merges(self):
        self.assertEqual(human_spans(active(0, 4) + active(8, 12)), [("dotfiles2", at(0), at(13))])

    def test_gap_of_5_minutes_splits(self):
        self.assertEqual(human_spans(active(0, 4) + active(10, 14)),
                         [("dotfiles2", at(0), at(5)), ("dotfiles2", at(10), at(15))])

    def test_intervals_under_3_minutes_are_dropped(self):
        self.assertEqual(human_spans(active(0, 1)), [])


class AgentTest(unittest.TestCase):
    def test_parallel_projects_are_separate_intervals(self):
        agents = [{"project": "dotfiles2", "type": "claude"}, {"project": "proj-b", "type": "codex"}]
        s = active(0, 4, agents=agents, idle=600)
        intervals = build_intervals("agent", agent_minutes(s), CFG)
        self.assertEqual([(i["project"], i["start"], i["end"]) for i in intervals],
                         [("dotfiles2", at(0), at(5)), ("proj-b", at(0), at(5))])

    def test_same_project_agents_share_one_interval(self):
        agents = [{"project": "dotfiles2", "type": "claude"}] * 2
        intervals = build_intervals("agent", agent_minutes(active(0, 4, agents=agents)), CFG)
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0]["details"][0], Counter({"claude": 2}))


if __name__ == "__main__":
    unittest.main()
