# 🎮 League of Legends User Churn Prediction

> **Riot Games API 기반 League of Legends 사용자 행동 분석 및 이탈 예측 서비스**

SK Networks Family AI Camp 36기  
**2nd Project · Team 4**

---

## 📌 Project Overview

League of Legends 사용자들의 경기 기록을 수집하고 분석하여  
**기준일 이후 30일 동안 경기를 하지 않을 가능성이 높은 사용자를 찾고, 대시보드에서 확인하는 서비스**입니다.

Riot Games API로 사용자와 경기 기록을 수집하고, 기준일 이전 활동으로 피처를 만든 뒤 CatBoost로 이탈 위험 순위를 계산합니다.  
여기서 이탈은 계정 탈퇴가 아니라, **기준일 2026-08-01 이후 30일 동안 경기 기록이 없는 상태**입니다.

예측 결과는 **React + TypeScript + FastAPI** 대시보드에서 확인합니다.  
화면은 저장소에 포함된 조회용 JSON을 읽으므로, 원본 CSV 없이도 대시보드를 실행할 수 있습니다.

### 핵심 흐름

```text
Riot Games API
      │
      ▼
사용자·경기 수집          data_collection/
      │
      ▼
코호트·피처·시퀀스         data_pipeline/  ,  lol_churn_all_data/
      │
      ▼
CatBoost 이탈 순위         modeling/  ,  models/
      │
      ▼
조회용 JSON               backend/app/data/
      │
      ▼
React Dashboard           frontend/
```

---

# 🎯 Project Goal

본 프로젝트의 핵심 목표는 단순한 데이터 분석이 아니라,

> **꾸준히 플레이하던 사용자 중, 기준일 이후 30일 무경기 위험이 높은 사람을 순위화하는 것**

입니다.

- Riot API로 사용자와 경기 기록을 수집
- 기준일 이전 기록만으로 활동·성과·모드 피처 생성
- 진성 활동 고객 코호트 정의
- CatBoost로 이탈 위험 순위 산출
- 위험 사용자와 사용자별 활동 변화를 대시보드에 표시

화면의 점수는 보정된 이탈 확률이 아니라, 고객 간 우선순위를 정하는 모델 출력입니다.

---

# 🧩 Service Architecture

```text
┌───────────────────────┐
│    Riot Games API     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   data_collection/    │
│  시드·코호트·경기 수집  │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   data_pipeline/      │
│  SQLite·코호트·세그먼트 │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  modeling/ · models/  │
│  CatBoost · 비교 실험  │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   backend/  FastAPI   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│  frontend/  React     │
│  전체 현황·위험 사용자  │
│  사용자 상세·모델 성능  │
└───────────────────────┘
```

---

# 📊 Data Pipeline

수집 스크립트는 `data_collection/`에 있습니다.  
팀별 원본은 저장소 밖 `lol_churn_all_data/`에 두고, 통합 결과는 그 안의 `final/`과 `derived/`에 있습니다. 이 데이터 폴더는 GitHub에 올리지 않습니다.

## 1. Seed User Collection

리그 티어에서 시드 사용자를 모아 이후 경기 조회의 시작점으로 씁니다.

```text
Tier / Rank
     │
     ▼
Summoner
     │
     ▼
PUUID
```

배치 폴더의 `01_seed_users.csv`가 이 단계의 결과입니다.

## 2. Cohort Construction

수집된 사용자 중 분석 가능한 대상을 고릅니다.  
대시보드와 CatBoost가 쓰는 **진성 활동 고객** 조건은 아래와 같습니다.

- 기준일: 2026-08-01
- 기준일 이전 30일에 4경기 이상 (`games_prev30d >= 4`)
- 기준일 직전 30일에 1경기 이상 (`games_30d > 0`)
- 전체 수집 9,879명 중 2,381명
- 그중 기준일 이후 30일 무경기는 363명(15.25%)

