import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardApi } from '../../api/client'
import type { RiskLevel, RiskUserListResponse } from '../../api/types'
import { EChart } from '../../components/common/EChart'
import {
  createRiskDistributionOption,
} from './chartOptions'

const PAGE_SIZE = 20

const riskLabels: Record<RiskLevel, string> = {
  HIGH: '고위험',
  MEDIUM: '주의',
  LOW: '일반 관찰',
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

function pageNumbers(current: number, total: number): number[] {
  const start = Math.max(1, Math.min(current - 2, total - 4))
  const end = Math.min(total, start + 4)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
}

export function RiskUsersPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<RiskUserListResponse | null>(null)
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState<'ALL' | RiskLevel>('ALL')
  const [page, setPage] = useState(1)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void dashboardApi
      .getRiskUsers()
      .then(setData)
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : '데이터를 불러오지 못했습니다.')
      })
  }, [])

  const filteredUsers = useMemo(() => {
    if (!data) return []
    const keyword = search.trim().toLowerCase()
    return data.items.filter((user) => {
      const matchesSearch =
        !keyword ||
        user.record_id.toLowerCase().includes(keyword) ||
        user.player_id.toLowerCase().includes(keyword)
      const matchesRisk = riskFilter === 'ALL' || user.risk_level === riskFilter
      return matchesSearch && matchesRisk
    })
  }, [data, riskFilter, search])

  const distributionOption = useMemo(
    () => createRiskDistributionOption(data?.distribution ?? []),
    [data],
  )
  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / PAGE_SIZE))
  const visibleUsers = filteredUsers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const originalRanks = useMemo(
    () => new Map((data?.items ?? []).map((user, index) => [user.record_id, index + 1])),
    [data],
  )

  if (error) {
    return <section className="error-state"><h1>위험 사용자 데이터를 불러오지 못했습니다</h1><p>{error}</p></section>
  }

  if (!data) {
    return <p className="loading">위험 사용자 데이터를 불러오는 중입니다.</p>
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>위험 사용자</h1>
          <p className="page-description">이탈 가능성이 높은 사용자를 탐지하고 주요 위험 신호를 비교합니다.</p>
        </div>
        <div className="header-badges">
          <span className="demo-badge">CATBOOST OOF</span>
          <span className="cutoff-badge">진성 활동 고객 {data.total.toLocaleString()}명</span>
        </div>
      </header>

      <div className="demo-notice">
        <strong>실제 검증 결과</strong>
        진성 고객 피처를 재평가해 선택한 CatBoost의 5-fold OOF 점수로 정렬했습니다. 후보 선택 후 계산한 점수이므로 성능은 탐색용입니다.
      </div>

      <section className="metric-grid risk-metric-grid" aria-label="위험 사용자 핵심 지표">
        <article className="metric-card danger-metric">
          <span>고위험 사용자</span>
          <strong>{data.overview.high_risk_users.toLocaleString()}명</strong>
          <small>점수 순위 상위 10%</small>
        </article>
        <article className="metric-card">
          <span>실제 30일 무경기 비율</span>
          <strong>15.25%</strong>
          <small>기준일 이후 관측 결과 · 계정 탈퇴율 아님</small>
        </article>
        <article className="metric-card warning-metric">
          <span>상위 20% 조치 규모</span>
          <strong>{data.overview.campaign_target_users.toLocaleString()}명</strong>
          <small>현재 배치에서 우선 검토할 고객</small>
        </article>
        <article className="metric-card">
          <span>고위험 평균 미활동</span>
          <strong>{data.overview.average_inactive_days.toFixed(1)}일</strong>
          <small>최근 경기 이후 공백</small>
        </article>
      </section>

      <section className="content-grid risk-users-grid">
        <article className="panel span-4">
          <div className="panel-title">
            <h2>위험 등급 분포</h2>
            <span className="panel-chip">{data.total.toLocaleString()} USERS</span>
          </div>
          <EChart option={distributionOption} ariaLabel="고위험, 주의, 일반 관찰 사용자 분포 도넛 차트" />
        </article>

        <article className="panel span-8 analysis-criteria-panel">
          <div className="panel-title"><h2>분석 기준</h2><span className="panel-chip">CORE COHORT</span></div>
          <div className="analysis-criteria-grid">
            <div className="analysis-criterion">
              <span>분석 대상</span>
              <strong>{data.total.toLocaleString()}명</strong>
              <p>90일 관찰 구간의 경기 기록이 확보된 진성 활동 고객만 사용합니다.</p>
            </div>
            <div className="analysis-criterion">
              <span>이탈 정의</span>
              <strong>향후 30일 0경기</strong>
              <p>기준일 이후 30일 동안 경기 기록이 없으면 이탈(무경기)로 라벨링합니다.</p>
            </div>
            <div className="analysis-criterion">
              <span>위험 점수</span>
              <strong>CatBoost · 5-Fold OOF</strong>
              <p>각 사용자가 학습에 포함되지 않은 Fold 모델에서 받은 점수로 순위를 정합니다.</p>
            </div>
            <div className="analysis-criterion">
              <span>위험 등급</span>
              <strong>10% · 10% · 80%</strong>
              <p>상위 10% 고위험, 다음 10% 주의, 나머지 80% 일반 관찰로 구분합니다.</p>
            </div>
          </div>
          <div className="analysis-flow" aria-label="위험 사용자 분석 흐름">
            <span>90일 행동 관찰</span><i>→</i><span>33개 행동 피처</span><i>→</i><span>OOF 위험 점수</span><i>→</i><span>상위 20% 우선 검토</span>
          </div>
          <p className="panel-footnote">점수는 보정된 이탈 확률이 아니라 고객 간 우선순위를 정하기 위한 모델 출력입니다. 티어는 수집 시점이 불명확해 모델 입력에서 제외했습니다.</p>
        </article>

        {data.tier_analysis && <article className="panel span-12 tier-analysis-panel">
          <div className="panel-title"><h2>티어별 경기 중단 현황</h2><span className="panel-chip">{data.tier_analysis.matched_users.toLocaleString()} / {data.tier_analysis.core_users.toLocaleString()}명 매칭</span></div>
          <div className="table-scroll">
            <table className="data-table" aria-label="진성 고객의 시드 티어별 관측 무경기율과 경기 지표">
              <thead><tr><th>시드 티어</th><th>고객 수</th><th>30일 무경기</th><th>관측 무경기율</th><th>최근 승률 평균</th><th>최근 KDA 평균</th><th>최근 30일 경기 평균</th></tr></thead>
              <tbody>{data.tier_analysis.tiers.map((row) => <tr key={row.tier}>
                <td>{row.tier}</td>
                <td>{row.users.toLocaleString()}명</td>
                <td>{row.churners.toLocaleString()}명</td>
                <td><strong>{formatPercent(row.observed_no_match_rate)}</strong></td>
                <td>{row.average_win_rate === null ? '—' : formatPercent(row.average_win_rate)}</td>
                <td>{row.average_kda === null ? '—' : row.average_kda.toFixed(2)}</td>
                <td>{row.average_games_30d === null ? '—' : `${row.average_games_30d.toFixed(1)}경기`}</td>
              </tr>)}</tbody>
            </table>
          </div>
          <p className="panel-footnote">티어가 연결된 사용자만 참고 집계합니다. 미매칭 사용자는 티어 미확인으로 처리하며, 티어 정보는 모델 피처나 원인 해석에 사용하지 않습니다.</p>
        </article>}

        <article className="panel span-12 retention-policy-panel">
          <div className="panel-title"><h2>이탈 예방 조치안</h2><span className="panel-chip">캠페인 검증 전</span></div>
          <div className="retention-policy-grid">
            <div className="retention-policy-card priority">
              <span>위험 순위 상위 10% · {data.overview.high_risk_users.toLocaleString()}명</span>
              <strong>적극적인 복귀 지원</strong>
              <p>플레이 유형에 맞춘 개인화 캠페인과 복귀 미션·비경쟁성 보상을 검토합니다.</p>
            </div>
            <div className="retention-policy-card low-cost">
              <span>위험 순위 10~20% · 약 {(data.overview.campaign_target_users - data.overview.high_risk_users).toLocaleString()}명</span>
              <strong>저비용 접점 유지</strong>
              <p>관심 게임 모드의 업데이트·이벤트 알림과 콘텐츠 추천을 우선 검토합니다.</p>
            </div>
          </div>
          <p className="panel-footnote">상위 20%는 상위 10%를 포함하므로 두 조치군이 겹치지 않도록 나눴습니다. 비용 대비 리텐션 효과는 아직 측정되지 않았으며, 무작위 대조군을 둔 A/B 테스트에서 재방문·추가 경기·캠페인 비용을 비교한 뒤 결정해야 합니다.</p>
        </article>

        <article className="panel span-12 risk-table-panel">
          <div className="panel-title table-panel-title">
            <div>
              <h2>위험 사용자 목록</h2>
              <p>사용자 행을 클릭하면 상세 분석 화면으로 이동합니다.</p>
            </div>
            <span className="panel-chip">검색 결과 {filteredUsers.length.toLocaleString()}명 · 페이지당 {PAGE_SIZE}명</span>
          </div>

          <div className="risk-filter-row">
            <label className="search-control">
              <span>검색</span>
              <input
                value={search}
                onChange={(event) => { setSearch(event.target.value); setPage(1) }}
                placeholder="player_id 또는 team_id:player_id"
              />
            </label>
            <label>
              <span>위험 등급</span>
              <select value={riskFilter} onChange={(event) => { setRiskFilter(event.target.value as 'ALL' | RiskLevel); setPage(1) }}>
                <option value="ALL">전체</option>
                <option value="HIGH">고위험</option>
                <option value="MEDIUM">주의</option>
                <option value="LOW">일반 관찰</option>
              </select>
            </label>
          </div>

          <div className="table-scroll">
            <table className="data-table risk-users-table">
              <thead>
                <tr>
                  <th>RANK</th>
                  <th>player_id (분석용)</th>
                  <th>위험도</th>
                  <th>최근 경기</th>
                  <th>최근 경기 수</th>
                  <th>승률</th>
                  <th>관측 신호</th>
                </tr>
              </thead>
              <tbody>
                {visibleUsers.map((user, index) => (
                  <tr
                    key={user.record_id}
                    className="clickable-row"
                    onClick={() => navigate(`/users/${encodeURIComponent(user.record_id)}`)}
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') navigate(`/users/${encodeURIComponent(user.record_id)}`)
                    }}
                  >
                    <td className="rank-cell">#{String(originalRanks.get(user.record_id) ?? (page - 1) * PAGE_SIZE + index + 1).padStart(2, '0')}</td>
                    <td><strong className="user-id-cell">{user.player_id}</strong><small>수집팀 {user.record_id.split(':')[0]}</small></td>
                    <td>
                      <div className="risk-score-cell">
                        <strong>{(user.risk_score * 100).toFixed(1)}점</strong>
                        <span className={`risk-level ${user.risk_level.toLowerCase()}`}>{riskLabels[user.risk_level]}</span>
                      </div>
                    </td>
                    <td>{user.last_game_days}일 전</td>
                    <td>{user.recent_matches}경기</td>
                    <td>{formatPercent(user.win_rate)}</td>
                    <td><span className="reason-pill">{user.main_reason}</span></td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && <tr><td colSpan={7} className="empty-table-cell">조건에 맞는 사용자가 없습니다.</td></tr>}
              </tbody>
            </table>
          </div>
          <nav className="risk-pagination" aria-label="위험 사용자 목록 페이지 이동">
            <div className="risk-pagination-buttons">
              <button type="button" disabled={page === 1} onClick={() => setPage((current) => current - 1)}>이전</button>
              {pageNumbers(page, totalPages).map((number) => <button
                key={number}
                type="button"
                className={number === page ? 'active' : ''}
                aria-current={number === page ? 'page' : undefined}
                onClick={() => setPage(number)}
              >{number}</button>)}
              <button type="button" disabled={page === totalPages} onClick={() => setPage((current) => current + 1)}>다음</button>
            </div>
            <label className="risk-pagination-slider">
              <span>드래그해서 페이지 이동</span>
              <input type="range" min={1} max={totalPages} value={page} disabled={totalPages === 1} onChange={(event) => setPage(Number(event.target.value))} aria-label="위험 사용자 목록 페이지" />
              <strong>{page} / {totalPages}</strong>
            </label>
          </nav>
        </article>

        <article className="panel span-12 risk-method-panel">
          <div className="panel-title">
            <h2>위험도 측정 방법</h2>
            <span className="panel-chip">CATBOOST SCORE</span>
          </div>
          <div className="risk-method-formula">
            <span>위험 점수</span>
            <strong>OOF 점수 × 100</strong>
            <small>고객 간 우선순위를 비교하기 위한 모델 점수입니다. 보정된 이탈 확률로 해석하지 않습니다.</small>
          </div>
          <div className="risk-method-grid">
            <div>
              <b>01</b>
              <strong>행동 피처 생성</strong>
              <p>최근 경기 수, 마지막 활동 경과일, 경기 간격, 승률·KDA, 플레이 시간과 게임 모드 변화 등을 사용자 단위로 집계합니다.</p>
            </div>
            <div>
              <b>02</b>
              <strong>위험 점수 계산</strong>
              <p>5-fold 학습에서 각 고객이 학습에 포함되지 않은 fold 모델로 받은 OOF 점수를 사용합니다.</p>
            </div>
            <div>
              <b>03</b>
              <strong>위험 등급 구간</strong>
              <p><span className="method-high">고위험 상위 10%</span><span className="method-medium">주의 다음 10%</span><span className="method-low">일반 관찰 나머지 80%</span></p>
            </div>
            <div>
              <b>04</b>
              <strong>관측 신호</strong>
              <p>목록의 신호는 집계 피처로 만든 참고 문구입니다. 개별 SHAP 기여도나 이탈 원인 분석 결과는 아닙니다.</p>
            </div>
          </div>
          <p className="risk-method-note">점수는 계정 탈퇴 확률이 아니라 30일 무경기 이탈 위험을 기준으로 계산한 모델 출력입니다. 캠페인 효과는 별도 A/B 테스트로 확인해야 합니다.</p>
        </article>
      </section>
    </>
  )
}
