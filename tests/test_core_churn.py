import json
import unittest

import pandas as pd

from modeling.train_core_churn import OUTPUT, end_streak, ranking_metrics, sequence_summary


class CoreChurnTests(unittest.TestCase):
    def test_sequence_features_keep_match_order_and_solo_only(self):
        events = pd.DataFrame({
            "event_time": pd.date_range("2026-07-01", periods=10, freq="D", tz="UTC"),
            "sequence_index": range(10),
            "mode_group": ["RANKED_SOLO"] * 8 + ["ARAM"] * 2,
            "win": [1] * 5 + [0] * 5,
            "kda": [4.0] * 5 + [1.0] * 5,
        }).iloc[::-1]
        summary = sequence_summary(events)
        self.assertEqual(summary["seq_recent5_winrate"], 0.0)
        self.assertEqual(summary["seq_previous5_winrate"], 1.0)
        self.assertEqual(summary["seq_last_loss_streak"], 5)
        self.assertEqual(summary["solo_last_loss_streak"], 3)
        self.assertEqual(summary["solo_matches_in_sequence"], 8)
        self.assertEqual(summary["seq_recent5_kda"], 1.0)

    def test_budget_counts(self):
        result = ranking_metrics([1, 0, 1, 0, 0], [0.9, 0.8, 0.7, 0.2, 0.1], 0.4)
        self.assertEqual(result["selected"], 2)
        self.assertEqual(result["found_churn"], 1)
        self.assertEqual(result["false_alarms"], 1)

    def test_manifest_excludes_labels_and_identifiers(self):
        manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
        for columns in manifest["features"].values():
            self.assertTrue(set(columns).isdisjoint({
                "churn", "team_id", "player_id", "cutoff_date", "source_batch_id",
                "play_style", "activity_trend", "actual_history_matches",
            }))


if __name__ == "__main__":
    unittest.main()