분리 코드는 `data_pipeline/prepare_core_cohorts.py`입니다. 정책은 [코호트 문서](docs/reports/CORE_COHORT_POLICY.md)에 있습니다.

## 3. Match ID Collection

사용자별 식별자로 경기 ID 목록을 수집합니다. 배치 결과는 `03_user_match_ids.csv`입니다.

## 4. Match Detail Collection

경기 ID로 상세 기록을 가져옵니다. 배치 결과는 `05_raw_matches.csv`입니다.

- 게임 모드, 경기 시각, 플레이 시간
- 승패, Kill / Death / Assist, KDA
- 골드, 피해량, CS, 시야 점수

## 5. Feature Engineering

기준일 이전 최대 90일 기록으로 사용자 단위 피처를 만듭니다. 기준일 이후 정보는 입력에 넣지 않습니다.

```text
최근 7·30·90일 경기 수
직전 30일 대비 활동 변화
마지막 경기 이후 경과일
평균·최대 경기 간격
최근 20경기 승률·KDA·CS·시야
연패, 승률 변화
모드별 플레이 비율, 모드 전환율
```

학습용 통합 파일은 `lol_churn_all_data/final/final_ml_features.csv`입니다.  
경기 시퀀스는 `final/final_transformer_sequence.csv`이며, Transformer 실험과 사용자 상세의 최근 경기 표시에 사용합니다. Transformer는 이탈 예측 모델로 채택하지 않았습니다.

---

# 📁 Dataset

번호 파일은 팀·배치 폴더(`lol_churn_all_data/team*/`)와 `merged_team/`에 있습니다.

| 파일 | 설명 |
|---|---|
| `01_seed_users.csv` | 최초 수집 사용자 |
| `02_cohort_users.csv` | 수집 코호트 |
| `03_user_match_ids.csv` | 사용자별 경기 ID |
| `04_targets.csv` | 기준일 이후 30일 무경기 라벨 |
| `05_raw_matches.csv` | 경기 상세 |
| `06_ml_features.csv` | 사용자 단위 피처 |
| `07_transformer_sequence.csv` | 사용자별 최근 경기 시퀀스 |
| `final/final_ml_features.csv` | 팀 통합 피처. 9,879명 |
| `final/final_transformer_sequence.csv` | 팀 통합 시퀀스. 270,181행 |

원본 CSV, SQLite, API 키, 사용자별 OOF 원본은 저장소에서 제외합니다.  
대시보드가 읽는 요약은 `backend/app/data/core_dashboard.json`과 `core_model_experiment.json`입니다.

---

# 🧠 Churn Definition

```text
기준일 2026-08-01
       │
       ├─ 이전 최대 90일  →  모델 입력
       │
       └─ 이후 30일       →  라벨
              경기 0회면 churn = 1
              경기 1회 이상이면 churn = 0
```

한 경기의 승패로 이탈을 정하지 않습니다.  
라벨은 계정 탈퇴나 로그인 중단이 아니라 **경기 기록** 기준입니다.

---

# 🤖 Machine Learning

이탈 순위 모델은 **CatBoost**입니다.  
같은 진성 활동 고객과 같은 5-fold 분할에서 XGBoost, LightGBM을 비교했고, 클래스 가중치·ROS·SMOTE도 함께 봤습니다. 채택 후보는 기존 집계 피처와 CatBoost 클래스 균형 가중치입니다.

경기 시퀀스 Transformer와 합성 생존분석은 비교·시연용입니다. 운영 이탈 점수로 쓰지 않습니다.  
생존분석 화면은 실제 장기 관측이 없어 만든 합성 데모입니다.

학습 코드는 `modeling/`, 결과와 보고서는 `models/`에 있습니다.

| 문서 | 내용 |
|---|---|
| [재선정 결과](models/core_reselected_2026-08-01/RESULTS.md) | 대시보드에 쓰는 진성 고객 모델 |
| [코호트 정책](docs/reports/CORE_COHORT_POLICY.md) | 대상 사용자 정의 |
| [Transformer 실험](docs/reports/TRANSFORMER_EXPERIMENTS.md) | 시퀀스 모델은 미채택 |

