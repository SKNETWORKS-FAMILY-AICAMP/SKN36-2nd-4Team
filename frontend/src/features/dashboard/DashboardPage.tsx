import { useCallback, useEffect, useMemo, useState } from 'react'
import { dashboardApi } from '../../api/client'
import type { SummaryResponse } from '../../api/types'
import { EChart } from '../../components/common/EChart'
import {
  ACTIVITY_HEATMAP_LAYOUT,
  createActivityHeatmapOption,
  createChurnRateBarOption,
} from './chartOptions'
import { KpiCard } from './components/KpiCard'

function formatPercent(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`
}

const GAME_MODES = [
  { value: 'ALL', label: '전체' },
  { value: 'RANKED_SOLO_5x5', label: '솔로랭크' },
  { value: 'RANKED_FLEX_SR', label: '자유랭크' },
  { value: 'NORMAL_SR', label: '일반 게임' },
  { value: 'ARAM', label: '칼바람 나락' },
  { value: 'ARENA', label: '아레나' },
] as const

export function DashboardPage() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedGameMode, setSelectedGameMode] = useState('ALL')

  const loadSummary = useCallback(async () => {
    try {
      setSummary(await dashboardApi.getSummary(selectedGameMode))
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : '알 수 없는 오류가 발생했습니다.',
      )
    }
  }, [selectedGameMode])

  useEffect(() => {
    // 첫 화면 진입 시 원격 API 결과를 상태에 저장해야 하므로 Effect에서 호출한다.
    // oxlint-disable-next-line react/set-state-in-effect
    void loadSummary()
  }, [loadSummary])

  const inactivityOption = useMemo(
    () =>
      createChurnRateBarOption(summary?.inactivity_churn_rates ?? [], '#3b8cff'),
    [summary],
  )
  const activityOption = useMemo(
    () => createChurnRateBarOption(summary?.activity_churn_rates ?? [], '#ff6b72'),
    [summary],
  )
  const heatmapOption = useMemo(() => createActivityHeatmapOption(), [])

  if (error) {
    return (
      <section className="error-state">
        <h1>데이터를 불러오지 못했습니다</h1>
        <p>{error}</p>
        <button
          type="button"
          onClick={() => {
            setError(null)
            void loadSummary()
          }}
        >
          다시 시도
        </button>
      </section>
    )
  }

  if (!summary) {
    return <p className="loading">전체 현황 데이터를 불러오는 중입니다.</p>
  }

  const excludedUsers =
    summary.kpis.total_users - summary.kpis.model_eligible_users

  return (
    <>
      <header className="page-header">
        <div>
          <h1>전체 현황</h1>
          <p className="page-description">
            사용자 활동과 실제 이탈 현황을 한눈에 확인합니다.
          </p>
        </div>
        <div className="header-badges">
          <span className="demo-badge">진성 활동 고객 배치</span>
          <span className="cutoff-badge">▣ 데이터 기준일&nbsp; {summary.cutoff_date}</span>
        </div>
      </header>

      <section className="filter-bar" aria-label="데이터 조회 조건">
        <div className="filter-item">
          <span className="filter-label">● 전체 수집 범위</span>
          <strong>{summary.collection_scope}</strong>
        </div>
        <label className="filter-item filter-select-item">
          <span className="filter-label">◆ 게임 모드</span>
          <select
            className="filter-select"
            value={selectedGameMode}
            onChange={(event) => setSelectedGameMode(event.target.value)}
            aria-label="게임 모드 선택"
          >
            {GAME_MODES.map((mode) => (
              <option key={mode.value} value={mode.value}>{mode.label}</option>
            ))}
          </select>
        </label>
        <div className="filter-item">
          <span className="filter-label">⚙ 모델 상태</span>
          <strong className="status-badge pending">
            {summary.model_status === 'ready' ? '연동 완료' : '연동 대기'}
          </strong>
        </div>
      </section>

      <section className="kpi-grid" aria-label="핵심 지표">
        <KpiCard label="전체 수집 사용자" value={`${summary.kpis.total_users.toLocaleString()}명`} icon="users" />
        <KpiCard
          label="진성 활동 고객"
          value={`${summary.kpis.model_eligible_users}명`}
          icon="verified-user"
          accent="mint"
        />
        <KpiCard
          label="실제 이탈"
          value={`${summary.kpis.actual_churn_users}명`}
          icon="churn-user"
          accent="coral"
          warning
        />
        <KpiCard
          label="실제 이탈률"
          value={formatPercent(summary.kpis.actual_churn_rate)}
          icon="pie-chart"
          accent="coral"
          warning
        />
        <KpiCard
          label="대상 고객 경기 기록"
          value={`${summary.kpis.unique_matches.toLocaleString()}건`}
          icon="gamepad"
          accent="cyan"
        />
      </section>

      <section className="dashboard-grid">
        <article className="panel span-5">
          <div className="panel-title">
            <h2>비활동 기간별 실제 이탈률</h2>
          </div>
          <EChart
            option={inactivityOption}
            ariaLabel="비활동 기간이 길어질수록 실제 이탈률이 높아지는 막대그래프"
          />
        </article>

        <article className="panel span-4">
          <div className="panel-title">
            <h2>최근 7일 활동별 실제 이탈률</h2>
          </div>
          <EChart
            option={activityOption}
            ariaLabel="최근 7일 경기 수에 따른 실제 이탈률 막대그래프"
          />
        </article>

        <article className="panel span-3">
          <div className="panel-title">
            <h2>진성 활동 고객 구성</h2>
          </div>
          <div className="donut-summary">
            <div className="donut-visual" style={{ background: `conic-gradient(#2d8fff 0 ${(summary.kpis.model_eligible_users / Math.max(summary.kpis.total_users, 1)) * 100}%, #415a78 ${(summary.kpis.model_eligible_users / Math.max(summary.kpis.total_users, 1)) * 100}% 100%)` }} aria-label={`전체 ${summary.kpis.total_users.toLocaleString()}명 중 진성 활동 고객 ${summary.kpis.model_eligible_users.toLocaleString()}명`}>
              <span>{summary.kpis.model_eligible_users.toLocaleString()}명<small>진성 활동 고객</small></span>
            </div>
            <ul className="legend-list">
              <li>
                <span className="legend-dot" />
                {summary.kpis.model_eligible_users.toLocaleString()}명 진성 활동 고객 ({formatPercent(summary.kpis.model_eligible_users / Math.max(summary.kpis.total_users, 1))})
              </li>
              <li>
                <span className="legend-dot muted" />
                {excludedUsers.toLocaleString()}명 그 외 수집 사용자 ({formatPercent(excludedUsers / Math.max(summary.kpis.total_users, 1))})
              </li>
            </ul>
          </div>
        </article>

        <article className="panel span-6">
          <div className="panel-title">
            <h2>요일·시간대 플레이 분포</h2>
            <span className="panel-chip">UTC → KST</span>
          </div>
          <EChart
            option={heatmapOption}
            ariaLabel="요일과 시간대별 플레이 활동 지수 히트맵"
            squareGrid={ACTIVITY_HEATMAP_LAYOUT}
          />
        </article>

        <article className="panel span-3">
          <div className="panel-title">
            <h2>예측 고위험 사용자</h2>
            <span className="panel-chip">CatBoost 상위 점수</span>
          </div>
          <ol className="risk-preview-list">
            <li><span><b>상위 위험 고객</b><small>Risk Customers에서 전체 목록 확인</small></span><strong>상위 20%</strong></li>
            <li><span><b>조치 기준</b><small>Recall과 Precision을 함께 검토</small></span><strong>477명</strong></li>
            <li><span><b>분석 대상</b><small>진성 활동 고객 기준</small></span><strong>2,381명</strong></li>
          </ol>
        </article>

        <article className="panel span-3">
          <div className="panel-title">
            <h2>데이터 품질 안내</h2>
          </div>
          <ul className="quality-list">
            {summary.data_quality_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
          <p className="panel-footnote">게임 모드 선택 시 해당 모드 경기 비율이 있는 고객 기준으로 다시 집계합니다.</p>
        </article>
      </section>
    </>
  )
}
