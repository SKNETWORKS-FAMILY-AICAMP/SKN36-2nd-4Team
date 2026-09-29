import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / "models/core_boosting_comparison_2026-08-01"
BACKEND_DATA = ROOT / "merged-app/backend/app/data"


class CoreBoostingAndTierArtifactsTest(unittest.TestCase):
    def test_boosting_uses_same_cohort_and_reproduces_selected_catboost(self):
        with (COMPARISON / "comparison.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["model"] for row in rows}, {"CatBoost", "XGBoost", "LightGBM"})
        self.assertTrue(all(int(row["users"]) == 2381 and int(row["churners"]) == 363 for row in rows))
        selected = json.loads((ROOT / "models/core_reselected_2026-08-01/metrics.json").read_text(encoding="utf-8"))
        catboost_ap = float(next(row["pr_auc_ap"] for row in rows if row["model"] == "CatBoost"))
        self.assertAlmostEqual(catboost_ap, selected["selected_candidate_oof_exploratory"]["all_core"]["pr_auc_ap"])

    def test_tier_coverage_and_observed_rates(self):
        dashboard = json.loads((BACKEND_DATA / "core_dashboard.json").read_text(encoding="utf-8"))
        tier = dashboard["tier_analysis"]
        self.assertEqual((tier["core_users"], tier["matched_users"], tier["unmatched_users"]), (2381, 792, 1589))
        self.assertEqual(sum(row["users"] for row in tier["tiers"]), 792)
        self.assertEqual(sum(row["churners"] for row in tier["tiers"]), 141)
        for row in tier["tiers"]:
            self.assertAlmostEqual(row["observed_no_match_rate"], row["churners"] / row["users"])
        self.assertFalse(tier["tier_collection_time_known"])


if __name__ == "__main__":
    unittest.main()