## Model Evaluation

이탈 사용자는 363명으로 전체의 15.25%라서 Accuracy만으로 평가하지 않습니다.

| Metric | 이 프로젝트에서 보는 것 |
|---|---|
| PR-AUC | 불균형 데이터에서 이탈 순위의 핵심 지표 |
| ROC-AUC | 전체 순위 분리 |
| Precision / Recall / F1 | 위험 점수 상위 10%, 20%를 조치 대상으로 잡았을 때의 탐지 결과 |
| Confusion Matrix | 상위 20% 기준 탐지·오탐 |
| SHAP | 예측에 쓰인 피처 크기. 이탈 원인이나 캠페인 효과는 아님 |

---

# 🖥 Dashboard

| 화면 | 경로 | 내용 |
|---|---|---|
| 전체 현황 | `/dashboard` | 수집 인원, 진성 고객, 실제 30일 무경기, 모드별 집계 |
| 위험 사용자 | `/risk-users` | CatBoost OOF 순위, 검색, 위험 등급 필터 |
| 사용자 상세 | `/users/:playerId` | 최근 경기, 활동 간격, 모드 분포 |
| 모델 성능 | `/model` | PR-AUC, ROC-AUC, 상위 20% 혼동행렬, SHAP |
| 데이터 설명 | `/data` | 이탈 정의, 코호트 규칙, 피처 범위 |
| 생존분석 확장 | `/survival` | 합성 Cox 데모. 운영 점수가 아님 |

위험 사용자 화면의 게임 모드 필터는 전체 현황에 있습니다.  
위험 목록은 위험 등급과 사용자 ID로 거르고, 한 페이지에 20명씩 불러옵니다.

---

# 🛠 Tech Stack

## Data

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)

## Machine Learning

