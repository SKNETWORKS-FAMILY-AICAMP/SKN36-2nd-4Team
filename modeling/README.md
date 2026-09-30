# 이탈 모델 및 실험

이 브랜치에는 고객 이탈 분류, 불균형 처리 비교, 생존분석 실험과 집계 결과를 둡니다. EDA·전처리·DB 구성 코드는 `feature/data-analysis`, 화면 코드는 `feature/dashboard`에 있습니다.

## 실행

모델 학습을 재현하려면 `lol_churn_all_data/`를 별도로 받아 저장소 루트에 둔 뒤 `feature/data-analysis`와 이 브랜치의 코드를 통합해야 합니다. 이미 학습된 요약 결과와 CatBoost 모델 파일은 `models/`에 포함되어 있습니다. 사용자별 OOF 점수와 원천 데이터는 공개 저장소에서 제외합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/modeling.txt
python -m modeling.train_core_churn
python -m modeling.compare_core_imbalance
python -m modeling.train_synthetic_survival
```

합성 생존분석은 가정한 이벤트 자료로 진행한 데모입니다. 실제 고객의 관찰 생존율이나 검증된 이탈 예측 성능으로 해석하지 않습니다. Transformer 분류 실험은 CatBoost와 비교한 결과 보고서에 기록했으며, 이탈 분류 기준 모델로 채택하지 않았습니다.
