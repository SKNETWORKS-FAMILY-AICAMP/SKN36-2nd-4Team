import { useEffect, useMemo, useState } from 'react'
import { dashboardApi } from '../../api/client'
import type { SyntheticSurvivalResponse, SyntheticSurvivalUser } from '../../api/types'

type Horizon = 7 | 14 | 30

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

function eventRisk(user: SyntheticSurvivalUser, days: Horizon): number {
  if (days === 7) return user.event_risk_7d
  if (days === 14) return user.event_risk_14d
  return user.event_risk_30d
}

function activitySurvival(user: SyntheticSurvivalUser, days: Horizon): number {
  if (days === 7) return user.activity_survival_7d
  if (days === 14) return user.activity_survival_14d
  return user.activity_survival_30d
}

export function SurvivalAnalysisPage() {
  const [data, setData] = useState<SyntheticSurvivalResponse | null>(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [selectedRecordId, setSelectedRecordId] = useState('')

  useEffect(() => {
    void dashboardApi.getSyntheticSurvivalUsers()
      .then((response) => {
        setData(response)
        setSelectedRecordId(response.items[0]?.record_id ?? '')
      })
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : '생존분석 자료를 불러오지 못했습니다.')
      })
  }, [])

  const filteredUsers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    if (!normalizedQuery) return data?.items ?? []
    return (data?.items ?? []).filter((user) =>
      user.player_id.toLowerCase().includes(normalizedQuery) ||
      user.record_id.toLowerCase().includes(normalizedQuery),
    )
  }, [data, query])

  const selectedUser = data?.items.find((user) => user.record_id === selectedRecordId) ?? filteredUsers[0]
  const cohortAverages = useMemo(() => {
    if (!data?.items.length) return null
    const count = data.items.length
    return {
      7: data.items.reduce((sum, user) => sum + user.activity_survival_7d, 0) / count,
      14: data.items.reduce((sum, user) => sum + user.activity_survival_14d, 0) / count,
      30: data.items.reduce((sum, user) => sum + user.activity_survival_30d, 0) / count,
    }
  }, [data])

  const horizons: Horizon[] = [7, 14, 30]

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">EXTENSION MODEL</p>
          <h1>생존분석 확장</h1>
          <p className="page-description">Cox 모델의 사용자별 기간 추정 예시와 실제 적용에 필요한 검증 기준을 확인합니다.</p>
        </div>
        <div className="header-badges">
          <span className="demo-badge">합성 검증 표본</span>
          <span className="cutoff-badge">Cox PH · C-index 0.762</span>
        </div>
      </header>

      <section className="demo-notice">
        <strong>시연 전용 · 실제 고객 예측 아님</strong>
        {data?.warning ?? '실제 후속 경기 라벨이 없어 만든 합성 데모입니다. 운영 점수로 사용하면 안 됩니다.'} 실제 피처와 기존 30일 무경기 라벨을 이용해 가상 이벤트 시점을 만들었으며, 아래 값은 합성 시험 표본 {data?.test_users ?? 715}명의 예측입니다.
      </section>

      {error && <section className="error-state"><h2>합성 시험 표본을 불러오지 못했습니다</h2><p>{error}</p></section>}
      {!data && !error && <p className="loading">합성 시험 표본을 불러오는 중입니다.</p>}

      {data && selectedUser && cohortAverages && (
        <>
          <section className="survival-definition panel">
            <div className="panel-title"><h2>이 화면에서 말하는 ‘생존’과 ‘이탈 위험’</h2><span className="panel-chip demo">가상 이벤트 기준</span></div>
            <p><b>활동 유지 추정</b>은 해당 기간 안에 가상 30일 무경기 이벤트가 발생하지 않을 것으로 계산된 비율입니다. <b>가상 이탈 위험</b>은 그 반대값(1 − 활동 유지 추정)이며, 계정 탈퇴·실제 이탈 확률을 뜻하지 않습니다.</p>
            <p>합성 30일 이벤트율을 기존 코호트의 실제 30일 무경기율(15.25%)에 맞춰 생성했기 때문에 전체 평균은 30일 기준 약 85% 유지로 나타납니다. 짧은 7일·14일 구간에서는 이벤트가 덜 발생하도록 설정되어 값이 더 높습니다.</p>
          </section>

          <section className="panel survival-user-panel">
            <div className="panel-title"><h2>사용자별 7·14·30일 추정치</h2><span className="panel-chip">시험 표본 {data.test_users.toLocaleString()}명</span></div>
            <div className="survival-user-toolbar">
              <label htmlFor="survival-user-search">분석용 사용자 ID 검색</label>
              <input id="survival-user-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="player_id 또는 team_id:player_id" />
              <span>{filteredUsers.length.toLocaleString()}명 표시</span>
            </div>
            <div className="survival-user-layout">
              <div className="table-scroll survival-user-table-wrap">
                <table className="data-table survival-user-table">
                  <thead><tr><th>표본 내 순위</th><th>분석용 사용자 ID</th><th>상대 구간</th><th>7일 위험</th><th>14일 위험</th><th>30일 위험</th></tr></thead>
                  <tbody>
                    {filteredUsers.map((user) => (
                      <tr key={user.record_id} className={selectedUser.record_id === user.record_id ? 'selected-row' : ''} onClick={() => setSelectedRecordId(user.record_id)}>
                        <td>#{user.risk_rank}</td><td>{user.record_id}</td><td><span className={`survival-risk-tag ${user.risk_band === '고위험' ? 'high' : user.risk_band === '주의' ? 'watch' : ''}`}>{user.risk_band}</span></td>
                        <td>{percent(user.event_risk_7d)}</td><td>{percent(user.event_risk_14d)}</td><td>{percent(user.event_risk_30d)}</td>
                      </tr>
                    ))}
                    {filteredUsers.length === 0 && <tr><td colSpan={6}>검색 결과가 없습니다.</td></tr>}
                  </tbody>
                </table>
              </div>
              <article className="survival-user-detail">
                <div className="survival-detail-heading"><div><small>선택 사용자 · 합성 Cox 시험 결과</small><strong>{selectedUser.record_id}</strong></div><span className={`survival-risk-tag ${selectedUser.risk_band === '고위험' ? 'high' : selectedUser.risk_band === '주의' ? 'watch' : ''}`}>{selectedUser.risk_band}</span></div>
                <p className="panel-footnote">시험 표본 내 30일 가상 이벤트 위험 순위 #{selectedUser.risk_rank}. “고위험/주의”는 이 합성 표본 안에서만 나눈 상대 구간입니다.</p>
                <table className="data-table survival-horizon-table"><thead><tr><th>기간</th><th>활동 유지 추정</th><th>가상 무경기 위험</th></tr></thead><tbody>
                  {horizons.map((days) => <tr key={days}><td>{days}일</td><td>{percent(activitySurvival(selectedUser, days))}</td><td>{percent(eventRisk(selectedUser, days))}</td></tr>)}
                </tbody></table>
                <p className="panel-footnote">예: 30일 위험 {percent(selectedUser.event_risk_30d)}는 합성 라벨 아래의 값이며, 실제 개인의 이탈 확률로 해석하지 않습니다.</p>
              </article>
            </div>
            <p className="panel-footnote">구간 기준: 시험 표본 715명 안에서 30일 가상 이벤트 위험 상위 20%는 고위험, 다음 20%는 주의, 나머지는 일반 관찰입니다. 실제 CatBoost 위험 등급과는 별도입니다.</p>
          </section>

          <section className="content-grid">
            <article className="panel span-8">
              <div className="panel-title"><h2>시험 표본 평균 활동 유지 추정</h2><span className="panel-chip demo">합성 결과</span></div>
              <div className="survival-chart" role="img" aria-label="합성 시험 표본의 기간별 평균 활동 유지 추정">
                {horizons.map((days) => <div className="survival-column" key={days}><span>{percent(cohortAverages[days])}</span><i style={{ height: `${cohortAverages[days] * 100}%` }} /><b>{days}일</b></div>)}
              </div>
              <p className="panel-footnote">715명 Cox 시험 표본의 사용자별 추정치를 평균한 값입니다. 실제 관측 생존율이 아닙니다.</p>
            </article>
            <article className="panel span-4">
              <div className="panel-title"><h2>실험 요약</h2></div>
              <dl className="definition-list">
                <div><dt>원 코호트</dt><dd>{data.cohort_users.toLocaleString()}명</dd></div>
                <div><dt>합성 시험 표본</dt><dd>{data.test_users.toLocaleString()}명</dd></div>
                <div><dt>30일 이벤트 생성 목표</dt><dd>실제 코호트 15.25%</dd></div>
                <div><dt>C-index</dt><dd>{data.c_index.toFixed(3)} · 합성 검증</dd></div>
              </dl>
              <p className="panel-footnote">{data.risk_band_definition}. CatBoost의 OOF 점수·위험 등급과 직접 비교하지 않습니다.</p>
            </article>

            <article className="panel span-12">
              <div className="panel-title"><h2>생존분석 평가지표는 무엇을 보나요?</h2><span className="panel-chip">현재 검증 범위</span></div>
              <div className="survival-metric-grid">
                <div><b>C-index · 0.762</b><strong>계산됨 · 합성 자료</strong><p>실제 이벤트가 더 빨리 발생한 사람에게 모델이 더 높은 위험 순위를 주는지 봅니다. 0.5는 무작위 순위, 1은 완벽한 순위입니다. 이 점수는 합성 생성 규칙과 비교한 결과라 실제 예측력을 보장하지 않습니다.</p></div>
                <div><b>IBS · 미산출</b><strong>낮을수록 좋음</strong><p>시간에 따른 생존확률 예측과 관측 결과의 평균 제곱 오차를 적분한 값입니다. 검열을 반영한 평가가 필요하며 0에 가까울수록 예측 오차가 작습니다.</p></div>
                <div><b>시간의존 ROC-AUC · 미산출</b><strong>높을수록 좋음</strong><p>예를 들어 30일 시점에서 그때까지 이벤트가 난 사람과 아직 이벤트가 없는 사람을 위험 점수로 구분하는 능력입니다. 일반 ROC-AUC와 달리 시점과 검열을 고려해야 합니다.</p></div>
              </div>
              <p className="panel-footnote">IBS와 시간의존 ROC-AUC는 숫자를 임의로 채우지 않았습니다. 실제 후속 경기 이벤트·검열 기간을 충분히 수집한 뒤 동일한 holdout 기간에서 계산해야 합니다.</p>
            </article>

            <article className="panel span-12">
              <div className="panel-title"><h2>실제 적용 전 검토할 개입안</h2><span className="panel-chip">A/B 검증 필요</span></div>
              <div className="survival-actions"><div><b>활동 간격이 평소보다 늘 때</b><span>보상 없는 관련 콘텐츠·이벤트 안내부터 노출</span></div><div><b>복귀 유도 대상</b><span>복귀 미션 완료 시 열쇠·상자 등 비경쟁성 보상 후보 검토</span></div><div><b>랭크 중심 고객</b><span>랭크 점수나 매칭 결과에 영향을 주는 보상은 제외하고, 별도 꾸미기 보상으로 설계</span></div></div>
              <p className="panel-footnote">30일은 이번 프로젝트의 무경기 라벨 기준이지, 한 달 미접속 즉시 휴면 처리하자는 운영 규칙이 아닙니다. 보상은 무작위 일부 대상 A/B 테스트로 재접속·추가 경기·비용을 비교한 뒤 결정해야 합니다.</p>
            </article>
          </section>
        </>
      )}
    </>
  )
}
