import { useEffect, useMemo, useState } from 'react'
import type { EChartsCoreOption } from 'echarts/core'
import { dashboardApi } from '../../api/client'
import type { CandidateModelRow, ModelMetricsResponse } from '../../api/types'
import { EChart } from '../../components/common/EChart'
import { MetricCard } from '../../components/common/MetricCard'
import { PageHeader } from '../../components/common/PageHeader'
import { modelMetricsFallback } from '../../data/modelMetricsFallback'

const featureNames: Record<string, string> = {
  days_since_last_game: '마지막 경기 경과일',
  games_7d: '최근 7일 경기 수',
  active_days_30d: '최근 30일 활동일',
  mode_switch_rate_20: '최근 모드 전환율',
  winrate_change_10: '최근 승률 변화',
  last_gap: '마지막 경기 간격',
  avg_cs_per_min_20: '평균 분당 CS',
  max_gap_30d: '최근 최대 경기 간격',
  avg_vision_per_min_20: '평균 분당 시야',
  avg_kda_20: '최근 평균 KDA',
}

const treatments: Record<string, string> = {
  none: '무처리',
  class_weight_2: '가중치 2',
  class_weight_balanced: '균형 가중치',
  ros: 'ROS',
  smote: 'SMOTE',
}

const sets: Record<string, string> = {
  aggregate33: '기존 집계 33개',
  engineered40: '파생 포함 40개',
  shap15: 'SHAP 상위 15개',
}

const pct = (value: string | number) => `${(Number(value) * 100).toFixed(1)}%`
const candidateName = (row: CandidateModelRow) => `${sets[row.feature_set] ?? row.feature_set} · ${treatments[row.treatment] ?? row.treatment}`

function horizontalBar(labels: string[], values: number[], color: string, max?: number): EChartsCoreOption {
  return {
    grid: { top: 10, right: 54, bottom: 24, left: 166 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'value',
      max,
      axisLabel: { color: '#91a7c3', fontSize: 9 },
      splitLine: { lineStyle: { color: 'rgba(84, 120, 164, .16)' } },
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#c5d6ea', width: 155, overflow: 'truncate', fontSize: 9 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: values,
      barWidth: 15,
      itemStyle: { color, borderRadius: [0, 6, 6, 0] },
      label: {
        show: true,
        position: 'right',
        color: '#d8e7f8',
        fontSize: 9,
        formatter: ({ value }: { value: unknown }) => Number(value).toFixed(3),
      },
    }],
  }
}

