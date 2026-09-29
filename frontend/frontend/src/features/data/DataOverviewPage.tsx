import { useEffect, useState } from 'react'
import { dashboardApi } from '../../api/client'

const featureGroups = [
  { category: '활동성', examples: '최근 7일 경기 수, 활동일 수, 마지막 경기 경과일', reason: '플레이 빈도와 최근성 변화' },
  { category: '경기 간격', examples: '평균·최대 경기 간격, 14일 간격 변화율', reason: '접속 주기가 길어지는 패턴' },
  { category: '성과', examples: '최근 승률, KDA 변화, 연속 패배 수', reason: '최근 경기 경험의 변화' },
  { category: '플레이 성향', examples: '주요 모드, 랭크 비중, 챔피언·포지션 다양성', reason: '플레이 방식의 변화' },
]

export function DataOverviewPage() {
  const [positionEda, setPositionEda] = useState<Awaited<ReturnType<typeof dashboardApi.getMonthlyPositionEda>> | null>(null)
  useEffect(() => { void dashboardApi.getMonthlyPositionEda().then(setPositionEda).catch(() => setPositionEda(null)) }, [])
  return (
    <>
      <header className="page-header">
        <div>
          <h1>데이터 설명</h1>
          <p className="page-description">수집 범위, 이탈 정의와 모델 입력 피처의 생성 기준을 설명합니다.</p>
        </div>
        <div className="header-badges">
          <span className="demo-badge">실제 배치 데이터</span>
          <span className="cutoff-badge">▣ 최대 90일 피처 + 예측 30일</span>
        </div>
      </header>

      <section className="definition-banner">
        <span className="definition-icon">30</span>
        <div>
          <p>프로젝트 이탈 정의</p>
          <strong>기준일 이후 30일 동안 대상 게임 모드의 추가 경기 기록이 없는 사용자</strong>
          <small>Riot의 공식 이탈 기준이 아니며, 로그인 여부나 계정 탈퇴를 의미하지 않습니다.</small>
        </div>
      </section>

      <section className="panel data-definition-panel">
        <div className="panel-title"><h2>진성 활동 고객 분류</h2><span className="panel-chip">MODEL COHORT</span></div>
        <p className="panel-footnote">전체 수집 사용자 중 최근에도 실제 플레이가 있고, 직전 기간에도 충분한 활동이 확인된 사용자만 이탈 예측 대상에 포함했습니다.</p>
        <div className="cohort-rule-grid">
          <div><b>포함</b><strong>games_prev30d ≥ 4</strong><span>기준일 이전 30일에 4경기 이상</span></div>
          <div><b>포함</b><strong>games_30d &gt; 0</strong><span>기준일 직전 30일에 1경기 이상</span></div>
          <div className="excluded"><b>제외</b><strong>둘 중 하나라도 미충족</strong><span>신규·저활동·우연 유입 사용자는 별도 분석</span></div>
        </div>
        <table className="data-table cohort-table"><thead><tr><th>구분</th><th>인원</th><th>목적</th></tr></thead><tbody><tr><td>진성 활동 고객</td><td>2,381명</td><td>CatBoost 이탈 예측 대상</td></tr><tr><td>30일 이탈자</td><td>363명</td><td>기준일 이후 30일 무경기</td></tr><tr><td>관측 이탈률</td><td>15.25%</td><td>배치 성과 기준</td></tr></tbody></table>
      </section>

      <section className="metric-grid four" aria-label="데이터 개요">
        <article className="metric-card"><span>전체 수집 사용자</span><strong>9,879명</strong><small>배치 통합·중복 정리 후</small></article>
        <article className="metric-card"><span>진성 활동 고객</span><strong>2,381명</strong><small>CatBoost 분석 대상</small></article>
        <article className="metric-card"><span>피처 참조 범위</span><strong>최대 90일</strong><small>30일 비교 구간 + 90일 활동량·최근 20경기 요약</small></article>
        <article className="metric-card"><span>예측 기간</span><strong>30일</strong><small>기준일 이후 경기 여부</small></article>
      </section>

      <section className="content-grid">
        <article className="panel span-12">
          <div className="panel-title"><h2>데이터 파이프라인</h2><span className="panel-chip">수집 → 학습 데이터</span></div>
          <div className="pipeline-flow">
            <div><b>01</b><strong>배치 데이터 수집</strong><small>여러 수집 배치의 사용자·경기 이력 통합</small></div><i>→</i>
            <div><b>02</b><strong>사용자 키 정리</strong><small>team_id + player_id 기준 중복 확인</small></div><i>→</i>
            <div><b>03</b><strong>경기 수집</strong><small>목록·상세·모드 저장</small></div><i>→</i>
            <div><b>04</b><strong>피처 생성</strong><small>최대 90일 활동량·최근 경기 요약</small></div><i>→</i>
            <div><b>05</b><strong>라벨 검증</strong><small>이후 30일 경기 확인</small></div>
          </div>
        </article>

        <article className="panel span-12">
          <div className="panel-title"><div><h2>솔로랭크 포지션별 월간 변화</h2><p className="panel-footnote">Transformer 경기 이력에서 `RANKED_SOLO`만 추려 TOP·JUNGLE 등 포지션별 평균 KDA와 경기시간을 집계합니다.</p></div><span className="panel-chip">{positionEda ? `${positionEda.months_available.length}개월 관측` : '불러오는 중'}</span></div>
          <div className="table-scroll">
            <table className="data-table"><thead><tr><th>월</th><th>포지션</th><th>경기 수</th><th>평균 KDA</th><th>평균 경기시간</th><th>승률</th></tr></thead><tbody>{(positionEda?.items ?? []).map((row) => <tr key={`${row.month}-${row.position}`}><td>{row.month}</td><td>{row.position}</td><td>{row.matches.toLocaleString()}</td><td>{row.avg_kda.toFixed(2)}</td><td>{row.avg_duration_min.toFixed(1)}분</td><td>{(row.win_rate * 100).toFixed(1)}%</td></tr>)}</tbody></table>
          </div>
          <p className="panel-footnote">현재 시퀀스 데이터 범위는 2026-05-03~2026-07-31로 약 3개월입니다. 4개월 비교는 다음 수집 배치가 추가된 뒤 자동으로 확장됩니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>피처 구성</h2></div>
          <div className="table-scroll">
            <table className="data-table feature-table">
              <thead><tr><th>분류</th><th>대표 피처</th><th>의미</th></tr></thead>
              <tbody>
                {featureGroups.map((group) => (
                  <tr key={group.category}><td><span className="category-pill">{group.category}</span></td><td>{group.examples}</td><td>{group.reason}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel span-12">
          <div className="panel-title"><h2>생존분석 확장 데이터</h2><span className="panel-chip demo">합성 데이터</span></div>
          <p>실제 장기 관찰 라벨이 없어 진성 고객 피처에 가상 이벤트 시점을 붙여 Cox 모델을 실험했습니다. 합성 30일 이벤트율을 실제 코호트의 30일 무경기율(15.25%)에 맞췄기 때문에, 평균 30일 이벤트 미도달 비율은 대략 85% 안팎으로 보입니다. 이는 실제 고객의 재접속 확률이 아닙니다.</p>
          <table className="data-table"><thead><tr><th>항목</th><th>값</th><th>설명</th></tr></thead><tbody><tr><td>사용자</td><td>2,381명</td><td>실제 피처 분포를 합성 데이터 생성에 활용</td></tr><tr><td>합성 30일 이벤트율</td><td>15.20%</td><td>실제 관측 비율 15.25%를 생성 목표로 사용</td></tr><tr><td>Cox concordance</td><td>0.762</td><td>가정으로 생성한 합성 이벤트 순위에 대한 점수이며 실제 예측력 검증이 아님</td></tr><tr><td>운영 사용</td><td>보류</td><td>실제 후속 경기 로그로 라벨을 만들고 별도 검증해야 함</td></tr></tbody></table>
          <p className="panel-footnote">합성 이벤트 시점은 기존 churn 라벨과 활동 피처를 이용한 규칙으로 생성했습니다. Cox 모델이 그 규칙을 재현하는지 보는 실험이므로, 높은 생존 비율이나 C-index를 실제 서비스 성능으로 해석하면 안 됩니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>기간 분리 원칙</h2></div>
          <div className="timeline-card">
            <div className="timeline-labels"><span>최대 T-90일</span><span>기준일 T</span><span>T+30일</span></div>
            <div className="timeline-bar"><span>입력 피처 관찰</span><span>이탈 라벨 확인</span></div>
            <ul>
              <li>피처는 최대 90일 이전 기록, 라벨은 기준일 이후 30일로 분리</li>
              <li>기준일 이후 정보는 모델 입력에서 제외</li>
              <li>수집 실패와 실제 무경기를 별도 상태로 관리</li>
            </ul>
          </div>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>식별자와 모델 입력</h2><span className="panel-chip">개인 식별값 미사용</span></div>
          <p>화면에는 수집 데이터에 저장된 `player_id`를 분석용 식별자로 표시합니다. 현재 자료에서 이 값이 Riot PUUID임을 확인할 수 없으므로 PUUID라고 부르지 않습니다. 수집팀 간 충돌 방지를 위해 내부 조회 키는 `team_id:player_id` 조합을 사용합니다.</p>
          <p className="panel-footnote">CatBoost 입력은 사용자별 활동·경기 요약 피처입니다. 사용자 ID와 team_id는 조회용이며 학습 피처가 아닙니다. 시드 파일의 티어는 진성 고객 2,381명 중 일부(792명)만 매칭되고 수집 시점도 불명확해 이번 모델에서 제외했습니다.</p>
        </article>

        <article className="panel span-6">
          <div className="panel-title"><h2>데이터 품질 기준</h2></div>
          <ul className="quality-checks">
            <li><span>✓</span><div><b>중복 제거</b><small>팀·배치 간 동일 사용자와 matchId 확인</small></div></li>
            <li><span>✓</span><div><b>수집 완전성</b><small>오류·빈 응답·실제 무경기를 구분</small></div></li>
            <li><span>✓</span><div><b>시간 누수 방지</b><small>기준일 이전 값만 피처로 사용</small></div></li>
            <li><span>✓</span><div><b>스키마 검증</b><small>컬럼 타입·범위·결측 처리 기록</small></div></li>
          </ul>
        </article>
      </section>
    </>
  )
}
