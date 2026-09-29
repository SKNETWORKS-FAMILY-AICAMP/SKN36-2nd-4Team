import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardApi } from '../../api/client'
import type { RiskLevel, RiskUserListResponse } from '../../api/types'
import { EChart } from '../../components/common/EChart'
import {
  createRiskDistributionOption,
} from './chartOptions'

const riskLabels: Record<RiskLevel, string> = {
  HIGH: '고위험',
  MEDIUM: '주의',
  LOW: '안정',
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function RiskUsersPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<RiskUserListResponse | null>(null)
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState<'ALL' | RiskLevel>('ALL')
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
        기준일 이전 행동 피처와 5-fold OOF CatBoost 점수로 정렬한 목록입니다. 점수는 고객 우선순위를 정하는 기준입니다.
      </div>

      <section className="metric-grid risk-metric-grid" aria-label="위험 사용자 핵심 지표">
        <article className="metric-card danger-metric">
          <span>고위험 사용자</span>
          <strong>{data.overview.high_risk_users.toLocaleString()}명</strong>
          <small>위험 점수 70점 이상</small>
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
          <EChart option={distributionOption} ariaLabel="고위험, 주의, 안정 사용자 분포 도넛 차트" />
        </article>

        <article className="panel span-8">
          <div className="panel-title"><h2>분석 기준</h2><span className="panel-chip">CORE COHORT</span></div>
          <p className="panel-footnote">이 목록은 티어가 아니라 진성 활동 고객 조건과 CatBoost 위험 점수로 정렬합니다. 티어 데이터는 현재 수집하지 않았습니다.</p>
        </article>

        <article className="panel span-12 risk-table-panel">
          <div className="panel-title table-panel-title">
            <div>
              <h2>위험 사용자 목록</h2>
              <p>사용자 행을 클릭하면 상세 분석 화면으로 이동합니다.</p>
            </div>
            <span className="panel-chip">{filteredUsers.length}명 표시</span>
          </div>

          <div className="risk-filter-row">
            <label className="search-control">
              <span>검색</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="player_id 또는 team_id:player_id"
              />
            </label>
            <label>
              <span>위험 등급</span>
              <select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value as 'ALL' | RiskLevel)}>
                <option value="ALL">전체</option>
                <option value="HIGH">고위험</option>
                <option value="MEDIUM">주의</option>
                <option value="LOW">안정</option>
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
                {filteredUsers.map((user, index) => (
                  <tr
                    key={user.record_id}
                    className="clickable-row"
                    onClick={() => navigate(`/users/${encodeURIComponent(user.record_id)}`)}
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') navigate(`/users/${encodeURIComponent(user.record_id)}`)
                    }}
                  >
                    <td className="rank-cell">#{String(index + 1).padStart(2, '0')}</td>
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
              </tbody>
            </table>
          </div>
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
              <p><span className="method-high">고위험 70점 이상</span><span className="method-medium">주의 50~69점</span><span className="method-low">안정 50점 미만</span></p>
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