function modelComparisonChart(rows: NonNullable<ModelMetricsResponse['details']>['boosting_comparison']): EChartsCoreOption {
  return {
    grid: { top: 18, right: 22, bottom: 36, left: 48 },
    tooltip: { trigger: 'axis' },
    legend: { top: 0, right: 0, textStyle: { color: '#9fb4cf', fontSize: 9 } },
    xAxis: {
      type: 'category',
      data: rows.map((row) => row.model),
      axisLabel: { color: '#a7bdd7', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(105,145,191,.28)' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0.3,
      max: 0.85,
      axisLabel: { color: '#7189a7', fontSize: 9 },
      splitLine: { lineStyle: { color: 'rgba(105,145,191,.12)' } },
    },
    series: [
      {
        name: 'PR-AUC',
        type: 'bar',
        data: rows.map((row) => Number(row.pr_auc_ap)),
        barMaxWidth: 28,
        itemStyle: { color: '#55d8ff', borderRadius: [5, 5, 0, 0] },
      },
      {
        name: 'ROC-AUC',
        type: 'bar',
        data: rows.map((row) => Number(row.roc_auc)),
        barMaxWidth: 28,
        itemStyle: { color: '#f4bd5e', borderRadius: [5, 5, 0, 0] },
      },
    ],
  }
}

export function ModelOverviewPage() {
  // 모델 성능 페이지는 첫 렌더부터 커밋된 평가 스냅샷을 보여준다.
  // API 응답이 오면 최신 값을 덮어쓰되, API 오류/누락으로 페이지 전체가 사라지지 않는다.
  const [data, setData] = useState<ModelMetricsResponse>(modelMetricsFallback)

  useEffect(() => {
    void dashboardApi.getModelMetrics().then((response) => {
      if (response.details) setData(response)
    }).catch(() => {
      // modelMetricsFallback을 그대로 유지한다.
    })
  }, [])

  const details = data.details ?? modelMetricsFallback.details!
  const candidateChart = useMemo(() => {
    const rows = (details?.candidates ?? []).slice(0, 5).reverse()
    return horizontalBar(rows.map(candidateName), rows.map((row) => Number(row.ap)), '#5a9aff', 0.45)
  }, [details])

  const shapChart = useMemo(() => {
    const rows = (details?.selected_model_shap ?? []).slice(0, 8).reverse()
    return horizontalBar(
      rows.map((row) => featureNames[row.feature] ?? row.feature),
      rows.map((row) => Number(row.mean_abs_shap)),
      '#55d8ff',
    )
  }, [details])

  const compareChart = useMemo(
    () => modelComparisonChart(details?.boosting_comparison ?? []),
    [details],
  )


  const nested = details.nested_selection_oof.all_core
  const candidate = details.selected_candidate_oof_exploratory.all_core
  const chosen = `${sets[details.selected_candidate.feature_set] ?? details.selected_candidate.feature_set} · ${treatments[details.selected_candidate.treatment] ?? details.selected_candidate.treatment}`

  const actualActive = nested.users - nested.churners
  const tp = nested.top_20pct.found_churn
  const fp = nested.top_20pct.false_alarms
  const fn = nested.churners - tp
  const tn = actualActive - fp
  const tnRate = actualActive ? tn / actualActive : 0
  const fpRate = actualActive ? fp / actualActive : 0
  const fnRate = nested.churners ? fn / nested.churners : 0
  const tpRate = nested.churners ? tp / nested.churners : 0

  return (
    <>
      <PageHeader
        className="model-page-header"
        title="모델 성능"
        description={`진성 활동 고객 ${nested.users.toLocaleString()}명 기준 · CatBoost 이탈 위험 모델 검증 결과입니다.`}
        badges={(
          <>
            <span className="demo-badge">5-FOLD OOF</span>
            <span className="status-badge ready">CATBOOST</span>
          </>
        )}
      />

      <section className="model-validation-strip" aria-label="모델 검증 기준">
        <div><span>분석 대상</span><strong>{nested.users.toLocaleString()}명</strong><small>진성 활동 고객</small></div>
        <div><span>실제 무경기</span><strong>{nested.churners.toLocaleString()}명</strong><small>{pct(nested.prevalence)}</small></div>
        <div><span>선택 모델</span><strong>{chosen}</strong><small>후보 탐색 결과</small></div>
        <div><span>평가 방식</span><strong>Nested 5-Fold CV</strong><small>후보 선택 과정 포함</small></div>
      </section>

      <section className="metric-grid four model-metric-grid" aria-label="모델 핵심 성능">
        <MetricCard label="PR-AUC" value={nested.pr_auc_ap.toFixed(3)} detail="불균형 데이터 핵심 지표" />
        <MetricCard label="ROC-AUC" value={nested.roc_auc.toFixed(3)} detail="전체 순위 분리 성능" />
        <MetricCard label="Recall @ 상위 20%" value={pct(nested.top_20pct.recall)} detail={`실제 이탈 ${tp} / ${nested.churners}명 탐지`} warning />
        <MetricCard label="F1 @ 상위 20%" value={nested.top_20pct.f1.toFixed(3)} detail={`Precision ${pct(nested.top_20pct.precision)}`} />
      </section>

      <section className="content-grid model-performance-grid">
        <article className="panel span-6 model-confusion-panel">
          <div className="panel-title"><h2>상위 20% 기준 혼동행렬</h2><span className="panel-chip">비율 + 인원</span></div>
          <p className="model-panel-lead">실제 클래스별 비율로 표시합니다. 행 기준 합계가 100%입니다.</p>
          <div className="model-confusion-matrix" role="img" aria-label="상위 20퍼센트 위험군 기준 비율 혼동행렬">
            <div className="model-matrix-corner"></div>
            <div className="model-matrix-axis">예측 일반</div>
            <div className="model-matrix-axis">예측 위험</div>
            <div className="model-matrix-axis row">실제 일반</div>
            <div className="model-matrix-cell good"><strong>{pct(tnRate)}</strong><span>TN · {tn.toLocaleString()}명</span></div>
            <div className="model-matrix-cell warn"><strong>{pct(fpRate)}</strong><span>FP · {fp.toLocaleString()}명</span></div>
            <div className="model-matrix-axis row">실제 이탈</div>
            <div className="model-matrix-cell danger-soft"><strong>{pct(fnRate)}</strong><span>FN · {fn.toLocaleString()}명</span></div>
            <div className="model-matrix-cell danger"><strong>{pct(tpRate)}</strong><span>TP · {tp.toLocaleString()}명</span></div>
          </div>
          <p className="panel-footnote">상위 20%인 {nested.top_20pct.selected.toLocaleString()}명을 위험군으로 잡았을 때 실제 무경기 고객의 {pct(tpRate)}를 탐지합니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>부스팅 모델 3종 비교</h2><span className="panel-chip">동일 5-Fold OOF</span></div>
          <EChart option={compareChart} ariaLabel="CatBoost XGBoost LightGBM PR-AUC ROC-AUC 비교" />
          <div className="model-mini-table">
            {details.boosting_comparison.map((row) => (
              <div key={row.model}>
                <strong>{row.model}</strong>
                <span>PR-AUC {Number(row.pr_auc_ap).toFixed(3)}</span>
                <span>Recall@20 {pct(row.recall_20)}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>후보별 PR-AUC</h2><span className="panel-chip">상위 5개</span></div>
          <EChart option={candidateChart} ariaLabel="모델 후보별 PR-AUC 비교" />
          <p className="panel-footnote">선택 후보 OOF PR-AUC는 {candidate.pr_auc_ap.toFixed(3)}입니다. 같은 데이터에서 후보를 고른 값이므로 최종 성능으로 단정하지 않습니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>주요 영향 변수</h2><span className="panel-chip">SHAP 중요도</span></div>
          <EChart option={shapChart} ariaLabel="CatBoost 주요 변수 SHAP 중요도" />
          <p className="panel-footnote">평균 절댓값 SHAP 기준입니다. 중요도는 예측에 미친 영향 크기이며 이탈의 원인이나 개입 효과를 의미하지 않습니다.</p>
        </article>

        <article className="panel span-12 model-evaluation-panel">
          <div className="panel-title"><h2>평가 기준 한눈에 보기</h2><span className="panel-chip">발표용 요약</span></div>
          <div className="model-evaluation-grid">
            <div><b>01</b><strong>라벨</strong><p>기준일 이후 30일 동안 경기 0회면 이탈로 정의합니다.</p></div>
            <div><b>02</b><strong>검증</strong><p>후보 선택까지 포함한 Nested 5-Fold CV를 대표 성능으로 사용합니다.</p></div>
            <div><b>03</b><strong>운영 기준</strong><p>위험 점수 상위 20%를 우선 검토 대상으로 두고 Recall과 Precision을 함께 확인합니다.</p></div>
            <div><b>04</b><strong>주의</strong><p>점수는 보정된 이탈 확률이 아니며 별도 미래 시점 검증이 필요합니다.</p></div>
          </div>
        </article>

        <article className="panel span-12">
          <div className="panel-title"><h2>모델별 상세 지표</h2><span className="panel-chip">동일 코호트 · 동일 분할</span></div>
          <div className="table-scroll">
            <table className="data-table model-score-table">
              <thead><tr><th>모델</th><th>PR-AUC</th><th>ROC-AUC</th><th>Recall@10%</th><th>Precision@10%</th><th>Recall@20%</th><th>Precision@20%</th><th>F1@20%</th><th>20% 탐지 / 오탐</th></tr></thead>
              <tbody>{details.boosting_comparison.map((row) => (
                <tr key={row.model}>
                  <td><strong>{row.model}</strong></td>
                  <td>{Number(row.pr_auc_ap).toFixed(3)}</td>
                  <td>{Number(row.roc_auc).toFixed(3)}</td>
                  <td>{pct(row.recall_10)}</td>
                  <td>{pct(row.precision_10)}</td>
                  <td>{pct(row.recall_20)}</td>
                  <td>{pct(row.precision_20)}</td>
                  <td>{Number(row.f1_20).toFixed(3)}</td>
                  <td>{row.found_20} / {row.false_alarms_20}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <p className="panel-footnote">세 모델 모두 동일한 진성 활동 고객 {nested.users.toLocaleString()}명, 같은 5-fold 분할을 사용한 탐색 비교입니다.</p>
        </article>
      </section>
    </>
  )
}
