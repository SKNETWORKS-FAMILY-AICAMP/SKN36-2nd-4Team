import { useEffect, useMemo, useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { dashboardApi } from '../../api/client'
import type { RiskUser, UserDetailResponse } from '../../api/types'
import { EChart } from '../../components/common/EChart'
import {
  createActivityCalendarOption,
  createIntervalOption,
  createModeOption,
  createPerformanceOption,
} from './chartOptions'

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function UserDetailPage() {
  const { playerId = '' } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState<UserDetailResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<RiskUser[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchMessage, setSearchMessage] = useState('')

  useEffect(() => {
    setData(null)
    setError(null)
    void dashboardApi
      .getUserDetail(playerId)
      .then(setData)
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : '사용자 데이터를 불러오지 못했습니다.')
      })
  }, [playerId])

  useEffect(() => {
    const keyword = searchQuery.trim()
    if (!keyword) {
      setSearchResults([])
      setSearchMessage('')
      setSearchLoading(false)
      return undefined
    }

    setSearchLoading(true)
    const timer = window.setTimeout(() => {
      void dashboardApi.searchUsers(keyword)
        .then((results) => {
          setSearchResults(results)
          setSearchMessage(results.length === 0 ? '검색 결과가 없습니다.' : '')
        })
        .catch(() => {
          setSearchResults([])
          setSearchMessage('사용자 검색에 실패했습니다.')
        })
        .finally(() => setSearchLoading(false))
    }, 180)

    return () => window.clearTimeout(timer)
  }, [searchQuery])

  const activityOption = useMemo(() => createActivityCalendarOption(data?.activity ?? []), [data])
  const performanceOption = useMemo(() => createPerformanceOption(data?.performance ?? []), [data])
  const intervalOption = useMemo(() => createIntervalOption(data?.intervals ?? []), [data])
  const modeOption = useMemo(() => createModeOption(data?.modes ?? []), [data])

  const moveToUser = (user: RiskUser) => {
    setSearchQuery('')
    setSearchResults([])
    setSearchMessage('')
    navigate(`/users/${encodeURIComponent(user.record_id)}`)
  }

  const handleSearchSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const keyword = searchQuery.trim()
    if (!keyword) return

    setSearchLoading(true)
    try {
      const results = await dashboardApi.searchUsers(keyword)
      const exact = results.find((user) =>
        user.player_id.toLowerCase() === keyword.toLowerCase() ||
        user.record_id.toLowerCase() === keyword.toLowerCase(),
      )
      const target = exact ?? results[0]
      if (target) {
        moveToUser(target)
      } else {
        setSearchResults([])
        setSearchMessage('검색 결과가 없습니다.')
      }
    } catch {
      setSearchMessage('사용자 검색에 실패했습니다.')
    } finally {
      setSearchLoading(false)
    }
  }

  if (error) {
    return (
      <section className="error-state">
        <h1>사용자 데이터를 불러오지 못했습니다</h1>
        <p>{error}</p>
        <button type="button" onClick={() => navigate('/risk-users')}>위험 사용자 목록으로</button>
      </section>
    )
  }

  if (!data) {
    return <p className="loading">사용자 상세 데이터를 불러오는 중입니다.</p>
  }

  return (
    <>
      <header className="page-header user-detail-header">
        <div>
          <button className="back-link" type="button" onClick={() => navigate('/risk-users')}>← 위험 사용자 목록</button>
          <h1>사용자 상세</h1>
          <p className="page-description">활동 변화와 모델 판단 근거를 사용자 단위로 확인합니다.</p>
        </div>
        <div className="header-badges">
          <span className="demo-badge">CATBOOST OOF</span>
          <span className="cutoff-badge">기준일 2026-08-01 · 최대 90일 피처</span>
        </div>
      </header>

      <section className="user-search-panel" aria-label="사용자 검색">
        <form className="user-search-form" onSubmit={handleSearchSubmit}>
          <div className="user-search-copy">
            <strong>사용자 검색</strong>
            <small>분석용 player_id 또는 수집팀:player_id를 입력해 찾습니다.</small>
          </div>
          <div className="user-search-box">
            <div className="user-search-input-row">
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="예: 947bfb88e3f67301 또는 3:947bfb88e3f67301"
                aria-label="분석용 player_id 검색"
                autoComplete="off"
              />
              <button type="submit" disabled={searchLoading}>
                {searchLoading ? '검색 중' : '검색'}
              </button>
            </div>
            {searchQuery.trim() && (
              <div className="user-search-results">
                {searchResults.map((user) => (
                  <button key={user.record_id} type="button" onClick={() => moveToUser(user)}>
                    <span>
                      <strong>{user.player_id}</strong>
                      <small>수집팀 {user.record_id.split(':')[0]}</small>
                    </span>
                    <b>{(user.risk_score * 100).toFixed(1)}점</b>
                  </button>
                ))}
                {searchMessage && <p>{searchMessage}</p>}
              </div>
            )}
          </div>
        </form>
      </section>

      <section className="user-hero-panel">
        <div className="user-profile-block">
          <span className="summoner-avatar">{data.player_id.charAt(0).toUpperCase()}</span>
          <div>
            <p className="eyebrow">분석용 사용자 ID</p>
            <h2>{data.player_id}</h2>
            <div className="profile-meta">
              <span>최근 활동 {data.last_game_days}일 전</span>
            </div>
          </div>
        </div>

        <div className={`risk-gauge ${data.risk_level.toLowerCase()}`}>
          <div className="risk-ring" style={{ '--risk-angle': `${data.risk_score * 360}deg` } as CSSProperties}>
            <div>
              <span>위험 점수</span>
              <strong>{(data.risk_score * 100).toFixed(1)}점</strong>
              <b>{data.risk_level} RISK</b>
            </div>
          </div>
        </div>
      </section>

      <section className="metric-grid user-metric-grid">
        <article className="metric-card"><span>최근 30일 경기</span><strong>{data.recent_matches}경기</strong><small>활동량 핵심 지표</small></article>
        <article className="metric-card"><span>최근 승률</span><strong>{formatPercent(data.recent_win_rate)}</strong><small>관찰 구간 승패 기준</small></article>
        <article className="metric-card"><span>평균 KDA</span><strong>{data.average_kda.toFixed(2)}</strong><small>최근 경기 평균</small></article>
        <article className="metric-card warning-metric"><span>평균 경기 간격</span><strong>{data.average_interval_days.toFixed(1)}일</strong><small>간격 증가 시 위험 신호</small></article>
      </section>

      <section className="content-grid user-detail-grid">
        <article className="panel span-7 activity-panel">
          <div className="panel-title"><h2>기준일 전 30일 활동</h2><span className="panel-chip">실제 경기 기록</span></div>
          <EChart className="activity-calendar-chart" option={activityOption} ariaLabel="날짜별 경기 횟수 활동 캘린더 히트맵" />
          <p className="chart-insight">날짜별 경기 수를 표시합니다. 활동 감소 여부는 이전 기간과 함께 확인하세요.</p>
        </article>

        <article className="panel span-5">
          <div className="panel-title"><h2>점수 해석</h2><span className="panel-chip">OOF 순위 점수</span></div>
          <p className="panel-footnote">개별 사용자 단위 SHAP 기여도는 아직 산출하지 않았습니다. 아래 활동 지표는 관측값이며, 이탈 원인이나 보상 효과를 뜻하지 않습니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>최근 경기 성과</h2><span className="panel-chip">실제 경기 기록</span></div>
          <EChart option={performanceOption} ariaLabel="최근 경기 KDA 변화 선그래프" />
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>경기 간격</h2><span className="panel-chip">실제 경기 기록</span></div>
          <EChart option={intervalOption} ariaLabel="최근 경기 사이 간격이 증가하는 막대그래프" />
        </article>

        <article className="panel span-4">
          <div className="panel-title"><h2>게임 모드 분포</h2><span className="panel-chip">기준일 전 30일</span></div>
          <EChart option={modeOption} ariaLabel="솔로랭크 칼바람 자유랭크 등 최근 게임 모드 분포" />
        </article>

        <article className="panel span-8">
          <div className="panel-title"><h2>최근 경기 요약</h2><span className="panel-chip">실제 경기 기록</span></div>
          <div className="recent-match-list">
            {data.performance.slice(-6).reverse().map((match) => (
              <div key={match.match_no} className={`match-row ${match.win ? 'win' : 'loss'}`}>
                <div><strong>{match.win ? '승리' : '패배'}</strong><small>#{match.match_no} 경기</small></div>
                <span>KDA <b>{match.kda.toFixed(1)}</b></span>
                <span>DMG≈ <b>{match.damage.toLocaleString()}</b></span>
                <span>CS≈ <b>{match.cs}</b></span>
                <span>VISION≈ <b>{match.vision}</b></span>
                <span>{match.duration_minutes}분</span>
              </div>
            ))}
          </div>
          <p className="panel-footnote">≈ 표시는 원본의 분당 수치에 경기시간을 곱해 환산한 참고값입니다.</p>
        </article>
      </section>
    </>
  )
}
