import sqlite3
import unittest

import pandas as pd

from data_pipeline.build_core_segment_db import DEST, KEY, segment_users


class CoreSegmentsTests(unittest.TestCase):
    def test_two_axes_are_separate_and_pre_cutoff(self):
        rows = pd.DataFrame({
            "team_id": [1, 1, 1],
            "player_id": ["a", "b", "c"],
            "cutoff_date": ["2026-08-01"] * 3,
            "games_prev30d": [10, 4, 0],
            "games_30d": [3, 10, 1],
            "ranked_solo_ratio_30d": [1.0, 0.0, 0.0],
            "normal_ratio_30d": [0.0, 0.0, 0.0],
            "aram_ratio_30d": [0.0, 0.8, 1.0],
            "arena_ratio_30d": [0.0, 0.0, 0.0],
            "rotating_ratio_30d": [0.0, 0.0, 0.0],
            "churn": [1, 0, 1],
        })
        segmented = segment_users(rows)
        self.assertEqual(segmented.customer_cohort.tolist(), [
            "established_active", "established_active", "limited_prior_activity"])
        self.assertEqual(segmented.play_style.tolist(), [
            "insufficient_recent_games", "casual_focused", "insufficient_recent_games"])
        self.assertEqual(segmented.activity_trend.tolist(), [
            "activity_declining", "activity_growing", "not_assessed"])
        # Changing the future label cannot change the cutoff-time groups.
        flipped = rows.copy()
        flipped["churn"] = 1 - flipped["churn"]
        self.assertTrue(segmented[["customer_cohort", "play_style", "activity_trend"]].equals(
            segment_users(flipped)[["customer_cohort", "play_style", "activity_trend"]]))

    def test_derived_database_separates_features_and_targets(self):
        with sqlite3.connect(f"file:{DEST.resolve().as_posix()}?mode=ro", uri=True) as conn:
            tables = {name for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {"cohort_membership", "core_ml_features", "core_targets"})
            self.assertEqual(conn.execute("SELECT count(*) FROM core_ml_features").fetchone()[0], 2381)
            self.assertEqual(conn.execute("SELECT count(*) FROM core_targets").fetchone()[0], 2381)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(core_ml_features)")}
            self.assertTrue(set(KEY).issubset(columns))
            self.assertNotIn("churn", columns)


if __name__ == "__main__":
    unittest.main()
