# 부스팅 모델 5-fold 비교 (2026-08-01 기준)

> 과거 실험 기록입니다. 저장 모델과 재실행 스크립트는 제거했으며 새 대상군에 대한 성능으로 사용하지 않습니다.

이 비교는 기존 CatBoost 실험의 **train+validation 사용자 8,397명**만 사용했습니다. 기존 test 1,482명은 이번 모델 비교·선택에 사용하지 않았습니다. 각 fold의 학습 데이터에서 CatBoost SHAP을 계산해 상위 15개 피처를 새로 선정했으므로, 해당 fold의 검증 정답이 피처 선택에 들어가지 않습니다. 완전히 중복된 `actual_history_matches`는 먼저 제외했습니다.

CatBoost, XGBoost, LightGBM을 전체 33개 피처와 SHAP 상위 15개 피처, 클래스 가중치 미적용/적용으로 비교했습니다. 이탈 비율은 약 13%입니다. 각 모델의 설정은 고정한 소규모 첫 비교로, 대규모 하이퍼파라미터 탐색은 하지 않았습니다.

| 모델 | 피처 | 클래스 가중치 | 평균 PR-AUC (AP) | 평균 ROC-AUC | 상위 10% 이탈자 발견율 |
|---|---:|---|---:|---:|---:|
| XGBoost | SHAP 상위 15개 | 적용 | **0.5438** | 0.8797 | 45.8% |
| LightGBM | SHAP 상위 15개 | 적용 | 0.5429 | 0.8780 | 45.6% |
| CatBoost | 전체 33개 | 미적용 | 0.5369 | **0.8850** | **46.0%** |
| CatBoost | SHAP 상위 15개 | 미적용 | 0.5364 | 0.8848 | 45.5% |

평균 PR-AUC가 가장 높은 XGBoost·SHAP 15개·가중치 적용 조합을 개발 데이터 전체로 다시 학습하여 `selected_model.json`에 저장했습니다. 정확한 입력 피처와 순서는 `manifest.json`을 확인하세요. 하지만 XGBoost와 LightGBM의 PR-AUC 차이는 0.001 미만이고, CatBoost와의 차이도 0.007 정도로 fold 간 변동(표준편차 약 0.026~0.030)보다 작습니다. **따라서 우월성이 입증된 모델이라고 해석하면 안 됩니다.** CatBoost는 ROC-AUC와 상위 10% 발견율에서 오히려 조금 높습니다.

SHAP 상위 15개에 5개 fold 모두 포함된 피처는 `days_since_last_game`, `games_7d`, `games_30d`, `games_90d`, `active_days_30d`, `activity_change_30d`, `avg_gap_30d`, `max_gap_30d`, `unique_modes_30d`, `mode_switch_rate_20`, `winrate_change_10`입니다. SHAP은 모델 의존도를 설명할 뿐 이탈의 원인을 증명하지 않습니다.

이번 5-fold는 동일한 cutoff 안에서 사용자만 다시 나눈 검증입니다. **미래 날짜로 일반화되는지**는 확인하지 못합니다. 이전 CatBoost 실험에서 기존 test 결과를 이미 확인했으므로, 이 실험에서 그 test를 반복 평가해 최종 성능이라고 주장하지 않았습니다. 다른 cutoff 또는 새 수집 사용자로 최종 평가해야 합니다. 특히 클래스 가중치를 적용한 모델의 출력은 별도 보정 없이 실제 이탈 확률이라고 해석하지 마세요.

- `cv_summary.csv`: 12개 조합의 5-fold 평균·표준편차
- `cv_fold_results.csv`: 조합별 fold 결과
- `shap_selection_frequency.csv`: 피처가 상위 15개에 포함된 fold 수
- `manifest.json`: 선택 조합, 입력 피처 순서 및 라이브러리 버전
- `selected_model.json`: 제거됨. `manifest.json`은 당시 선택 설정의 기록만 보존

비교 스크립트는 정리되어 현재 저장소에서 이 실험을 그대로 재실행할 수 없습니다.
