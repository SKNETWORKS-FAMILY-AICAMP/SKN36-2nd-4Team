# LoL Churn Intelligence React Dashboard

진성 활동 고객(`games_prev30d >= 4`, `games_30d > 0`)을 대상으로 만든 운영 화면 목업입니다.

## 포함 화면

- Overview: 배치 현황, KPI, CatBoost 성능, 조치 규모 비교
- Campaign Planner: 상위 10% / 20% 조치 범위와 Recall·Precision 비교
- Segment Analysis: 솔로랭크·활동 감소 등 고객군별 관측 이탈률
- Risk Customers: 위험 점수 순위, 필터, 권장 액션
- Customer Detail: 선택 고객의 점수와 행동 변화 근거
- Timing Simulation: synthetic survival 기반 7/14/30일 데모
- Model Lab: CatBoost, class weight, ROS, SMOTE, Transformer, Survival 실험 기록

현재 `src/main.jsx`의 상단 상수는 모델 산출물의 요약값을 화면에 표시합니다. 백엔드 API를 붙일 때는 이 상수만 API 응답으로 교체하면 됩니다.

## 실행

PowerShell에서:

```powershell
cd C:\dev\project\lol_churn\react-dashboard
npm install
npm run dev
```

현재 환경에는 `npm`이 없으므로, Node.js 설치 후 실행하세요. UI 담당자는 `src/styles.css`를 중심으로 색상과 레이아웃을 수정하면 됩니다.

## 운영 데이터 주의

- 위험 점수는 확률로 보정된 값이 아니라 모델의 순위 점수입니다.
- churn은 계정 탈퇴가 아니라 기준일 이후 30일 동안 경기 기록이 없는 상태입니다.
- Survival 화면은 합성 라벨을 사용한 데모이므로 실제 정책 판단에 사용하지 않습니다.
