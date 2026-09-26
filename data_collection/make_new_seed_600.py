import pandas as pd
from pathlib import Path

BASE = Path(r"C:\dev\project\riot_churn_vscode_bundle")

PUUID_PATH = BASE / "puuids.csv"
OLD_COHORT_PATH = BASE / "lol_churn_project" / "02_cohort_users.csv"

TOTAL_SEED = 600
SEED_PER_TEAM = 150
N_TEAMS = 4
RANDOM_STATE = 42


def detect_id_column(df):
    if "puuid" in df.columns:
        return "puuid"
    if "player_id" in df.columns:
        return "player_id"
    raise ValueError(
        "PUUID 컬럼을 찾을 수 없습니다. "
        f"현재 컬럼: {df.columns.tolist()}"
    )


def main():
    print("=" * 70)
    print("새 Seed 600명 생성")
    print("=" * 70)

    if not PUUID_PATH.exists():
        raise FileNotFoundError(
            f"puuids.csv를 찾을 수 없습니다:\n{PUUID_PATH}"
        )

    pool = pd.read_csv(PUUID_PATH)
    pool_col = detect_id_column(pool)

    print("\n[1] 원본 PUUID 풀")
    print("원본 행 수:", len(pool))
    print("ID 컬럼:", pool_col)

    pool = pool.dropna(subset=[pool_col]).copy()
    pool[pool_col] = pool[pool_col].astype(str).str.strip()
    pool = pool.drop_duplicates(subset=[pool_col]).copy()

    print("중복 제거 후:", len(pool))

    if not OLD_COHORT_PATH.exists():
        raise FileNotFoundError(
            f"기존 cohort 파일을 찾을 수 없습니다:\n{OLD_COHORT_PATH}"
        )

    old = pd.read_csv(OLD_COHORT_PATH)
    old_col = detect_id_column(old)

    old = old.dropna(subset=[old_col]).copy()
    old[old_col] = old[old_col].astype(str).str.strip()
    old_ids = set(old[old_col])

    before = len(pool)
    pool = pool[~pool[pool_col].isin(old_ids)].copy()

    print("\n[2] 기존 500명 제외")
    print("기존 cohort 고유 PUUID:", len(old_ids))
    print("제외 전:", before)
    print("제외 후:", len(pool))

    if len(pool) < TOTAL_SEED:
        raise ValueError(
            f"후보 PUUID가 부족합니다. 필요={TOTAL_SEED}, 현재={len(pool)}"
        )

    seed_all = (
        pool.sample(n=TOTAL_SEED, random_state=RANDOM_STATE)
        .reset_index(drop=True)
        .copy()
    )

    seed_all = seed_all[[pool_col]].rename(columns={pool_col: "puuid"})

    all_output = BASE / "new_seed_600.csv"
    seed_all.to_csv(all_output, index=False)

    print("\n[3] 새 seed 600명 생성")
    print("전체 seed:", len(seed_all))
    print("고유 PUUID:", seed_all["puuid"].nunique())
    print("저장:", all_output)

    print("\n[4] 팀별 seed 생성")
    team_frames = []

    for i in range(N_TEAMS):
        start = i * SEED_PER_TEAM
        end = start + SEED_PER_TEAM

        part = seed_all.iloc[start:end].copy()
        output_path = BASE / f"seed_team_{i+1}.csv"
        part.to_csv(output_path, index=False)
        team_frames.append(part)

        print(f"team_{i+1}: {len(part)}명 -> {output_path}")

    combined = pd.concat(team_frames, ignore_index=True)

    overlap_old = combined["puuid"].isin(old_ids).sum()
    duplicated = combined["puuid"].duplicated().sum()

    print("\n" + "=" * 70)
    print("검증 결과")
    print("=" * 70)
    print("팀 파일 합계:", len(combined))
    print("고유 PUUID:", combined["puuid"].nunique())
    print("팀 간 중복:", duplicated)
    print("기존 500명과 중복:", overlap_old)

    if (
        len(combined) == TOTAL_SEED
        and combined["puuid"].nunique() == TOTAL_SEED
        and duplicated == 0
        and overlap_old == 0
    ):
        print("\nOK: 새 seed 600명 생성 완료")
        print("OK: 기존 500명과 중복 없음")
        print("OK: 4개 팀 seed 간 중복 없음")
    else:
        print("\n주의: 검증 결과를 확인하세요.")


if __name__ == "__main__":
    main()
