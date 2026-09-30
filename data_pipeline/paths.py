"""Shared locations for the LoL churn project.

Scripts should import these constants instead of rebuilding the same
`parents[1] / "lol_churn_all_data"` paths.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "lol_churn_all_data"
DB = DATA_DIR / "database" / "lol_churn.db"
DERIVED = DATA_DIR / "derived"
MODELS_DIR = PROJECT_ROOT / "models"
CUTOFF = "2026-08-01"
