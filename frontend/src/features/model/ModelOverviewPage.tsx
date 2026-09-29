import { useMemo } from 'react'
import type { EChartsCoreOption } from 'echarts/core'
import { EChart } from '../../components/common/EChart'

const modelRows = [
  { name: 'CatBoost · 무처리(기준 모델)', prAuc: '0.397', rocAuc: '0.783', recall10: '32.5%', f1_10: '0.392', recall20: '52.1%', f1_20: '0.450', found: '189 / 오탐 288', status: '현재 기준' },
  { name: 'CatBoost · 클래스 가중치 2', prAuc: '0.402', rocAuc: '0.784', recall10: '31.7%', f1_10: '0.382', recall20: '51.5%', f1_20: '0.445', found: '187 / 오탐 290', status: '비교' },
  { name: 'CatBoost · 균형 가중치', prAuc: '0.402', rocAuc: '0.778', recall10: '33.1%', f1_10: '0.399', recall20: '51.0%', f1_20: '0.440', found: '185 / 오탐 292', status: '비교' },
  { name: 'CatBoost · ROS', prAuc: '0.396', rocAuc: '0.774', recall10: '33.3%', f1_10: '0.402', recall20: '50.4%', f1_20: '0.436', found: '183 / 오탐 294', status: '비교' },
  { name: 'CatBoost · SMOTE', prAuc: '0.392', rocAuc: '0.771', recall10: '31.1%', f1_10: '0.375', recall20: '47.7%', f1_20: '0.412', found: '173 / 오탐 304', status: '비교' },
]

