# 🎮 League of Legends User Churn Prediction

> **Riot Games API 기반 League of Legends 사용자 행동 분석 및 이탈 예측 서비스**

SK Networks Family AI Camp 36기  
**2nd Project · Team 4**

---

## 📌 Project Overview

League of Legends 사용자들의 최근 게임 활동 데이터를 수집하고 분석하여  
**사용자의 게임 이탈 가능성을 예측하고 위험 사용자를 시각적으로 확인할 수 있는 서비스**입니다.

Riot Games API를 활용하여 실제 사용자 데이터를 수집하고,  
게임 플레이 패턴을 기반으로 머신러닝 모델을 학습하여 사용자의 이탈 위험도를 예측합니다.

예측 결과는 **React + FastAPI 기반 웹 대시보드**에서 확인할 수 있도록 구현했습니다.

### 핵심 흐름

```text
Riot Games API
      │
      ▼
사용자 PUUID 수집
      │
      ▼
Match ID 수집
      │
      ▼
게임 상세 데이터 수집
      │
      ▼
데이터 전처리 / Feature Engineering
      │
      ▼
이탈 여부 정의
      │
      ▼
Machine Learning Model
      │
      ▼
FastAPI Backend
      │
      ▼
React Dashboard
```

---

# 🎯 Project Goal

본 프로젝트의 핵심 목표는 단순한 데이터 분석이 아니라,

> **사용자의 게임 행동 패턴을 기반으로 이탈 가능성이 높은 사용자를 조기에 탐지하는 것**

입니다.

이를 위해 다음과 같은 과정을 수행합니다.

- Riot API 기반 실제 사용자 데이터 수집
- 사용자별 최근 경기 기록 분석
- 게임 활동 패턴 기반 이탈 기준 정의
- 머신러닝 학습용 Feature 생성
- 사용자 이탈 예측 모델 구축
- 위험 사용자 탐지
- 사용자별 상세 분석
- 웹 기반 데이터 시각화

---

# 🧩 Service Architecture

```text
┌───────────────────────┐
│    Riot Games API     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│    Data Collection    │
│                       │
│  PUUID / Match ID     │
│  Match Detail         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Data Preprocessing    │
│ Feature Engineering   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│    Churn Prediction   │
│    Machine Learning   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│      FastAPI API      │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   React Dashboard     │
│                       │
│ 위험 사용자 분석       │
│ 사용자 상세 분석       │
│ 모델 성능 분석         │
└───────────────────────┘
```

---

# 📊 Data Pipeline

## 1. Seed User Collection

League API를 활용하여 초기 사용자 집단을 확보합니다.

```text
Tier / Rank
     │
     ▼
Summoner
     │
     ▼
PUUID
```

수집된 사용자는 이후 Match API를 통해 경기 기록을 조회하기 위한 기준 데이터로 사용됩니다.

---

## 2. Cohort Construction

수집된 사용자 중 프로젝트 분석 기준에 적합한 사용자를 선정하여  
최종 분석 Cohort를 구성합니다.

주요 고려 요소는 다음과 같습니다.

- 사용자 활동 여부
- 최근 경기 존재 여부
- 데이터 수집 가능 여부
- 분석에 필요한 경기 수 확보 여부

---

## 3. Match ID Collection

사용자별 PUUID를 기준으로 최근 경기 Match ID를 수집합니다.

```text
PUUID
  │
  ├─ Match 1
  ├─ Match 2
  ├─ Match 3
  │
  └─ ...
```

사용자별 최근 경기 데이터를 기반으로 게임 활동 패턴을 분석합니다.

---

## 4. Match Detail Collection

수집된 Match ID를 활용하여 경기 상세 정보를 가져옵니다.

주요 데이터 예시는 다음과 같습니다.

- 게임 모드
- 플레이 시간
- 승/패
- Kill / Death / Assist
- 골드 획득량
- Damage
- CS
- Vision Score
- 경기 시간
- 경기 시작 시각

---

## 5. Feature Engineering

원본 경기 데이터에서 사용자 행동을 설명할 수 있는 머신러닝 Feature를 생성합니다.

예시 Feature:

```text
최근 경기 수
평균 플레이 시간
평균 Kill
평균 Death
평균 Assist
평균 KDA
평균 Damage
평균 Gold
평균 CS
평균 Vision Score
승률
최근 활동 간격
경기 간 시간 간격
활동 빈도
게임 모드별 플레이 비율
```

