#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Riot API 기반 LoL 고객 이탈(Churn) 데이터 수집 - VS Code / 로컬 PC 버전

목적
----
1) Colab에서 10번까지 완료한 경우:
   - Google Drive의 lol_churn_project 폴더를 이 파일 옆으로 복사
   - 이 스크립트를 실행하면 03_user_match_ids.csv / 04_targets.csv를 읽고
     11번(Match 상세정보 수집)부터 자동으로 이어서 실행합니다.

2) 기존 10번 결과가 없는 경우:
   - 이 파일 옆의 puuids.csv를 사용해 cohort를 만들고
   - 10번부터 17번까지 실행합니다.

중요
----
- puuids.csv는 열 이름이 반드시 "puuid"여야 합니다.
- 기본 신규 cohort 크기는 500명입니다. 더 늘리려면 실행 옵션:
      python riot_churn_vscode.py --cohort-size 3000
- 200,000명을 한 번에 조회하지 마세요. Development/Personal Key 속도 제한 때문에
  매우 오래 걸립니다.
- 기존 체크포인트 파일을 보존하면 중간에 PC/프로그램이 꺼져도 이어받을 수 있습니다.

실행 예
-------
python riot_churn_vscode.py
python riot_churn_vscode.py --cohort-size 3000
python riot_churn_vscode.py --mode resume
python riot_churn_vscode.py --mode from-puuid --cohort-size 1000
"""

from pathlib import Path
from urllib.parse import urlparse
from datetime import timedelta
import argparse
import getpass
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm


# ============================================================
# 0. 사용자 설정
# ============================================================

CUTOFF_DATE = "2026-08-01"
OBS_DAYS = 90
LABEL_DAYS = 30

MAX_HISTORY_MATCHES = 30
MIN_HISTORY_MATCHES = 3

# Riot Development/Personal Key의 장기 rate limit을 보수적으로 지키기 위한 간격.
REQUEST_INTERVAL_SEC = 1.35

DEFAULT_COHORT_SIZE = 500
RANDOM_STATE = 42

PLATFORM = "kr"
REGION = "asia"

EXPORT_EXCEL = True
EXPORT_PARQUET = True

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = SCRIPT_DIR / "lol_churn_project"
DEFAULT_PUUID_FILE = SCRIPT_DIR / "puuids.csv"

PLATFORM_URL = f"https://{PLATFORM}.api.riotgames.com"
REGION_URL = f"https://{REGION}.api.riotgames.com"

QUEUE_URL = "https://static.developer.riotgames.com/docs/lol/queues.json"


# ============================================================
# 1. CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Riot LoL churn pipeline - VS Code local version"
    )

    parser.add_argument(
        "--mode",
        choices=["auto", "resume", "from-puuid"],
        default="auto",
        help=(
            "auto: 기존 10번 결과가 있으면 11번부터, 없으면 puuids.csv로 10번부터 / "
            "resume: 기존 10번 결과 사용 / "
            "from-puuid: puuids.csv로 새 cohort 생성"
        ),
    )

    parser.add_argument(
        "--cohort-size",
        type=int,
        default=DEFAULT_COHORT_SIZE,
        help="puuids.csv에서 새 cohort를 만들 때 사용할 유저 수 (기본 500)",
    )

    parser.add_argument(
        "--base-dir",
        type=str,
        default=str(DEFAULT_BASE_DIR),
        help="결과/체크포인트 폴더",
    )

    parser.add_argument(
        "--puuid-file",
        type=str,
        default=str(DEFAULT_PUUID_FILE),
        help="PUUID 원본 CSV 경로",
    )

    parser.add_argument(
        "--no-excel",
        action="store_true",
        help="Excel 통합 파일 생성을 생략",
    )

    parser.add_argument(
        "--no-parquet",
        action="store_true",
        help="Parquet 저장을 생략",
    )

    return parser.parse_args()


# ============================================================
# 2. 공통 유틸
# ============================================================

def player_id_from_puuid(puuid: str) -> str:
    return hashlib.sha256(str(puuid).encode("utf-8")).hexdigest()[:16]


def read_done_set(path: Path):
    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def append_done(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(str(value) + "\n")
        f.flush()


def safe_read_csv(path: Path, required=False):
    if not path.exists():
        if required:
            raise FileNotFoundError(f"필수 파일이 없습니다: {path}")
        return None

    return pd.read_csv(path)


def ensure_player_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "puuid" not in df.columns:
        raise ValueError("데이터에 'puuid' 열이 없습니다.")

    df["puuid"] = df["puuid"].astype(str)

    if "player_id" not in df.columns:
        df["player_id"] = df["puuid"].map(player_id_from_puuid)
    else:
        missing = df["player_id"].isna()
        if missing.any():
            df.loc[missing, "player_id"] = (
                df.loc[missing, "puuid"].map(player_id_from_puuid)
            )

    return df


# ============================================================
# 3. Riot API
# ============================================================

SESSION = requests.Session()
_last_request = {}


def set_api_key():
    api_key = os.environ.get("RIOT_API_KEY", "").strip()

    if not api_key:
        api_key = getpass.getpass(
            "Riot API Key 입력 (입력 내용은 화면에 보이지 않음): "
        ).strip()

    if not api_key:
        raise RuntimeError("Riot API Key가 비어 있습니다.")

    SESSION.headers.update({"X-Riot-Token": api_key})


def _throttle(url: str):
    host = urlparse(url).netloc

    now = time.time()
    last = _last_request.get(host, 0.0)
    elapsed = now - last

    if elapsed < REQUEST_INTERVAL_SEC:
        time.sleep(REQUEST_INTERVAL_SEC - elapsed)

    _last_request[host] = time.time()


def riot_get(url, params=None, max_retry=8):
    for attempt in range(max_retry):
        _throttle(url)

        try:
            response = SESSION.get(url, params=params, timeout=30)

        except requests.RequestException as exc:
            wait = min(60, 2 ** attempt)
            print(f"[네트워크 오류] {exc} -> {wait}초 후 재시도")
            time.sleep(wait)
            continue

        if response.status_code == 200:
            return response.json()

        if response.status_code == 404:
            return None

        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", 120))
            print(f"[429 Rate Limit] {retry_after:.0f}초 대기")
            time.sleep(retry_after + 1)
            continue

        if response.status_code in (500, 502, 503, 504):
            wait = min(60, 2 ** attempt)
            print(
                f"[{response.status_code} Riot 서버 오류] "
                f"{wait}초 후 재시도"
            )
            time.sleep(wait)
            continue

        if response.status_code in (401, 403):
            raise RuntimeError(
                f"Riot API 인증/권한 오류 {response.status_code}. "
                "Development Key가 만료됐는지 확인하고 새 Key로 다시 실행하세요. "
                "체크포인트가 있으면 완료된 부분은 건너뜁니다."
            )

        raise RuntimeError(
            f"요청 실패 status={response.status_code}\n"
            f"url={url}\n"
            f"body={response.text[:300]}"
        )

    raise RuntimeError(f"최대 재시도 초과: {url}")


def get_match_ids(puuid, start_time, end_time, max_matches=30):
    url = f"{REGION_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"

    all_ids = []
    start = 0

    while len(all_ids) < max_matches:
        count = min(100, max_matches - len(all_ids))

        params = {
            "startTime": int(start_time),
            "endTime": int(end_time),
            "start": start,
            "count": count,
        }

        batch = riot_get(url, params=params)

        if not batch:
            break

        all_ids.extend(batch)

        if len(batch) < count:
            break

        start += len(batch)

    return all_ids[:max_matches]


def get_match_detail(match_id):
    url = f"{REGION_URL}/lol/match/v5/matches/{match_id}"
    return riot_get(url)


# ============================================================
# 4. Queue 정보
# ============================================================

def load_queue_info():
    try:
        response = requests.get(QUEUE_URL, timeout=30)
        response.raise_for_status()

        queue_data = response.json()
        queue_df = pd.DataFrame(queue_data)

        queue_map = {
            int(row["queueId"]): row
            for row in queue_data
            if row.get("queueId") is not None
        }

        return queue_df, queue_map

    except Exception as exc:
        print(
            "[경고] Riot queues.json을 불러오지 못했습니다. "
            f"queueDescription 없이 계속합니다: {exc}"
        )
        return pd.DataFrame(), {}


def get_mode_group(queue_id):
    if queue_id == 420:
        return "RANKED_SOLO"
    if queue_id == 440:
        return "RANKED_FLEX"
    if queue_id in (400, 430, 480, 490):
        return "NORMAL"
    if queue_id in (450, 2400):
        return "ARAM"
    if queue_id in (1700, 1710):
        return "ARENA"
    if queue_id in (700, 720):
        return "CLASH"
    if queue_id in (900, 1020, 1300, 1400, 1900, 2300):
        return "ROTATING"

    return "OTHER"


# ============================================================
# 5. 기준일
# ============================================================

CUTOFF = pd.Timestamp(CUTOFF_DATE, tz="UTC")
OBS_START = CUTOFF - pd.Timedelta(days=OBS_DAYS)
LABEL_END = CUTOFF + pd.Timedelta(days=LABEL_DAYS)

OBS_START_TS = int(OBS_START.timestamp())
CUTOFF_TS = int(CUTOFF.timestamp())
LABEL_END_TS = int(LABEL_END.timestamp())


# ============================================================
# 6. Cohort 준비
# ============================================================

def build_cohort_from_puuid_file(
    puuid_file: Path,
    cohort_path: Path,
    cohort_size: int,
):
    if not puuid_file.exists():
        raise FileNotFoundError(
            f"PUUID 파일을 찾을 수 없습니다: {puuid_file}\n"
            "riot_churn_vscode.py와 같은 폴더에 puuids.csv를 놓거나 "
            "--puuid-file 경로를 지정하세요."
        )

    source = pd.read_csv(puuid_file)

    if "puuid" not in source.columns:
        raise ValueError(
            f"{puuid_file.name}에 'puuid' 열이 없습니다. "
            f"현재 열: {source.columns.tolist()}"
        )

    source = (
        source[["puuid"]]
        .dropna()
        .drop_duplicates("puuid")
        .reset_index(drop=True)
    )
    source["puuid"] = source["puuid"].astype(str)

    if cohort_size <= 0:
        raise ValueError("--cohort-size는 1 이상이어야 합니다.")

    n = min(cohort_size, len(source))

    cohort = (
        source.sample(n=n, random_state=RANDOM_STATE)
        .reset_index(drop=True)
    )

    cohort["player_id"] = cohort["puuid"].map(player_id_from_puuid)

    cohort.to_csv(
        cohort_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"[Cohort 생성] 원본 고유 PUUID={len(source):,}명 / "
        f"사용={len(cohort):,}명"
    )
    print(f"[저장] {cohort_path}")

    return cohort


def reconstruct_cohort_if_needed(
    cohort_path: Path,
    user_match_ids_path: Path,
    targets_path: Path,
):
    if cohort_path.exists():
        cohort = pd.read_csv(cohort_path)
        return ensure_player_id(cohort).drop_duplicates("puuid").reset_index(drop=True)

    # 10번까지 끝났는데 02 파일만 없는 예외 상황 방어:
    # 04_targets.csv가 있으면 cohort를 복구할 수 있음.
    if targets_path.exists():
        targets = pd.read_csv(targets_path)

        if {"puuid", "player_id"}.issubset(targets.columns):
            cohort = (
                targets[["puuid", "player_id"]]
                .dropna(subset=["puuid"])
                .drop_duplicates("puuid")
                .reset_index(drop=True)
            )
            cohort.to_csv(cohort_path, index=False, encoding="utf-8-sig")
            print(f"[복구] 04_targets.csv에서 cohort 복구: {len(cohort):,}명")
            return cohort

    if user_match_ids_path.exists():
        mids = pd.read_csv(user_match_ids_path)

        if "puuid" in mids.columns:
            keep = ["puuid"]
            if "player_id" in mids.columns:
                keep.append("player_id")

            cohort = mids[keep].drop_duplicates("puuid").reset_index(drop=True)
            cohort = ensure_player_id(cohort)
            cohort.to_csv(cohort_path, index=False, encoding="utf-8-sig")
            print(f"[복구] 03_user_match_ids.csv에서 cohort 복구: {len(cohort):,}명")
            return cohort

    return None


# ============================================================
# 7. STEP 10
#    Cohort 전체 관찰 Match ID + 미래 30일 Churn
# ============================================================

def has_future_match(puuid):
    ids = get_match_ids(
        puuid,
        CUTOFF_TS,
        LABEL_END_TS,
        max_matches=1,
    )
    return 1 if len(ids) > 0 else 0


def collect_cohort_match_ids_and_targets(
    cohort_df: pd.DataFrame,
    user_match_ids_path: Path,
    targets_path: Path,
    cohort_done_path: Path,
):
    cohort_df = ensure_player_id(cohort_df)

    done = read_done_set(cohort_done_path)

    # target 파일에 이미 정상 저장된 PUUID도 완료로 간주.
    if targets_path.exists():
        existing_targets = pd.read_csv(targets_path)
        if "puuid" in existing_targets.columns:
            done.update(
                existing_targets["puuid"].dropna().astype(str).tolist()
            )

    first_match_write = not user_match_ids_path.exists()
    first_target_write = not targets_path.exists()

    for _, row in tqdm(
        cohort_df.iterrows(),
        total=len(cohort_df),
        desc="STEP 10 | Cohort Match ID + Target",
    ):
        puuid = str(row["puuid"])
        player_id = row["player_id"]

        if puuid in done:
            continue

        history_ids = get_match_ids(
            puuid,
            OBS_START_TS,
            CUTOFF_TS,
            max_matches=MAX_HISTORY_MATCHES,
        )

        future_exists = has_future_match(puuid)

        if history_ids:
            temp = pd.DataFrame({
                "puuid": [puuid] * len(history_ids),
                "player_id": [player_id] * len(history_ids),
                "matchId": history_ids,
                "split": ["history"] * len(history_ids),
            })

            temp.to_csv(
                user_match_ids_path,
                mode="a",
                header=first_match_write,
                index=False,
                encoding="utf-8-sig",
            )
            first_match_write = False

        target_row = pd.DataFrame([{
            "puuid": puuid,
            "player_id": player_id,
            "history_match_count_requested": len(history_ids),
            "future30d_has_match": future_exists,
            "churn": 0 if future_exists == 1 else 1,
            "cutoff_date": CUTOFF_DATE,
            "obs_days": OBS_DAYS,
            "label_days": LABEL_DAYS,
        }])

        target_row.to_csv(
            targets_path,
            mode="a",
            header=first_target_write,
            index=False,
            encoding="utf-8-sig",
        )
        first_target_write = False

        # 데이터가 파일에 기록된 뒤 완료 처리.
        append_done(cohort_done_path, puuid)
        done.add(puuid)

    if not targets_path.exists():
        raise RuntimeError("04_targets.csv가 생성되지 않았습니다.")

    # 중간 종료 직전에 중복 append가 있었더라도 최종 정리.
    targets_df = pd.read_csv(targets_path)
    targets_df = (
        targets_df
        .drop_duplicates("puuid", keep="last")
        .reset_index(drop=True)
    )
    targets_df.to_csv(targets_path, index=False, encoding="utf-8-sig")

    if user_match_ids_path.exists():
        user_match_ids_df = pd.read_csv(user_match_ids_path)
        user_match_ids_df = (
            user_match_ids_df
            .drop_duplicates(["puuid", "matchId", "split"])
            .reset_index(drop=True)
        )
        user_match_ids_df.to_csv(
            user_match_ids_path,
            index=False,
            encoding="utf-8-sig",
        )
    else:
        user_match_ids_df = pd.DataFrame(
            columns=["puuid", "player_id", "matchId", "split"]
        )
        user_match_ids_df.to_csv(
            user_match_ids_path,
            index=False,
            encoding="utf-8-sig",
        )

    print(
        f"[STEP 10 완료] Match-ID rows={len(user_match_ids_df):,}, "
        f"Targets={len(targets_df):,}"
    )

    if len(targets_df):
        print(
            f"[Churn 비율] {targets_df['churn'].mean():.4f} "
            f"({targets_df['churn'].sum():,.0f}/{len(targets_df):,})"
        )

    return user_match_ids_df, targets_df


# ============================================================
# 8. STEP 11
#    고유 Match 상세정보 수집
# ============================================================

def extract_cohort_participant_rows(
    match,
    cohort_puuids,
    puuid_to_player,
    queue_map,
):
    if not match:
        return []

    metadata = match.get("metadata", {})
    info = match.get("info", {})

    match_id = metadata.get("matchId")
    queue_id = info.get("queueId")

    queue_info = queue_map.get(queue_id, {})
    queue_description = queue_info.get("description")

    duration_sec = info.get("gameDuration", 0) or 0

    # 오래된 응답 방어
    if duration_sec > 100000:
        duration_sec = duration_sec / 1000

    duration_min = max(duration_sec / 60.0, 1e-6)

    rows = []

    for participant in info.get("participants", []):
        puuid = participant.get("puuid")

        if puuid not in cohort_puuids:
            continue

        kills = participant.get("kills", 0) or 0
        deaths = participant.get("deaths", 0) or 0
        assists = participant.get("assists", 0) or 0

        total_minions = participant.get("totalMinionsKilled", 0) or 0
        neutral_minions = participant.get("neutralMinionsKilled", 0) or 0
        cs = total_minions + neutral_minions

        gold = participant.get("goldEarned", 0) or 0
        damage = participant.get("totalDamageDealtToChampions", 0) or 0
        vision = participant.get("visionScore", 0) or 0

        rows.append({
            "player_id": puuid_to_player.get(puuid),
            "puuid": puuid,
            "matchId": match_id,
            "gameCreation": info.get("gameCreation"),
            "gameEndTimestamp": info.get("gameEndTimestamp"),
            "gameDurationSec": duration_sec,
            "gameDurationMin": duration_min,
            "queueId": queue_id,
            "queueDescription": queue_description,
            "modeGroup": get_mode_group(queue_id),
            "gameMode": info.get("gameMode"),
            "mapId": info.get("mapId"),

            "win": int(bool(participant.get("win", False))),
            "championId": participant.get("championId"),
            "championName": participant.get("championName"),
            "teamPosition": participant.get("teamPosition"),
            "individualPosition": participant.get("individualPosition"),

            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "kda": (kills + assists) / max(deaths, 1),

            "goldEarned": gold,
            "goldPerMin": gold / duration_min,

            "totalMinionsKilled": total_minions,
            "neutralMinionsKilled": neutral_minions,
            "cs": cs,
            "csPerMin": cs / duration_min,

            "damageToChampions": damage,
            "damagePerMin": damage / duration_min,
            "damageTaken": participant.get("totalDamageTaken", 0) or 0,

            "visionScore": vision,
            "visionPerMin": vision / duration_min,
            "wardsPlaced": participant.get("wardsPlaced", 0) or 0,
            "wardsKilled": participant.get("wardsKilled", 0) or 0,
        })

    return rows


def collect_raw_match_details(
    user_match_ids_df: pd.DataFrame,
    cohort_df: pd.DataFrame,
    raw_matches_path: Path,
    raw_match_done_path: Path,
    queue_map,
):
    cohort_df = ensure_player_id(cohort_df)

    cohort_puuids = set(cohort_df["puuid"].astype(str))
    puuid_to_player = dict(
        zip(cohort_df["puuid"].astype(str), cohort_df["player_id"])
    )

    done = read_done_set(raw_match_done_path)

    unique_ids = (
        user_match_ids_df["matchId"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    first_write = not raw_matches_path.exists()

    print(
        f"[STEP 11] 고유 Match ID={len(unique_ids):,}, "
        f"이미 완료={len(done):,}"
    )

    for match_id in tqdm(
        unique_ids,
        desc="STEP 11 | Match 상세정보",
    ):
        if match_id in done:
            continue

        match = get_match_detail(match_id)

        rows = extract_cohort_participant_rows(
            match=match,
            cohort_puuids=cohort_puuids,
            puuid_to_player=puuid_to_player,
            queue_map=queue_map,
        )

        if rows:
            pd.DataFrame(rows).to_csv(
                raw_matches_path,
                mode="a",
                header=first_write,
                index=False,
                encoding="utf-8-sig",
            )
            first_write = False

        # raw row 저장이 끝난 뒤 완료 체크포인트 기록.
        append_done(raw_match_done_path, match_id)
        done.add(match_id)

    if not raw_matches_path.exists():
        raise RuntimeError(
            "05_raw_matches.csv가 생성되지 않았습니다. "
            "03_user_match_ids.csv와 cohort를 확인하세요."
        )

    raw_matches = pd.read_csv(raw_matches_path)

    # 런타임/프로세스 종료 직전 중복 append가 있었던 경우 정리.
    if {"player_id", "matchId"}.issubset(raw_matches.columns):
        raw_matches = (
            raw_matches
            .drop_duplicates(["player_id", "matchId"], keep="last")
            .reset_index(drop=True)
        )
        raw_matches.to_csv(
            raw_matches_path,
            index=False,
            encoding="utf-8-sig",
        )

    print(f"[STEP 11 완료] raw_matches={raw_matches.shape}")

    return raw_matches


# ============================================================
# 9. STEP 12
#    시간 전처리
# ============================================================

def preprocess_time(
    raw_matches: pd.DataFrame,
    targets_df: pd.DataFrame,
    targets_path: Path,
):
    raw_matches = raw_matches.copy()

    raw_matches["eventTime"] = pd.to_datetime(
        raw_matches["gameCreation"],
        unit="ms",
        utc=True,
        errors="coerce",
    )

    raw_matches = (
        raw_matches
        .sort_values(["player_id", "eventTime"])
        .drop_duplicates(["player_id", "matchId"])
        .reset_index(drop=True)
    )

    raw_matches["timeGapDays"] = (
        raw_matches
        .groupby("player_id")["eventTime"]
        .diff()
        .dt.total_seconds()
        .div(86400)
    )

    history = raw_matches[
        raw_matches["eventTime"] < CUTOFF
    ].copy()

    actual_counts = (
        history
        .groupby("player_id")
        .size()
        .rename("actual_history_matches")
    )

    targets_df = targets_df.copy()
    targets_df = targets_df.drop(
        columns=["actual_history_matches"],
        errors="ignore",
    )

    targets_df = targets_df.merge(
        actual_counts,
        on="player_id",
        how="left",
    )

    targets_df["actual_history_matches"] = (
        targets_df["actual_history_matches"]
        .fillna(0)
        .astype(int)
    )

    targets_df.to_csv(
        targets_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("[STEP 12 완료] 관찰 경기 수 통계")
    print(targets_df["actual_history_matches"].describe())

    return raw_matches, history, targets_df


# ============================================================
# 10. STEP 13
#     Boosting feature
# ============================================================

def current_losing_streak(df):
    if df.empty:
        return 0

    x = df.sort_values("eventTime", ascending=False)

    count = 0

    for win in x["win"].tolist():
        if int(win) == 0:
            count += 1
        else:
            break

    return count


def make_ml_features(history, targets_df):
    rows = []

    for player_id, group in tqdm(
        history.groupby("player_id"),
        desc="STEP 13 | Boosting Feature",
    ):
        g = group.sort_values("eventTime")

        last7 = g[
            g["eventTime"] >= CUTOFF - pd.Timedelta(days=7)
        ]

        last30 = g[
            g["eventTime"] >= CUTOFF - pd.Timedelta(days=30)
        ]

        prev30 = g[
            (g["eventTime"] >= CUTOFF - pd.Timedelta(days=60))
            & (g["eventTime"] < CUTOFF - pd.Timedelta(days=30))
        ]

        last90 = g[
            g["eventTime"] >= CUTOFF - pd.Timedelta(days=90)
        ]

        last20 = g.tail(20)
        last10 = g.tail(10)
        prev10 = g.iloc[-20:-10] if len(g) >= 20 else pd.DataFrame()

        last_time = g["eventTime"].max()

        days_since_last = (
            (CUTOFF - last_time).total_seconds() / 86400
        )

        gaps30 = last30["timeGapDays"].dropna()

        mode_ratio = last30["modeGroup"].value_counts(
            normalize=True
        )

        champ_counts = last20["championId"].value_counts()

        if len(last20) > 0 and len(champ_counts) > 0:
            top_champ_ratio = champ_counts.iloc[0] / len(last20)
        else:
            top_champ_ratio = np.nan

        wr_last10 = (
            last10["win"].mean()
            if len(last10)
            else np.nan
        )

        wr_prev10 = (
            prev10["win"].mean()
            if len(prev10)
            else np.nan
        )

        if len(last20) >= 2:
            switches = (
                last20["modeGroup"]
                != last20["modeGroup"].shift()
            ).sum() - 1

            mode_switch_rate = switches / (len(last20) - 1)

        else:
            mode_switch_rate = 0.0

        rows.append({
            "player_id": player_id,

            "games_7d": len(last7),
            "games_30d": len(last30),
            "games_90d": len(last90),
            "games_prev30d": len(prev30),
            "activity_change_30d": len(last30) - len(prev30),
            "active_days_30d": last30["eventTime"].dt.date.nunique(),

            "days_since_last_game": days_since_last,
            "avg_gap_30d": gaps30.mean() if len(gaps30) else np.nan,
            "max_gap_30d": gaps30.max() if len(gaps30) else np.nan,
            "last_gap": (
                g["timeGapDays"].iloc[-1]
                if len(g)
                else np.nan
            ),

            "winrate_20": last20["win"].mean(),
            "avg_kda_20": last20["kda"].mean(),
            "avg_kills_20": last20["kills"].mean(),
            "avg_deaths_20": last20["deaths"].mean(),
            "avg_assists_20": last20["assists"].mean(),
            "losing_streak": current_losing_streak(last20),

            "winrate_change_10": (
                wr_last10 - wr_prev10
                if pd.notna(wr_last10) and pd.notna(wr_prev10)
                else np.nan
            ),

            "avg_game_duration_20": last20["gameDurationMin"].mean(),
            "avg_gold_per_min_20": last20["goldPerMin"].mean(),
            "avg_cs_per_min_20": last20["csPerMin"].mean(),
            "avg_damage_per_min_20": last20["damagePerMin"].mean(),
            "avg_vision_per_min_20": last20["visionPerMin"].mean(),

            "unique_champions_20": last20["championId"].nunique(),
            "top_champion_ratio_20": top_champ_ratio,

            "unique_modes_30d": last30["modeGroup"].nunique(),
            "mode_switch_rate_20": mode_switch_rate,

            "ranked_solo_ratio_30d": mode_ratio.get("RANKED_SOLO", 0.0),
            "ranked_flex_ratio_30d": mode_ratio.get("RANKED_FLEX", 0.0),
            "normal_ratio_30d": mode_ratio.get("NORMAL", 0.0),
            "aram_ratio_30d": mode_ratio.get("ARAM", 0.0),
            "arena_ratio_30d": mode_ratio.get("ARENA", 0.0),
            "rotating_ratio_30d": mode_ratio.get("ROTATING", 0.0),
            "other_ratio_30d": mode_ratio.get("OTHER", 0.0),
        })

    features = pd.DataFrame(rows)

    if features.empty:
        return features

    target_cols = [
        "player_id",
        "churn",
        "future30d_has_match",
        "actual_history_matches",
        "cutoff_date",
    ]

    features = features.merge(
        targets_df[target_cols],
        on="player_id",
        how="left",
    )

    features = features[
        features["actual_history_matches"] >= MIN_HISTORY_MATCHES
    ].reset_index(drop=True)

    return features


# ============================================================
# 11. STEP 14
#     Transformer sequence
# ============================================================

def make_transformer_df(history, targets_df):
    valid_players = set(
        targets_df.loc[
            targets_df["actual_history_matches"] >= MIN_HISTORY_MATCHES,
            "player_id",
        ]
    )

    transformer_df = (
        history[
            history["player_id"].isin(valid_players)
        ]
        .sort_values(["player_id", "eventTime"])
        .groupby("player_id", group_keys=False)
        .tail(MAX_HISTORY_MATCHES)
        .copy()
    )

    transformer_df["sequenceIndex"] = (
        transformer_df
        .groupby("player_id")
        .cumcount()
    )

    transformer_df["daysBeforeCutoff"] = (
        (CUTOFF - transformer_df["eventTime"])
        .dt.total_seconds()
        .div(86400)
    )

    sequence_cols = [
        "player_id",
        "sequenceIndex",
        "eventTime",
        "timeGapDays",
        "daysBeforeCutoff",

        "queueId",
        "modeGroup",
        "championId",
        "teamPosition",

        "win",
        "kills",
        "deaths",
        "assists",
        "kda",

        "gameDurationMin",
        "goldPerMin",
        "csPerMin",
        "damagePerMin",
        "visionPerMin",
    ]

    transformer_df = transformer_df[sequence_cols].merge(
        targets_df[["player_id", "churn"]],
        on="player_id",
        how="left",
    )

    return transformer_df


# ============================================================
# 12. STEP 15~17
#     Excel / Parquet / 최종확인
# ============================================================

def write_large_df(writer, df, prefix, chunk_rows=800_000):

    df = df.copy()

    # Excel은 timezone-aware datetime을 지원하지 않음
    for col in df.columns:
        if isinstance(df[col].dtype, pd.DatetimeTZDtype):
            df[col] = df[col].dt.tz_localize(None)

    if len(df) == 0:
        pd.DataFrame().to_excel(
            writer,
            sheet_name=prefix[:31],
            index=False,
        )
        return

    for i, start in enumerate(
        range(0, len(df), chunk_rows),
        start=1,
    ):
        chunk = df.iloc[start:start + chunk_rows]

        sheet_name = (
            prefix
            if i == 1
            else f"{prefix}_{i}"
        )

        chunk.to_excel(
            writer,
            sheet_name=sheet_name[:31],
            index=False,
        )

def excel_safe(df):
    df = df.copy()

    for col in df.columns:
        if isinstance(df[col].dtype, pd.DatetimeTZDtype):
            df[col] = df[col].dt.tz_localize(None)

    return df


def export_excel(
    excel_path,
    queue_df,
    cohort_df,
    targets_df,
    ml_features,
    transformer_df,
    raw_matches,
):

    # Excel 저장 전에 timezone 제거
    cohort_df = excel_safe(cohort_df)
    targets_df = excel_safe(targets_df)
    ml_features = excel_safe(ml_features)
    transformer_df = excel_safe(transformer_df)
    raw_matches = excel_safe(raw_matches)
    queue_df = excel_safe(queue_df)

    summary_df = pd.DataFrame({
        "item": [
            "cutoff_date",
            "obs_days",
            "label_days",
            "cohort_users",
            "valid_ml_users",
            "raw_match_rows",
            "transformer_rows",
            "churn_rate",
        ],
        "value": [
            CUTOFF_DATE,
            OBS_DAYS,
            LABEL_DAYS,
            len(cohort_df),
            len(ml_features),
            len(raw_matches),
            len(transformer_df),
            (
                ml_features["churn"].mean()
                if len(ml_features)
                else np.nan
            ),
        ],
    })
    with pd.ExcelWriter(
        excel_path,
        engine="xlsxwriter",
    ) as writer:
        summary_df.to_excel(
            writer,
            sheet_name="summary",
            index=False,
        )

        if len(queue_df):
            queue_df.to_excel(
                writer,
                sheet_name="queue_lookup",
                index=False,
            )

        cohort_df.to_excel(
            writer,
            sheet_name="cohort_users",
            index=False,
        )

        targets_df.to_excel(
            writer,
            sheet_name="targets",
            index=False,
        )

        ml_features.to_excel(
            writer,
            sheet_name="ml_features",
            index=False,
        )

        write_large_df(
            writer,
            transformer_df,
            "transformer",
        )

        write_large_df(
            writer,
            raw_matches,
            "raw_matches",
        )


def print_final_status(base_dir, include_excel=True):
    expected = [
        "02_cohort_users.csv",
        "03_user_match_ids.csv",
        "04_targets.csv",
        "05_raw_matches.csv",
        "06_ml_features.csv",
        "07_transformer_sequence.csv",
        "25.csv",
    ]

    if include_excel:
        expected.append("LOL_CHURN_DATASET.xlsx")

    print("\n" + "=" * 70)
    print("STEP 17 | 최종 파일 확인")
    print("=" * 70)

    for name in expected:
        path = base_dir / name
        status = "OK" if path.exists() else "--"
        print(f"{status:>2}  {path}")


# ============================================================
# 13. MAIN
# ============================================================

def main():
    args = parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    puuid_file = Path(args.puuid_file).expanduser().resolve()

    base_dir.mkdir(parents=True, exist_ok=True)

    # 파일 경로
    cohort_path = base_dir / "02_cohort_users.csv"
    user_match_ids_path = base_dir / "03_user_match_ids.csv"
    targets_path = base_dir / "04_targets.csv"
    cohort_done_path = base_dir / "_cohort_done.txt"

    raw_matches_path = base_dir / "05_raw_matches.csv"
    raw_match_done_path = base_dir / "_raw_match_done.txt"

    ml_features_path = base_dir / "06_ml_features.csv"
    transformer_path = base_dir / "07_transformer_sequence.csv"
    final_25_path = base_dir / "25.csv"

    excel_path = base_dir / "LOL_CHURN_DATASET.xlsx"

    print("=" * 70)
    print("Riot LoL Churn Pipeline | VS Code")
    print("=" * 70)
    print("BASE_DIR       :", base_dir)
    print("PUUID FILE     :", puuid_file)
    print("MODE           :", args.mode)
    print("CUTOFF         :", CUTOFF_DATE)
    print("OBS            :", OBS_START, "~", CUTOFF)
    print("LABEL          :", CUTOFF, "~", LABEL_END)
    print("MAX HISTORY    :", MAX_HISTORY_MATCHES)
    print("=" * 70)

    queue_df, queue_map = load_queue_info()

    # ----------------------------
    # 기존 STEP 10 결과 탐색
    # ----------------------------
    cohort_df = reconstruct_cohort_if_needed(
        cohort_path=cohort_path,
        user_match_ids_path=user_match_ids_path,
        targets_path=targets_path,
    )

    step10_ready = (
        user_match_ids_path.exists()
        and targets_path.exists()
        and cohort_df is not None
    )

    # mode 판정
    if args.mode == "resume":
        if not step10_ready:
            raise RuntimeError(
                "--mode resume을 선택했지만 STEP 10 결과가 없습니다.\n"
                "Colab의 lol_churn_project 폴더에서 최소 다음 파일을 복사하세요:\n"
                "  02_cohort_users.csv\n"
                "  03_user_match_ids.csv\n"
                "  04_targets.csv\n"
                "  _cohort_done.txt (있으면 함께)\n"
            )

        run_step10 = False

    elif args.mode == "from-puuid":
        print(
            "\n[주의] from-puuid 모드는 새 cohort를 만듭니다. "
            "기존 03/04와 섞이지 않도록 별도 base-dir 사용을 권장합니다."
        )

        if user_match_ids_path.exists() or targets_path.exists():
            raise RuntimeError(
                "현재 BASE_DIR에 기존 STEP 10 파일이 있습니다.\n"
                "새 PUUID cohort를 만들려면 새 폴더를 --base-dir로 지정하세요.\n"
                "예: python riot_churn_vscode.py --mode from-puuid "
                "--cohort-size 3000 --base-dir ./lol_churn_project_3000"
            )

        cohort_df = build_cohort_from_puuid_file(
            puuid_file=puuid_file,
            cohort_path=cohort_path,
            cohort_size=args.cohort_size,
        )
        run_step10 = True

    else:  # auto
        if step10_ready:
            print(
                "\n[AUTO] 기존 STEP 10 결과 발견 -> "
                "11번부터 이어서 실행합니다."
            )
            run_step10 = False

        else:
            print(
                "\n[AUTO] STEP 10 결과가 없음 -> "
                "puuids.csv에서 cohort를 만들고 10번부터 실행합니다."
            )

            cohort_df = build_cohort_from_puuid_file(
                puuid_file=puuid_file,
                cohort_path=cohort_path,
                cohort_size=args.cohort_size,
            )
            run_step10 = True

    cohort_df = ensure_player_id(cohort_df)
    cohort_df = (
        cohort_df
        .drop_duplicates("puuid")
        .reset_index(drop=True)
    )
    cohort_df.to_csv(
        cohort_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"[Cohort] {len(cohort_df):,}명")

    # API 호출이 필요한 단계 직전에 Key 입력
    set_api_key()

    # ----------------------------
    # STEP 10
    # ----------------------------
    if run_step10:
        user_match_ids_df, targets_df = (
            collect_cohort_match_ids_and_targets(
                cohort_df=cohort_df,
                user_match_ids_path=user_match_ids_path,
                targets_path=targets_path,
                cohort_done_path=cohort_done_path,
            )
        )

    else:
        user_match_ids_df = pd.read_csv(user_match_ids_path)
        targets_df = pd.read_csv(targets_path)

        user_match_ids_df = (
            user_match_ids_df
            .drop_duplicates(["puuid", "matchId", "split"])
            .reset_index(drop=True)
        )

        targets_df = (
            targets_df
            .drop_duplicates("puuid", keep="last")
            .reset_index(drop=True)
        )

        print(
            f"[STEP 10 불러오기] Match-ID rows="
            f"{len(user_match_ids_df):,}, Targets={len(targets_df):,}"
        )

    # ----------------------------
    # STEP 11
    # ----------------------------
    raw_matches = collect_raw_match_details(
        user_match_ids_df=user_match_ids_df,
        cohort_df=cohort_df,
        raw_matches_path=raw_matches_path,
        raw_match_done_path=raw_match_done_path,
        queue_map=queue_map,
    )

    # ----------------------------
    # STEP 12
    # ----------------------------
    raw_matches, history, targets_df = preprocess_time(
        raw_matches=raw_matches,
        targets_df=targets_df,
        targets_path=targets_path,
    )

    # STEP 12 결과까지 raw_matches에 timeGapDays/eventTime 반영하여 저장
    raw_matches.to_csv(
        raw_matches_path,
        index=False,
        encoding="utf-8-sig",
    )

    # ----------------------------
    # STEP 13
    # ----------------------------
    ml_features = make_ml_features(
        history=history,
        targets_df=targets_df,
    )

    ml_features.to_csv(
        ml_features_path,
        index=False,
        encoding="utf-8-sig",
    )

    ml_features.to_csv(
        final_25_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"[STEP 13 완료] Boosting 데이터="
        f"{ml_features.shape}"
    )

    # ----------------------------
    # STEP 14
    # ----------------------------
    transformer_df = make_transformer_df(
        history=history,
        targets_df=targets_df,
    )

    transformer_df.to_csv(
        transformer_path,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"[STEP 14 완료] Transformer 데이터="
        f"{transformer_df.shape}"
    )

    # ----------------------------
    # STEP 15
    # ----------------------------
    use_excel = EXPORT_EXCEL and not args.no_excel

    if use_excel:
        export_excel(
            excel_path=excel_path,
            queue_df=queue_df,
            cohort_df=cohort_df,
            targets_df=targets_df,
            ml_features=ml_features,
            transformer_df=transformer_df,
            raw_matches=raw_matches,
        )

        print(f"[STEP 15 완료] {excel_path}")

    # ----------------------------
    # STEP 16
    # ----------------------------
    use_parquet = EXPORT_PARQUET and not args.no_parquet

    if use_parquet:
        try:
            raw_matches.to_parquet(
                base_dir / "05_raw_matches.parquet",
                index=False,
            )

            transformer_df.to_parquet(
                base_dir / "07_transformer_sequence.parquet",
                index=False,
            )

            print("[STEP 16 완료] Parquet 저장")

        except Exception as exc:
            print(
                "[경고] Parquet 저장 실패. "
                "pyarrow 설치 여부를 확인하세요:",
                exc,
            )

    # ----------------------------
    # STEP 17
    # ----------------------------
    print_final_status(
        base_dir=base_dir,
        include_excel=use_excel,
    )

    print("\n완료.")
    print(
        "Boosting 입력 :",
        ml_features_path,
    )
    print(
        "Transformer 입력:",
        transformer_path,
    )


if __name__ == "__main__":
    main()
