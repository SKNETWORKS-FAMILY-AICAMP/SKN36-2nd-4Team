import unittest

import pandas as pd

from data_pipeline.behavior_analysis import analyze_behavior


class BehaviorAnalysisTests(unittest.TestCase):
    def make_events(self):
        times = pd.date_range("2026-07-10", periods=10, freq="D", tz="UTC")
        return pd.DataFrame({
            "sequence_index": range(10),
            "event_time": times,
            "time_gap_days": [0.25] * 5 + [2.0] * 5,
            "mode_group": ["RANKED_SOLO"] * 5 + ["ARAM"] * 5,
            "team_position": ["MIDDLE"] * 10,
            "champion_id": [1] * 10,
            "win": [1] * 5 + [0] * 5,
            "kda": [4.0] * 5 + [1.0] * 5,
        })

    def test_all_change_tags_and_chronological_timeline(self):
        events = self.make_events().iloc[::-1]
        profile = analyze_behavior(events, {
            "games_30d": 5, "games_prev30d": 20,
            "actual_history_matches": 40,
        }, "2026-08-01")
        codes = {tag["code"] for tag in profile["tags"]}
        self.assertEqual(codes, {
            "long_inactive", "activity_decline", "gap_widening",
            "performance_drop", "mode_shift",
        })
        self.assertEqual([row["sequence_index"] for row in profile["timeline"]], list(range(10)))
        self.assertTrue(profile["data_quality"]["sequence_truncated_to_30"])

    def test_short_history_does_not_invent_comparisons(self):
        events = self.make_events().tail(3)
        profile = analyze_behavior(events, {
            "games_30d": 3, "games_prev30d": 0,
            "actual_history_matches": 3,
        }, "2026-07-20")
        self.assertEqual([tag["code"] for tag in profile["tags"]], ["insufficient_history"])
        self.assertIsNone(profile["metrics"]["activity_change_pct"])

    def test_event_at_cutoff_rejected(self):
        events = self.make_events()
        events.loc[9, "event_time"] = "2026-08-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "cutoff"):
            analyze_behavior(events, {}, "2026-08-01")


if __name__ == "__main__":
    unittest.main()
