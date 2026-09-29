# EDA, 전처리 및 코호트 분석

이 브랜치에는 원천 데이터를 정리하고 분석용 테이블을 만드는 코드만 둡니다. 원본 경기·사용자 데이터와 SQLite DB는 저장소에 포함하지 않습니다.

## 입력 데이터

재현 실행 시 별도 배포되는 `lol_churn_all_data/`를 저장소 루트에 둡니다. 기본 DB 생성기는 `final/final_ml_features.csv`와 `final/final_transformer_sequence.csv`를 읽어 `database/lol_churn.db`를 만듭니다.

## 주요 코드

- `data_pipeline/build_sqlite_db.py`: 최종 피처·경기 시퀀스 CSV를 SQLite 테이블로 적재
- `data_pipeline/prepare_core_cohorts.py`: 기준일 이전 활동으로 진성 활동 고객 코호트 생성
- `data_pipeline/build_core_segment_db.py`: 코호트와 플레이 유형·활동 추세 테이블 생성
- `data_pipeline/behavior_analysis.py`: 사용자별 최근 행동 요약과 변화 신호 분석
- `data_analysis/explore_core_clusters.py`: 진성 활동 고객의 플레이 특성 군집 탐색

## 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-data-analysis.txt
python -m data_pipeline.build_sqlite_db
python -m data_pipeline.prepare_core_cohorts
python -m data_pipeline.build_core_segment_db
python -m data_pipeline.behavior_analysis 1 <PLAYER_ID>
python data_analysis/explore_core_clusters.py
```

이 분석용 명령들은 별도 데이터 폴더가 있어야 합니다. **대시보드 화면만 실행할 때는 이 전처리를 돌릴 필요가 없고**, 대시보드 브랜치에 포함된 화면 스냅샷을 사용합니다.