단순 경기 결과뿐 아니라 **시간에 따른 사용자 행동 변화**를 반영하기 위한 파생변수도 활용합니다.

---

# 📁 Dataset

프로젝트에서 생성되는 주요 데이터 파일은 다음과 같습니다.

| 파일 | 설명 |
|---|---|
| `01_seed_users.csv` | 최초 수집 사용자 데이터 |
| `02_cohort_users.csv` | 분석 대상 사용자 Cohort |
| `03_user_match_ids.csv` | 사용자별 Match ID |
| `04_targets.csv` | 사용자별 이탈 Target |
| `05_raw_matches.csv` | Riot API 경기 상세 Raw Data |
| `06_ml_features.csv` | 머신러닝 학습용 Feature |
| `07_transformer_sequence.csv` | 시계열 / Sequence 모델용 데이터 |

대용량 Raw Data와 API를 통해 생성되는 개인 실행 결과는 GitHub 저장소에서 제외할 수 있습니다.

---

# 🧠 Churn Definition

본 프로젝트에서는 사용자의 최근 게임 활동을 기반으로  
**활동 사용자와 이탈 위험 사용자를 구분**합니다.

```text
사용자 경기 기록
       │
       ▼
최근 활동 패턴 분석
       │
       ▼
게임 빈도 / 활동 간격 / 최근 활동일
       │
       ▼
Churn Target 생성
```

단순히 한 경기의 승패만으로 이탈을 판단하지 않고,  
**사용자의 일정 기간 게임 활동 패턴**을 종합적으로 활용합니다.

---

# 🤖 Machine Learning

사용자의 행동 Feature를 기반으로 이탈 여부를 예측합니다.

프로젝트에서는 여러 머신러닝 모델을 비교하여  
이탈 탐지에 적합한 모델을 선정합니다.

예시 모델:

```text
Logistic Regression
Random Forest
XGBoost
LightGBM
CatBoost
```

---

## Model Evaluation

사용자 이탈 데이터는 정상 사용자와 이탈 사용자 간 클래스 비율이 다를 수 있으므로  
단순 Accuracy만으로 모델을 평가하지 않습니다.

주요 평가 지표:

| Metric | 설명 |
|---|---|
| Precision | 이탈로 예측한 사용자 중 실제 이탈 사용자 비율 |
| Recall | 실제 이탈 사용자 중 모델이 탐지한 비율 |
| F1 Score | Precision과 Recall의 조화 평균 |
| ROC-AUC | 전체 분류 성능 |
| PR-AUC | 불균형 데이터 환경에서 이탈 클래스 탐지 성능 |

또한 Confusion Matrix를 활용해 모델의 예측 결과를 분석합니다.

---

# 🖥 Dashboard

분석 및 예측 결과는 웹 대시보드를 통해 제공합니다.

### 주요 기능

**Overview**

전체 사용자 현황과 핵심 지표를 확인합니다.

- 전체 분석 사용자
- 활동 사용자
- 이탈 위험 사용자
- 평균 위험도
- 사용자 행동 통계

**Risk Users**

모델이 예측한 위험 사용자를 확인합니다.

- 위험 사용자 목록
- 위험도
- 이탈 확률
- 사용자 검색
- 조건별 필터
- 게임 모드 선택

**User Detail**

특정 사용자의 경기 활동 패턴을 상세하게 확인합니다.

- 사용자 기본 정보
- 최근 경기 기록
- 게임 플레이 빈도
- 승률
- KDA
- 활동 변화
- 이탈 위험도

**Model Analysis**

머신러닝 모델의 성능을 확인합니다.

- Precision
- Recall
- F1 Score
- ROC-AUC
- PR-AUC
- Confusion Matrix
- Feature Importance

---

# 🛠 Tech Stack

## Data

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)

## Machine Learning

![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-FF6600?style=flat-square)
![LightGBM](https://img.shields.io/badge/LightGBM-02569B?style=flat-square)

## Backend

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)

## Frontend

