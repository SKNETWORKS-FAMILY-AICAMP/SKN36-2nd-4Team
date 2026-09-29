import pandas as pd

base = r"C:\dev\project\riot_churn_vscode_bundle\lol_churn_project"

# 전체 cohort 500명
cohort = pd.read_csv(f"{base}\\02_cohort_users.csv")

# 경기 상세 데이터
raw = pd.read_csv(f"{base}\\05_raw_matches.csv")

print("raw 컬럼:")
print(raw.columns.tolist())

# 솔로랭크 경기만
solo = raw[raw["queueId"] == 420]

# 솔로랭크를 한 유저
solo_users = solo["player_id"].unique()

print("\n전체 cohort 유저 수:", len(cohort))
print("솔로랭크 경험 유저 수:", len(solo_users))
print("솔로랭크 경험 비율:", len(solo_users) / len(cohort))

print("\n솔로랭크 경기 수:", len(solo))