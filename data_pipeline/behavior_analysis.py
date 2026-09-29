r"""Read-only, model-free behavior profile for a future API or React frontend.

Example: python -m data_pipeline.behavior_analysis 1 PLAYER_ID
The profile is as of the saved cutoff, not a live account status.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "lol_churn_all_data/database/lol_churn.db"
DEFAULT_CUTOFF = "2026-08-01"


@dataclass(frozen=True)
class BehaviorRules:
    """Transparent display thresholds, not learned or medically/business validated."""

    long_inactive_days: float = 7.0
    min_previous_30d_games: int = 4
    activity_ratio_at_most: float = 0.5
    gap_ratio_at_least: float = 2.0
    gap_increase_days_at_least: float = 0.5
    winrate_drop_at_least: float = 0.4
    kda_drop_at_least: float = 1.5
    kda_ratio_at_most: float = 0.6
    dominant_mode_share_at_least: float = 0.6


def _number(value):
    """Convert pandas values to JSON-safe numbers, preserving missing as None."""
    if pd.isna(value):
        return None
    return float(value)


def _mean(frame: pd.DataFrame, column: str):
    if frame.empty:
        return None
    return _number(pd.to_numeric(frame[column], errors="coerce").mean())


def _dominant_mode(frame: pd.DataFrame):
    if frame.empty:
        return None, None
    counts = frame["mode_group"].fillna("UNKNOWN").astype(str).value_counts()
    return str(counts.index[0]), float(counts.iloc[0] / len(frame))


def _tag(code: str, label: str, evidence: str, rule: str):
    return {"code": code, "label": label, "evidence": evidence, "rule": rule}


def analyze_behavior(
    events: pd.DataFrame,
    features: dict,
    cutoff_date: str,
    rules: BehaviorRules = BehaviorRules(),
) -> dict:
    """Compute descriptive changes using only matches before cutoff.

    The comparison is last 5 observed matches versus the preceding 5, not a
    complete long-term history. `games_*` values come from ml_features and
    are not limited by the retained 30-event sequence.
    """
    cutoff = pd.Timestamp(cutoff_date, tz="UTC")
    frame = events.copy()
    frame["event_time"] = pd.to_datetime(frame["event_time"], utc=True, errors="coerce")
    if frame.event_time.isna().any():
        raise ValueError("Invalid event_time in sequence_events")
    if frame.event_time.ge(cutoff).any():
        raise ValueError("A match on or after the cutoff cannot be used")
    frame = frame.sort_values(["event_time", "sequence_index"], kind="stable").tail(30)
    if frame.empty:
        raise ValueError("No pre-cutoff matches for this user")
    recent = frame.tail(5)
    previous = frame.iloc[-10:-5] if len(frame) >= 10 else frame.iloc[0:0]

    recent_gap = _mean(recent, "time_gap_days")
    previous_gap = _mean(previous, "time_gap_days")
    gap_ratio = (recent_gap / previous_gap if recent_gap is not None
                 and previous_gap is not None and previous_gap > 0 else None)
    recent_winrate = _mean(recent, "win")
    previous_winrate = _mean(previous, "win")
    recent_kda = _mean(recent, "kda")
    previous_kda = _mean(previous, "kda")
    recent_mode, recent_mode_share = _dominant_mode(recent)
    previous_mode, previous_mode_share = _dominant_mode(previous)

    last_game = frame.event_time.iloc[-1]
    since_last = float((cutoff - last_game).total_seconds() / 86400)
    games_30d = _number(features.get("games_30d"))
    games_prev30d = _number(features.get("games_prev30d"))
    activity_change_pct = ((games_30d - games_prev30d) / games_prev30d
                           if games_30d is not None and games_prev30d is not None
                           and games_prev30d > 0 else None)
    tags = []
    if since_last >= rules.long_inactive_days:
        tags.append(_tag(
            "long_inactive", "마지막 경기 이후 공백",
            f"기준일까지 {since_last:.1f}일",
            f"마지막 경기 이후 {rules.long_inactive_days:g}일 이상"))
    if (games_30d is not None and games_prev30d is not None
            and games_prev30d >= rules.min_previous_30d_games
            and games_30d <= games_prev30d * rules.activity_ratio_at_most):
        tags.append(_tag(
            "activity_decline", "30일 경기 수 감소",
            f"이전 30일 {games_prev30d:.0f}판 → 최근 30일 {games_30d:.0f}판",
            f"이전 {rules.min_previous_30d_games}판 이상, 최근 경기 수가 "
            f"이전의 {rules.activity_ratio_at_most:.0%} 이하"))
    if (len(previous) == 5 and len(recent) == 5 and gap_ratio is not None
            and gap_ratio >= rules.gap_ratio_at_least
            and recent_gap - previous_gap >= rules.gap_increase_days_at_least):
        tags.append(_tag(
            "gap_widening", "경기 간격 증가",
            f"이전 5경기 평균 {previous_gap:.2f}일 → 최근 5경기 평균 {recent_gap:.2f}일",
            f"간격 {rules.gap_ratio_at_least:g}배 이상 및 "
            f"{rules.gap_increase_days_at_least:g}일 이상 증가"))
    win_drop = (recent_winrate is not None and previous_winrate is not None
                and previous_winrate - recent_winrate >= rules.winrate_drop_at_least)
    kda_drop = (recent_kda is not None and previous_kda is not None
                and previous_kda > 0 and previous_kda - recent_kda >= rules.kda_drop_at_least
                and recent_kda <= previous_kda * rules.kda_ratio_at_most)
    if len(previous) == 5 and (win_drop or kda_drop):
        tags.append(_tag(
            "performance_drop", "최근 성적 하락",
            f"승률 {previous_winrate:.0%} → {recent_winrate:.0%}; "
            f"평균 KDA {previous_kda:.2f} → {recent_kda:.2f}",
            "최근 5경기의 승률 또는 KDA가 이전 5경기보다 지정 기준만큼 낮음"))
    if (len(previous) == 5 and recent_mode != previous_mode
            and recent_mode_share is not None and previous_mode_share is not None
            and recent_mode_share >= rules.dominant_mode_share_at_least
            and previous_mode_share >= rules.dominant_mode_share_at_least):
        tags.append(_tag(
            "mode_shift", "주요 게임 모드 변화",
            f"이전: {previous_mode} ({previous_mode_share:.0%}) → "
            f"최근: {recent_mode} ({recent_mode_share:.0%})",
            f"각 5경기의 최다 모드 비중 {rules.dominant_mode_share_at_least:.0%} 이상"))
    if not tags:
        tags.append(_tag(
            "insufficient_history" if len(frame) < 10 else "no_large_change",
            "비교 경기 부족" if len(frame) < 10 else "설정 기준에서 큰 변화 없음",
            f"보유 시퀀스 {len(frame)}경기",
            "최근·이전 각 5경기 비교에는 최소 10경기 필요" if len(frame) < 10
            else "위 표시 규칙 어느 것도 충족하지 않음"))

    timeline = []
    for row in frame.itertuples(index=False):
        timeline.append({
            "event_time": row.event_time.isoformat(),
            "sequence_index": int(row.sequence_index),
            "mode_group": str(row.mode_group) if pd.notna(row.mode_group) else None,
            "team_position": str(row.team_position) if pd.notna(row.team_position) else None,
            "champion_id": int(row.champion_id) if pd.notna(row.champion_id) else None,
            "win": int(row.win) if pd.notna(row.win) else None,
            "kda": _number(row.kda),
            "time_gap_days": _number(row.time_gap_days),
        })
    actual_history = _number(features.get("actual_history_matches"))
    return {
        "as_of_cutoff": cutoff_date,
        "metrics": {
            "games_30d": games_30d,
            "games_prev30d": games_prev30d,
            "activity_change_pct": activity_change_pct,
            "days_since_last_game": since_last,
            "recent_5_gap_mean_days": recent_gap,
            "previous_5_gap_mean_days": previous_gap,
            "gap_ratio": gap_ratio,
            "recent_5_winrate": recent_winrate,
            "previous_5_winrate": previous_winrate,
            "recent_5_kda_mean": recent_kda,
            "previous_5_kda_mean": previous_kda,
            "recent_5_dominant_mode": recent_mode,
            "previous_5_dominant_mode": previous_mode,
        },
        "tags": tags,
        "timeline": timeline,
        "data_quality": {
            "matches_in_sequence": len(frame),
            "actual_history_matches": actual_history,
            "sequence_truncated_to_30": (actual_history > len(frame)
                                         if actual_history is not None else None),
            "previous_5_available": len(previous) == 5,
        },
        "interpretation": "cutoff 이전 관측 변화이며 이탈 원인·예측 확률이 아닙니다.",
    }


def get_user_behavior(
    team_id: int,
    player_id: str,
    cutoff_date: str = DEFAULT_CUTOFF,
    db_path: Path = DEFAULT_DB,
    rules: BehaviorRules = BehaviorRules(),
) -> dict:
    """UI-independent entry point. Never reads targets or changes the DB."""
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    uri = f"file:{path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        feature_row = conn.execute(
            "SELECT games_30d, games_prev30d, actual_history_matches "
            "FROM ml_features WHERE team_id=? AND player_id=? AND cutoff_date=?",
            (int(team_id), str(player_id), cutoff_date),
        ).fetchone()
        if feature_row is None:
            raise ValueError("User/cutoff not found in ml_features")
        events = pd.read_sql_query(
            "SELECT sequence_index,event_time,time_gap_days,mode_group,"
            "team_position,champion_id,win,kda FROM sequence_events "
            "WHERE team_id=? AND player_id=? AND cutoff_date=? "
            "ORDER BY sequence_index",
            conn, params=(int(team_id), str(player_id), cutoff_date),
        )
    features = dict(zip(("games_30d", "games_prev30d", "actual_history_matches"),
                        feature_row))
    profile = analyze_behavior(events, features, cutoff_date, rules)
    profile["team_id"] = int(team_id)
    profile["player_id"] = str(player_id)
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("team_id", type=int)
    parser.add_argument("player_id")
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    args = parser.parse_args()
    profile = get_user_behavior(args.team_id, args.player_id, args.cutoff)
    # Keep CLI output compact; the function returns the complete timeline.
    profile["timeline"] = profile["timeline"][-5:]
    print(json.dumps(profile, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
