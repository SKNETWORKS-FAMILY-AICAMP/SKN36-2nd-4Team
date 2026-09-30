"""프로젝트 루트의 모델 산출물을 FastAPI가 읽을 수 있는 JSON으로 변환한다."""
from __future__ import annotations

import csv
import json
from pathlib import Path

# backend/ 바로 위가 프로젝트 루트다. merged-app/backend 시절의 parents[2]는 한 단계 위 폴더를 가리킨다.
ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "lol_churn_all_data/derived/established_active_segmented_ml_2026-08-01.csv"
OOF = ROOT / "models/core_churn_2026-08-01/oof_predictions.jsonl"
OUT = Path(__file__).resolve().parent / "app/data/core_dashboard.json"


def number(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def reason(row: dict[str, str]) -> str:
    if number(row, "activity_change_30d") < -0.25:
        return "활동량 급감"
    if number(row, "last_gap") >= 7 or number(row, "days_since_last_game") >= 10:
        return "경기 간격 증가"
    if number(row, "winrate_change_10") < -0.15:
        return "최근 승률 하락"
    if number(row, "losing_streak") >= 3:
        return "연패 증가"
    return "최근 활동 변화"


def main() -> None:
    with FEATURES.open(encoding="utf-8-sig", newline="") as handle:
        features = {f"{r['team_id']}:{r['player_id']}": r for r in csv.DictReader(handle)}
    scores: dict[str, dict] = {}
    with OOF.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            scores[f"{item['team_id']}:{item['player_id']}"] = item

    items = []
    for record_id, row in features.items():
        player_id = row["player_id"]
        score_row = scores.get(record_id, {})
        score = float(score_row.get("baseline_aggregates", 0.0))
        if score >= 0.7:
            level = "HIGH"
        elif score >= 0.5:
            level = "MEDIUM"
        else:
            level = "LOW"
        items.append({
            "record_id": record_id,
            "player_id": player_id,
            "tier": "미제공",
            "risk_score": score,
            "risk_level": level,
            "last_game_days": round(number(row, "days_since_last_game")),
            "recent_matches": round(number(row, "games_30d")),
            "win_rate": number(row, "winrate_20"),
            "main_reason": reason(row),
            "play_style": row.get("play_style", "mixed_or_other"),
            "activity_trend": row.get("activity_trend", "unknown"),
            "team_id": row.get("team_id", ""),
            "churn": int(number(row, "churn")),
        })
    items.sort(key=lambda item: item["risk_score"], reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    def grouped_rates(rows: list[dict[str, str]], feature: str, bands: list[tuple[str, float, float]]) -> list[dict[str, object]]:
        result = []
        for label, low, high in bands:
            group = [row for row in rows if low <= number(row, feature) <= high]
            result.append({"label": label, "rate": sum(int(number(row, "churn")) for row in group) / len(group) if group else 0.0})
        return result

    mode_summary = {"ALL": {"users": len(features), "churners": sum(int(number(row, "churn")) for row in features.values())}}
    core_players = set(features)
    record_counts = {"ALL": 0}
    mode_columns = {"RANKED_SOLO_5x5": "ranked_solo_ratio_30d", "RANKED_FLEX_SR": "ranked_flex_ratio_30d", "NORMAL_SR": "normal_ratio_30d", "ARAM": "aram_ratio_30d", "ARENA": "arena_ratio_30d"}
    mode_summary["ALL"]["inactivity_churn_rates"] = grouped_rates(list(features.values()), "days_since_last_game", [("0~3일", 0, 3), ("4~7일", 4, 7), ("8~14일", 8, 14), ("15~30일", 15, 30)])
    mode_summary["ALL"]["activity_churn_rates"] = grouped_rates(list(features.values()), "games_7d", [("0경기", 0, 0), ("1~4경기", 1, 4), ("5~14경기", 5, 14), ("15경기 이상", 15, 1000000)])
    for mode, column in mode_columns.items():
        rows = [row for row in features.values() if number(row, column) > 0]
        churners = sum(int(number(row, "churn")) for row in rows)
        mode_summary[mode] = {"users": len(rows), "churners": churners, "churn_rate": churners / len(rows) if rows else 0.0, "inactivity_churn_rates": grouped_rates(rows, "days_since_last_game", [("0~3일", 0, 3), ("4~7일", 4, 7), ("8~14일", 8, 14), ("15~30일", 15, 30)]), "activity_churn_rates": grouped_rates(rows, "games_7d", [("0경기", 0, 0), ("1~4경기", 1, 4), ("5~14경기", 5, 14), ("15경기 이상", 15, 1000000)])}
    sequence_path = ROOT / "lol_churn_all_data/final/final_transformer_sequence.csv"
    monthly_position = []
    user_histories: dict[str, list[dict[str, object]]] = {record_id: [] for record_id in core_players}
    if sequence_path.exists():
        with sequence_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                record_key = f"{row.get('team_id', '')}:{row.get('player_id', '')}"
                if record_key in core_players:
                    record_counts["ALL"] += 1
                    mode_key = {"RANKED_SOLO": "RANKED_SOLO_5x5", "RANKED_FLEX": "RANKED_FLEX_SR", "NORMAL": "NORMAL_SR", "ARAM": "ARAM", "ARENA": "ARENA"}.get(row.get("modeGroup", ""))
                    if mode_key:
                        record_counts[mode_key] = record_counts.get(mode_key, 0) + 1
                    if 0 <= number(row, "daysBeforeCutoff", 9999) <= 30:
                        user_histories[record_key].append({
                            "date": row.get("eventTime", "")[:10],
                            "event_time": row.get("eventTime", ""),
                            "mode": row.get("modeGroup", "OTHER"),
                            "kda": number(row, "kda"),
                            "win": int(number(row, "win")),
                            "damage": round(number(row, "damagePerMin") * number(row, "gameDurationMin")),
                            "cs": round(number(row, "csPerMin") * number(row, "gameDurationMin")),
                            "vision": round(number(row, "visionPerMin") * number(row, "gameDurationMin")),
                            "duration_minutes": round(number(row, "gameDurationMin")),
                            "gap_days": number(row, "timeGapDays"),
                        })
                if row.get("modeGroup") != "RANKED_SOLO" or not row.get("teamPosition"):
                    continue
                month = row.get("eventTime", "")[:7]
                monthly_position.append({
                    "month": month,
                    "position": row["teamPosition"],
                    "kda": number(row, "kda"),
                    "duration": number(row, "gameDurationMin"),
                    "win": number(row, "win"),
                })
        grouped = {}
        for row in monthly_position:
            key = (row["month"], row["position"])
            group = grouped.setdefault(key, {"month": row["month"], "position": row["position"], "matches": 0, "kda_sum": 0.0, "duration_sum": 0.0, "wins": 0})
            group["matches"] += 1; group["kda_sum"] += row["kda"]; group["duration_sum"] += row["duration"]; group["wins"] += int(row["win"])
        monthly_position = [{"month": g["month"], "position": g["position"], "matches": g["matches"], "avg_kda": g["kda_sum"] / g["matches"], "avg_duration_min": g["duration_sum"] / g["matches"], "win_rate": g["wins"] / g["matches"]} for g in grouped.values()]
    cohort_path = ROOT / "lol_churn_all_data/derived/customer_cohorts_2026-08-01.csv"
    mode_summary["ALL"]["match_records"] = record_counts.get("ALL", 0)
    for mode in mode_columns:
        mode_summary[mode]["match_records"] = record_counts.get(mode, 0)
    total_collected_users = len(features)
    if cohort_path.exists():
        with cohort_path.open(encoding="utf-8-sig", newline="") as handle:
            total_collected_users = sum(1 for _ in csv.DictReader(handle))
    details = {}
    features_by_id = features
    for record_id, events in user_histories.items():
        events.sort(key=lambda event: str(event["event_time"]))
        events = events[-30:]
        activity: dict[str, int] = {}
        modes: dict[str, int] = {}
        for event in events:
            day = str(event["date"])
            if day:
                activity[day] = activity.get(day, 0) + 1
            mode = str(event["mode"])
            modes[mode] = modes.get(mode, 0) + 1
        details[record_id] = {
            "events": events,
            "activity": [{"date": day, "matches": count} for day, count in sorted(activity.items())],
            "modes": [{"mode": mode, "count": count} for mode, count in sorted(modes.items())],
            "average_kda": number(features_by_id[record_id], "avg_kda_20"),
            "average_interval_days": number(features_by_id[record_id], "avg_gap_30d"),
        }
    payload = {"cutoff_date": "2026-08-01", "total_collected_users": total_collected_users, "items": items, "details": details, "mode_summary": mode_summary, "monthly_position": monthly_position}
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(items)} users to {OUT}")


if __name__ == "__main__":
    main()
