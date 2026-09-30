# LoL 이탈 예측

진성 활동 고객의 30일 무경기 위험을 CatBoost로 순위화하고, React 대시보드에서 조회하는 프로젝트입니다.

## 폴더

| 경로 | 역할 |
|---|---|
| `data_collection/` | Riot API 수집 스크립트 |
| `data_pipeline/` | SQLite 적재, 코호트·세그먼트·행동 요약 |
| `modeling/` | CatBoost 학습, 불균형 비교, 군집, 합성 생존분석 |
| `models/` | 학습 산출물과 실험 기록 |
| `backend/` | FastAPI |
| `frontend/` | 현재 React 대시보드 |
| `archive/react-dashboard/` | 초기 화면 목업 |
| `docs/` | 정책, 보고서, 기획 문서 |
| `deliverables/` | 발표 자료 |
| `requirements.txt` | 공통 파이썬 패키지 |
| `requirements/` | 분석·모델링용 패키지 목록 |

원본 CSV와 SQLite(`lol_churn_all_data/`)는 저장소에 포함하지 않습니다. 화면만 볼 때는 백엔드에 들어 있는 조회용 JSON을 사용합니다.

자세한 실행 방법은 [프로젝트 구성](docs/PROJECT_LAYOUT.md)을 보세요.

## 배포

백엔드는 Render, 화면은 Vercel을 사용합니다. 브라우저는 Vercel의 `/api`로 요청하고, `vercel.json`이 Render API로 전달합니다.

1. Render에서 이 저장소를 Blueprint(`render.yaml`)로 연결합니다. 서비스 주소는 `https://skn36-lol-churn-api.onrender.com` 입니다.
2. Vercel에서 같은 저장소를 Import 합니다. Framework Preset은 Other, 출력 폴더는 `frontend/dist` 입니다.
3. Render가 다른 주소를 주면 `vercel.json`의 `rewrites.destination`을 그 주소로 바꾼 뒤 다시 배포합니다.