![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

## Collaboration

![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)

---

# 📂 Project Structure

```text
project/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   └── requirements.txt
│
├── data_collection/
│   ├── seed_users/
│   ├── match_ids/
│   └── match_detail/
│
├── data_analysis/
│   ├── preprocessing/
│   ├── eda/
│   └── feature_engineering/
│
├── churn_model/
│   ├── training/
│   ├── evaluation/
│   └── models/
│
├── data/
│   ├── processed/
│   └── sample/
│
├── docs/
│
├── .gitignore
├── .env.example
└── README.md
```

---

# 🚀 Installation

## 1. Repository Clone

SSH를 사용하는 경우:

```bash
git clone git@github.com:USERNAME/REPOSITORY.git
```

프로젝트 폴더로 이동합니다.

```bash
cd REPOSITORY
```

---

# ⚙️ Backend

Backend 폴더로 이동합니다.

```bash
cd backend
```

가상환경을 생성합니다.

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

FastAPI 서버를 실행합니다.

```bash
uvicorn main:app --reload
```

기본 서버 주소:

```text
http://127.0.0.1:8000
```

Swagger API 문서:

```text
http://127.0.0.1:8000/docs
```

---

# 🌐 Frontend

새 터미널에서 Frontend 폴더로 이동합니다.

```bash
cd frontend
```

패키지를 설치합니다.

```bash
npm install
```

개발 서버를 실행합니다.

```bash
npm run dev
```

기본 접속 주소:

```text
http://localhost:5173
```

---

# 🔑 Environment Variables

Riot API Key와 같은 민감 정보는 GitHub에 업로드하지 않습니다.

`.env`

```env
RIOT_API_KEY=YOUR_RIOT_API_KEY
```

Repository에는 실제 `.env` 대신 `.env.example`만 포함합니다.

```env
RIOT_API_KEY=
```

`.gitignore`

```gitignore
.env
**/.env
```

---

# 🌿 Git Branch Strategy

본 프로젝트는 기능별 개발을 위해 다음과 같은 Branch 구조를 사용했습니다.

```text
main
│
└── develop
    │
    ├── feature/data-collection
    │
    ├── feature/data-analysis
    │
    ├── feature/churn-model
    │
    └── feature/dashboard
```

### `main`

최종 배포 및 발표용 코드

### `develop`

팀 개발 내용을 통합하는 Branch

### `feature/data-collection`

Riot API 데이터 수집

### `feature/data-analysis`

EDA / 데이터 전처리 / Feature Engineering

### `feature/churn-model`

이탈 예측 모델 개발 및 평가

### `feature/dashboard`

React / FastAPI 웹 서비스 개발

---

# 🔄 Git Workflow

개발 Branch 이동:

```bash
git switch develop
```

최신 코드 가져오기:

```bash
git pull origin develop
```

작업 후 변경 파일 확인:

```bash
git status
```

변경 사항 추가:

```bash
git add .
```

Commit:

```bash
git commit -m "feat: 작업 내용"
```

GitHub에 Push:

```bash
git push origin develop
```

최종적으로 `develop`의 검증된 코드를 `main`에 반영합니다.

```text
feature/*
    ↓
 develop
    ↓
  main
```

---

# ⚠️ GitHub Upload Policy

다음 파일은 GitHub에 업로드하지 않습니다.

```text
.venv/
venv/
node_modules/
__pycache__/
.pytest_cache/
.env
*.db
*.sqlite
*.sqlite3
*.parquet
frontend/dist/
lol_churn_all_data/
```

특히 다음 정보가 포함된 파일은 반드시 제외합니다.

- Riot API Key
- 개인 API Token
- 대용량 Raw Dataset
- Local Database
- 가상환경
- Node.js 패키지

---

# 👥 Team

**SK Networks Family AI Camp 36기**  
**2nd Project · Team 4**

| Role | Responsibility |
|---|---|
| Data Collection | Riot API 기반 사용자 및 경기 데이터 수집 |
| Data Analysis | EDA / 전처리 / Feature Engineering |
| Modeling | 사용자 이탈 예측 모델 개발 |
| Dashboard | React / FastAPI 웹 서비스 구현 |

---

# 🔮 Expected Value

본 프로젝트는 단순히 사용자의 현재 상태를 보여주는 것에서 끝나지 않고,

```text
현재 사용자 행동
        ↓
행동 변화 탐지
        ↓
이탈 위험 예측
        ↓
위험 사용자 식별
        ↓
선제적 사용자 관리
```

와 같은 흐름을 구현하는 것을 목표로 합니다.

이를 통해 게임 서비스 운영자가 **사용자가 실제로 이탈하기 전에 위험 신호를 파악할 수 있는 분석 환경**을 제시합니다.

---

# 📎 Notes

본 프로젝트는 교육 및 데이터 분석 프로젝트 목적으로 제작되었습니다.

League of Legends 및 Riot Games 관련 데이터는 Riot Games API를 기반으로 수집하며,  
본 프로젝트는 Riot Games의 공식 서비스가 아닙니다.
