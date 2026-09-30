"""Post-hoc seed-tier breakdown for the fixed core cohort.

Seed tier has no acquisition timestamp and is deliberately excluded from model
features. This module only joins it for descriptive dashboard statistics.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


from data_pipeline.paths import DATA_DIR as DATA
TIERS = ("IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND")


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def tier_by_record_id() -> dict[str, str]:
    """Match PUUID within its collection batch, then use team:player_id."""
    result: dict[str, str] = {}
    for cohort_path in sorted(DATA.glob("team*/team*_batch*/02_cohort_users.csv")):
        seed_path = cohort_path.with_name("01_seed_users.csv")
        if not seed_path.exists():
            continue
        seed = {row["puuid"]: row["seed_tier"].upper() for row in _rows(seed_path)}
        team = cohort_path.parent.parent.name.removeprefix("team")
        for row in _rows(cohort_path):
            tier = seed.get(row["puuid"], "")
            if tier not in TIERS:
                continue
            key = f"{team}:{row['player_id']}"
            if key in result and result[key] != tier:
                raise ValueError(f"Conflicting seed tier for {key}")
            result[key] = tier
    return result


def _mean(rows: list[dict[str, str]], column: str) -> tuple[float | None, int]:
    values = []
    for row in rows:
        raw = row.get(column, "")
        if raw not in (None, ""):
            values.append(float(raw))
    return (sum(values) / len(values) if values else None, len(values))


def build_tier_analysis(core: dict[str, dict[str, str]]) -> dict:
    tier_lookup = tier_by_record_id()
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record_id, row in core.items():
        groups[tier_lookup.get(record_id, "UNMATCHED")].append(row)
    matched = sum(len(groups[tier]) for tier in TIERS)
    if len(core) != 2381 or matched != 792:
        raise ValueError(f"Unexpected core/tier join coverage: {len(core)} / {matched}")
    summary = []
    for tier in TIERS:
        rows = groups[tier]
        if not rows:
            continue
        churners = sum(int(row["churn"]) for row in rows)
        win_rate, win_rate_n = _mean(rows, "winrate_20")
        kda, kda_n = _mean(rows, "avg_kda_20")
        games, games_n = _mean(rows, "games_30d")
        summary.append({
            "tier": tier, "users": len(rows), "churners": churners,
            "observed_no_match_rate": churners / len(rows),
            "average_win_rate": win_rate, "win_rate_n": win_rate_n,
            "average_kda": kda, "kda_n": kda_n,
            "average_games_30d": games, "games_30d_n": games_n,
        })
    return {
        "core_users": len(core), "matched_users": matched,
        "unmatched_users": len(groups["UNMATCHED"]),
        "tier_source": "01_seed_users.csv ↔ 02_cohort_users.csv, same batch PUUID join",
        "tier_collection_time_known": False,
        "tiers": summary,
    }