![CatBoost](https://img.shields.io/badge/CatBoost-FFCC00?style=flat-square&logoColor=black)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-FF6600?style=flat-square)
![LightGBM](https://img.shields.io/badge/LightGBM-02569B?style=flat-square)

## Backend

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)

## Frontend

![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![Apache ECharts](https://img.shields.io/badge/Apache%20ECharts-AA344D?style=flat-square)

## Deploy

![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)

## Collaboration

![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)

---

# 📂 Project Structure

```text
SKN36_2ND_LOL_CHURN/
│
├── frontend/                 React + TypeScript + Vite 대시보드
│   ├── src/
│   │   ├── api/              API 클라이언트
│   │   ├── features/         화면별 페이지
│   │   └── components/       공통 화면 조각
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  FastAPI
│   ├── app/
│   │   ├── main.py           앱 진입점
│   │   ├── api/routes/       경로별 API
│   │   ├── services/         조회 로직
│   │   └── data/             대시보드가 읽는 JSON
│   ├── prepare_core_dashboard_data.py
│   └── requirements.txt
│
├── data_collection/          Riot API 수집 스크립트
├── data_pipeline/            SQLite, 코호트, 세그먼트, 행동 요약
├── modeling/                 CatBoost 학습, 비교, 군집, 합성 생존분석
├── models/                   학습 결과와 실험 보고서
│
├── docs/
│   ├── reports/              코호트 정책, 모델·Transformer 기록
│   ├── guides/               전처리 재현 절차
│   ├── plans/                대시보드 후속 메모
│   └── planning/             기획 PDF
├── deliverables/             발표 PPT
├── archive/react-dashboard/  API 연결 전 화면 목업
│
├── requirements/             분석·모델링 패키지 목록
├── requirements.txt
├── render.yaml               Render 백엔드 배포
├── vercel.json               Vercel 프론트 배포
├── .gitignore
└── README.md
```

재현용 원본은 저장소 루트에 `lol_churn_all_data/`로 둡니다. 이 폴더는 Git에 포함하지 않습니다.

---

# 🚀 Installation

```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN36-2nd-4Team.git
cd SKN36-2nd-4Team
```

---

# ⚙️ Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

앱 모듈은 `app.main:app`입니다. `uvicorn main:app`으로는 실행되지 않습니다.

---

# 🌐 Frontend

백엔드를 켠 터미널은 그대로 두고, 새 터미널에서 실행합니다.

```bash
cd frontend
npm install
npm run dev
```

```text
http://localhost:5173
```

개발 서버는 `/api` 요청을 `http://127.0.0.1:8000`으로 넘깁니다.

---

# ☁️ Deployment

백엔드는 Render, 화면은 Vercel을 사용합니다. 브라우저는 Vercel의 `/api`로 요청하고, `vercel.json`이 Render API로 전달합니다.

1. Render에서 이 저장소를 Blueprint(`render.yaml`)로 연결합니다. 예정 주소는 `https://skn36-lol-churn-api.onrender.com` 입니다.
2. Vercel에서 같은 저장소를 Import 합니다. 빌드 설정은 루트의 `vercel.json`을 따릅니다.
3. Render 주소가 달라지면 `vercel.json`의 `rewrites.destination`을 그 주소로 바꾼 뒤 Vercel을 다시 배포합니다.

---

# 🔑 Environment Variables

실제 비밀 값은 GitHub에 올리지 않습니다. 예시는 `backend/.env.example`, `frontend/.env.example`에 있습니다.

Backend `backend/.env`

```env
APP_ENV=development
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Frontend는 개발 중 별도 값이 없어도 됩니다. 배포 환경에서 API 주소를 직접 지정할 때만 사용합니다.

```env
VITE_API_BASE_URL=/api/v1
```

데이터 수집을 다시 실행할 때만 Riot API 키가 필요합니다. 수집 스크립트를 실행하는 터미널에 환경 변수로 넣습니다.

```powershell
$env:RIOT_API_KEY = "발급받은 키"
```

---

# 🌿 Repository

정리된 코드는 `main`에 있습니다. `develop`과 `feature/*`는 폴더 정리 전 작업 기록입니다.

```text
data_collection/   Riot API 수집
data_pipeline/     전처리·코호트
modeling/          이탈 모델
frontend/          대시보드 화면
backend/           대시보드 API
```

---

# ⚠️ GitHub Upload Policy

다음 파일은 GitHub에 업로드하지 않습니다.

```text
.venv/
node_modules/
__pycache__/
.env
*.db
*.sqlite
*.parquet
*.xlsx
frontend/dist/
lol_churn_all_data/
models/**/oof_predictions.*
```

제외 대상은 Riot API 키, 대용량 원본 데이터, 로컬 DB, 가상환경, 사용자별 OOF 예측 원본입니다.

---

# 👥 Team

**SK Networks Family AI Camp 36기**  
**2nd Project · Team 4**

| Role | Responsibility |
|---|---|
| Data Collection | Riot API 기반 사용자 및 경기 데이터 수집 |
| Data Analysis | 코호트, 전처리, 피처 생성 |
| Modeling | CatBoost 이탈 예측과 비교 실험 |
| Dashboard | React / FastAPI 웹 서비스 |

---

# 🔮 Expected Value

```text
기준일 이전 경기 기록
        ↓
활동 변화와 플레이 패턴
        ↓
30일 무경기 위험 순위
        ↓
상위 사용자 식별
        ↓
조치 후보 검토
```

이 점수로 보상이나 매칭을 바로 바꾸지는 않습니다.  
캠페인 효과는 별도의 A/B 테스트로 확인해야 합니다.

---

# 📎 Notes

교육 및 데이터 분석 프로젝트입니다.

League of Legends와 Riot Games 데이터는 Riot Games API로 수집했습니다.  
이 프로젝트는 Riot Games의 공식 서비스가 아닙니다.
