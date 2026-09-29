"""Consistency checks for the published 2,381-user experiment artifacts."""

import csv
import json
import math
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models/core_reselected_2026-08-01"
DASHBOARD = ROOT / "merged-app/backend/app/data"


class CoreReselectionArtifactsTest(unittest.TestCase):
    def test_candidate_grid_and_metrics(self) -> None:
        with (MODEL / "candidate_cv.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 15)
        self.assertEqual(len({(row["feature_set"], row["treatment"]) for row in rows}), 15)
        metrics = json.loads((MODEL / "metrics.json").read_text(encoding="utf-8"))
        winner = metrics["selected_candidate"]
        self.assertEqual((rows[0]["feature_set"], rows[0]["treatment"]),
                         (winner["feature_set"], winner["treatment"]))
        self.assertGreater(float(rows[0]["ap"]),
                           metrics["nested_selection_oof"]["all_core"]["pr_auc_ap"])

    def test_scores_and_dashboard_match_exactly(self) -> None:
        with (MODEL / "oof_predictions.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        payload = json.loads((DASHBOARD / "core_dashboard.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows), len(payload["items"]))
        self.assertEqual(len(rows), 2381)
        source = {f"{row['team_id']}:{row['player_id']}": float(row["selected_candidate_oof_score"])
                  for row in rows}
        self.assertEqual(len(source), 2381)
        for item in payload["items"]:
            self.assertTrue(math.isclose(item["risk_score"], source[item["record_id"]]))
        self.assertEqual(Counter(item["risk_level"] for item in payload["items"]),
                         {"HIGH": 239, "MEDIUM": 238, "LOW": 1904})

    def test_excluded_features_and_selected_shap(self) -> None:
        manifest = json.loads((MODEL / "manifest.json").read_text(encoding="utf-8"))
        selected = manifest["selected_features"]
        self.assertEqual(len(selected), 33)
        self.assertFalse({"churn", "player_id", "team_id", "seed_tier"} & set(selected))
        with (MODEL / "selected_model_shap_importance.csv").open(encoding="utf-8", newline="") as handle:
            shap = list(csv.DictReader(handle))
        self.assertEqual({row["feature"] for row in shap}, set(selected))
        self.assertEqual(shap[0]["feature"], "days_since_last_game")


if __name__ == "__main__":
    unittest.main()