function createModelComparisonOption(): EChartsCoreOption {
  return {
    grid: { top: 34, right: 18, bottom: 42, left: 48 },
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { color: '#9fb4cf' } },
    xAxis: {
      type: 'category',
      data: ['CatBoost', '가중치 2', '균형 가중치', 'ROS', 'SMOTE'],
      axisLabel: { color: '#91a7c3' },
      axisLine: { lineStyle: { color: '#35506f' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 0.5,
      axisLabel: { color: '#91a7c3' },
      splitLine: { lineStyle: { color: 'rgba(84, 120, 164, .18)' } },
    },
    series: [
      { name: 'PR-AUC', type: 'bar', data: [0.397, 0.402, 0.402, 0.396, 0.392], itemStyle: { color: '#3d8dff', borderRadius: [5, 5, 0, 0] } },
      { name: 'F1@20%', type: 'bar', data: [0.45, 0.445, 0.44, 0.436, 0.412], itemStyle: { color: '#55d8ff', borderRadius: [5, 5, 0, 0] } },
    ],
  }
}

function createFeatureImportanceOption(): EChartsCoreOption {
  return {
    grid: { top: 10, right: 32, bottom: 24, left: 128 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'value',
      max: 0.65,
      axisLabel: { color: '#91a7c3' },
      splitLine: { lineStyle: { color: 'rgba(84, 120, 164, .18)' } },
    },
    yAxis: {
      type: 'category',
      data: ['최근 승률 변화', '평균 경기 간격', '최근 30일 경기 수', '최근 7일 경기 수', '마지막 경기 경과일'],
      axisLabel: { color: '#c5d6ea' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: [0.051, 0.038, 0.088, 0.196, 0.587],
      barWidth: 15,
      itemStyle: { color: '#5a9aff', borderRadius: [0, 6, 6, 0] },
      label: { show: true, position: 'right', color: '#d8e7f8' },
    }],
  }
}

export function ModelOverviewPage() {
  const comparisonOption = useMemo(() => createModelComparisonOption(), [])
  const importanceOption = useMemo(() => createFeatureImportanceOption(), [])

  return (
    <>
      <header className="page-header">
        <div>
          <h1>모델 설명</h1>
          <p className="page-description">CatBoost 기준 모델과 불균형 처리 실험, 별도 시계열·생존분석 결과를 확인합니다.</p>
        </div>
        <div className="header-badges">
          <span className="demo-badge">실험 기록</span>
          <span className="status-badge ready">● CatBoost 선정</span>
        </div>
      </header>

      <section className="demo-notice">
        <strong>현재 기준 모델 · CatBoost 무가중치</strong>
        2,381명에 대한 5-fold OOF 결과입니다. 상위 20% 검토 대상 477명 중 189명이 실제 30일 무경기 사용자였습니다.
      </section>

      <section className="metric-grid four" aria-label="모델 핵심 성능 지표">
        <article className="metric-card"><span>PR-AUC</span><strong>0.397</strong><small>불균형 데이터 핵심 지표</small></article>
        <article className="metric-card"><span>ROC-AUC</span><strong>0.783</strong><small>전체 순위 분리 성능</small></article>
        <article className="metric-card"><span>Recall@20%</span><strong>52.1%</strong><small>조치 대상 상위 20%</small></article>
        <article className="metric-card"><span>F1@20%</span><strong>0.450</strong><small>Precision·Recall 균형</small></article>
      </section>

      <section className="content-grid">
        <article className="panel span-7">
          <div className="panel-title"><h2>모델 비교</h2><span className="panel-chip">실험 결과</span></div>
          <EChart option={comparisonOption} ariaLabel="CatBoost 불균형 처리별 PR-AUC와 상위 20퍼센트 F1 비교 막대그래프" />
          <p className="panel-footnote">같은 진성 활동 고객 코호트의 결과입니다. 무가중치 기준 행은 현재 목록에 점수로 쓰는 기준 모델이고, 가중치·ROS·SMOTE 비교는 결측치 중앙값 대체를 적용한 별도 재실험입니다.</p>
        </article>

        <article className="panel span-5">
          <div className="panel-title"><h2>캠페인 기준 성능</h2><span className="panel-chip">CatBoost OOF</span></div>
          <div className="risk-method-grid compact-method">
            <div><b>상위 10%</b><strong>239명 검토</strong><p>Recall 32.5%<br />Precision 49.4%<br />F1 0.392</p></div>
            <div><b>상위 20%</b><strong>477명 검토</strong><p>Recall 52.1%<br />Precision 39.6%<br />F1 0.450</p></div>
          </div>
          <p className="panel-footnote">고비용 보상은 상위 10%, 저비용 알림과 콘텐츠 추천은 상위 20%를 검토합니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>이전 전체 사용자 실험의 주요 변수</h2><span className="panel-chip">SHAP · 별도 코호트</span></div>
          <EChart option={importanceOption} ariaLabel="CatBoost 주요 변수 중요도 막대그래프" />
          <p className="panel-footnote">이 SHAP 결과는 기존 전체 활동 사용자 CatBoost 실험에서 계산되어 현재 2,381명 모델을 설명하는 값이 아닙니다. 점수는 예측 기여 크기이며 원인이나 인과 효과를 뜻하지 않습니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>모델 비교표</h2></div>
          <div className="table-scroll">
            <table className="data-table">
              <thead><tr><th>학습 처리</th><th>PR-AUC</th><th>ROC-AUC</th><th>Recall@10%</th><th>F1@10%</th><th>Recall@20%</th><th>F1@20%</th><th>20% 발견/오탐</th></tr></thead>
              <tbody>
                {modelRows.map((model) => (
                  <tr key={model.name}>
                    <td>{model.name}</td><td>{model.prAuc}</td><td>{model.rocAuc}</td><td>{model.recall10}</td><td>{model.f1_10}</td><td>{model.recall20}</td><td>{model.f1_20}</td><td>{model.found}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="panel-footnote">2,381명 중 30일 무경기 363명. ROS는 소수 클래스 단순 복제, SMOTE는 합성 보간이며 두 방식 모두 학습 fold에만 적용했습니다. 재실험에서는 ROS의 상위 10% F1이 높았지만, 상위 20%와 PR-AUC는 기준 모델과 비슷하거나 낮아 교체하지 않았습니다.</p>
        </article>

        <article className="panel span-12">
          <div className="panel-title"><h2>별도 분석 실험 기록</h2><span className="panel-chip">다른 목적·다른 코호트</span></div>
          <div className="table-scroll"><table className="data-table"><thead><tr><th>실험</th><th>대상·목표</th><th>주요 결과</th><th>판단</th></tr></thead><tbody>
            <tr><td>CatBoost · SHAP 상위 15개</td><td>이전 활동 사용자 7,806명 · churn</td><td>PR-AUC 0.364, Recall@20% 66.1%, F1@20% 0.413</td><td>현재 2,381명 기준과 직접 비교 불가</td></tr>
            <tr><td>CatBoost 소규모 튜닝</td><td>같은 이전 코호트 · 3-fold, 5개 설정</td><td>깊이 4에서 Recall@20% 67.5%, F1@20% 0.422</td><td>작은 개선·선택 편향 가능성으로 채택 보류</td></tr>
            <tr><td>부스팅 3종 비교</td><td>이전 코호트 · CatBoost/XGBoost/LightGBM</td><td>18개 조합을 5-fold로 비교</td><td>현 진성 고객 모델은 CatBoost로 별도 재평가</td></tr>
            <tr><td>Transformer churn</td><td>이전 활동 사용자 · churn 분류</td><td>개선 실험 PR-AUC 0.363, ROC-AUC 0.857, Recall@20% 66.1%</td><td>CatBoost와 목적은 같고 현재 표본 성능은 별도 검증 전</td></tr>
            <tr><td>Transformer 다음 행동</td><td>시간순 경기 로그 · 다음 모드/경기 간격</td><td>모드 정확도 90.3% 대 직전 모드 기준선 90.9%; 간격 MAE 1.09일 대 0.99일</td><td>단순 기준선보다 낮아 보류</td></tr>
            <tr><td>Cox 생존분석</td><td>2,381명 피처 기반 합성 시간·이벤트 라벨</td><td>C-index 0.762</td><td>합성 검증치일 뿐 실제 생존 예측 성능 아님</td></tr>
          </tbody></table></div>
          <p className="panel-footnote">과거 실험은 당시 코호트·목표를 함께 표시했습니다. 특히 7,806명 churn 실험 결과를 현재 2,381명 모델 성능처럼 해석하지 않습니다.</p>
        </article>

        <article className="panel span-12 insight-panel">
          <div className="panel-title"><h2>해석 시 주의사항</h2></div>
          <div className="insight-list">
            <p><b>01</b><span>위험 점수는 확률 보정값이 아닌 고객 우선순위 점수입니다. 라벨은 기준일 이후 30일 무경기 여부이며 계정 탈퇴를 뜻하지 않습니다.</span></p>
            <p><b>02</b><span>중요 변수는 예측에 기여한 관측값이며, 사용자가 이탈한 원인을 확정하는 인과관계가 아닙니다.</span></p>
            <p><b>03</b><span>단일 기준일 OOF 결과이며, 다른 기간 데이터의 시간 외 검증과 캠페인 A/B 테스트는 아직 필요합니다.</span></p>
          </div>
        </article>
      </section>
    </>
  )
}
