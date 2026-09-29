# 프로젝트 파일 안내

## 주요 폴더

| 폴더 | 역할 |
|---|---|
| `data_pipeline/` | SQLite 생성, 활동 고객 코호트 구성, 세그먼트 DB·행동 요약 생성 |
| `modeling/` | CatBoost 학습·평가, 불균형 처리 비교, 군집화·합성 생존분석 실험 |
| `lol_churn_all_data/` | 입력 CSV, 파생 CSV, SQLite 데이터와 스키마 설명 |
| `models/` | 학습 모델, 지표, 실험 보고서 및 비교표 산출물 |
| `notebooks/` | 탐색·분석용 Jupyter 노트북 |
| `merged-app/backend/` | 현재 React 화면에서 사용하는 FastAPI API |
| `merged-app/frontend/` | React 대시보드 화면 |

원본·통합 CSV, DB, 학습 산출물은 이번 정리에서 삭제하거나 다시 만들지 않았습니다. 파이썬 스크립트만 책임별 폴더로 이동했습니다.

## 자주 쓰는 명령

아래 명령은 프로젝트 루트에서 실행합니다.

```powershell
python -m data_pipeline.build_sqlite_db
python -m data_pipeline.prepare_core_cohorts
python -m data_pipeline.build_core_segment_db
python -m modeling.train_core_churn
python -m modeling.compare_core_imbalance
python -m modeling.reselect_core_features
python merged-app/backend/prepare_core_dashboard_data.py
python -m modeling.train_synthetic_survival
```

기존 가상환경을 쓰는 경우 `python` 대신 `..\.venv\Scripts\python.exe` 같은 다른 폴더 경로를 임의로 섞지 말고, 프로젝트 루트에서 활성화된 환경의 Python으로 실행하세요.

## 현재 분석 범위

- 전체 수집: 9,879명
- CatBoost 대상 코호트: 2,381명 (`games_prev30d >= 4` 및 `games_30d > 0`)
- 기준일: 2026-08-01
- 피처 참조 범위: 기준일 전 최대 90일 (30일 비교 구간 및 최근 20경기 요약 포함)
- 라벨: 기준일 이후 30일 동안 추가 경기 기록이 없는지 여부
- 이 라벨은 게임 미활동 기준이며 계정 탈퇴 여부를 뜻하지 않습니다.
- 현재 대시보드는 [재선정 결과](models/core_reselected_2026-08-01/RESULTS.md)의 선택 후보 OOF 점수와 진성 고객 SHAP을 표시합니다. 후보 선택까지 포함한 중첩 검증 성능도 별도로 표기합니다.
