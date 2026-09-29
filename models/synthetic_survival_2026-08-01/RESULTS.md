# Synthetic Survival Model Demo

이 폴더의 결과는 실제 장기 관찰 정답이 아니라, 진성 활동 고객 2,381명의 feature 분포를 바탕으로 만든 **합성 생존분석 데모**입니다.

## 목적

- CatBoost: 기준일 이후 30일 이탈 위험 고객을 고르는 모델
- Synthetic survival model: 위험 고객에게 **언제 개입할지**를 설명하는 발표용 확장 실험

## 합성 데이터 정의

| 항목 | 값 |
|---|---:|
| 기준일 | 2026-08-01 |
| 합성 사용자 수 | 2,381 |
| 실제 core churn 비율 | 15.2% |
| 합성 30일 event 비율 | 15.2% |
| 합성 관찰 event 비율 | 41.9% |
| 합성 관찰 최대일 | 179.9 |

합성 event는 `30일 무경기 상태에 도달`로 해석했습니다. 실제 경기 로그에서 확인한 값이 아니라 `days_since_last_game`, `avg_gap_30d`, `games_30d`, `activity_trend`, `losing_streak`, KDA 등으로 위험도를 만든 뒤 시뮬레이션했습니다.

## 모델 결과

| 모델 | 평가 |
|---|---:|
| Cox Proportional Hazards | Concordance index 0.762 |

Concordance index는 생존분석의 순위 지표입니다. 1에 가까울수록 더 이른 event가 발생한 사용자를 더 위험하게 정렬했다는 뜻입니다.

## 영향이 큰 합성 요인

| 변수 | Cox 계수 | Hazard ratio |
|---|---:|---:|
| `play_style_insufficient_recent_games` | 0.462 | 1.59 |
| `days_since_last_game` | 0.313 | 1.37 |
| `active_days_30d` | -0.279 | 0.76 |
| `activity_trend_roughly_stable` | -0.247 | 0.78 |
| `games_30d` | -0.172 | 0.84 |
| `avg_gap_30d` | 0.128 | 1.14 |
| `activity_trend_activity_growing` | -0.126 | 0.88 |
| `losing_streak` | 0.125 | 1.13 |

## 사용 방법

- `synthetic_survival_core_2026-08-01.csv`: 합성 생존분석 학습 데이터
- `survival_predictions.csv`: 테스트 사용자별 7/14/30/60/90일 생존확률
- `survival_curves.png`: 발표용 생존곡선 이미지
- `cox_coefficients.csv`: Cox 계수와 hazard ratio

## 한계

이 결과는 CatBoost 실제 이탈 예측 성능과 비교하면 안 됩니다. 실제 장기 관찰 로그가 없어서 event time과 censoring을 인위적으로 만들었기 때문입니다. 보고서에서는 `생존분석을 적용하면 어떤 질문에 답할 수 있는지`를 보여주는 데 사용하세요.
