import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { BrandEmblem } from '../../app/layout/BrandEmblem'
import './HomePage.css'

const menuItems = [
  { to: '/dashboard', no: '01', title: '전체 현황', subtitle: 'Overview' },
  { to: '/risk-users', no: '02', title: '위험 사용자', subtitle: 'Risk Users' },
  { to: '/users', no: '03', title: '사용자 상세', subtitle: 'User Detail' },
  { to: '/model', no: '04', title: '모델 설명', subtitle: 'Model' },
  { to: '/data', no: '05', title: '데이터 설명', subtitle: 'Data' },
  { to: '/survival', no: '06', title: '생존분석 확장', subtitle: 'Survival' },
] as const

export function HomePage() {
  const introRef = useRef<HTMLElement>(null)
  const introVideoRef = useRef<HTMLVideoElement>(null)
  const [playIntro, setPlayIntro] = useState(false)

  useEffect(() => {
    const section = introRef.current
    if (!section) return
    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) setPlayIntro(true)
    }, { threshold: 0.2 })
    observer.observe(section)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const video = introVideoRef.current
    if (!playIntro || !video) return
    video.src = '/home-intro.mp4'
    void video.play().catch(() => undefined)
  }, [playIntro])

  return (
    <div className="home-scroll-page">
      <section className="video-opening" aria-label="프로젝트 오프닝 영상">
        <video className="video-opening-media" autoPlay muted loop playsInline preload="metadata" poster="/dashboard-background-poster.jpg">
          <source src="/opening-video.webm" type="video/webm" />
        </video>
        <div className="video-opening-shade" aria-hidden="true" />
        <div className="video-opening-brand">
          <span className="video-opening-emblem"><BrandEmblem /></span>
          <span><b>SKN36 · 2ND PROJECT</b><small>TEAM 4 · USER CHURN ANALYTICS</small></span>
        </div>
        <a className="video-scroll-cue" href="#project-home" aria-label="프로젝트 메인 화면으로 스크롤">
          <span>SCROLL TO EXPLORE</span><i aria-hidden="true">⌄</i>
        </a>
      </section>

      <section id="project-home" className="intro-page" ref={introRef}>
        <video ref={introVideoRef} className="intro-video" muted loop playsInline preload="none" poster="/dashboard-background-poster.jpg" aria-hidden="true" />
        <div className="intro-overlay" aria-hidden="true" />
        <div className="intro-vignette" aria-hidden="true" />
        <div className="intro-particles" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /></div>

        <header className="intro-topbar">
          <div className="intro-brand">
            <span className="intro-emblem"><BrandEmblem /></span>
            <span><b>SKN36 · 2ND PROJECT</b><small>TEAM 4</small></span>
          </div>
          <span className="intro-status">CHURN PREDICTION SYSTEM · 2026</span>
        </header>

        <div className="intro-center">
          <span className="intro-kicker">LEAGUE OF LEGENDS USER CHURN ANALYTICS</span>
          <h1>MIA 보호소</h1>
          <p>League of Legends 사용자 이탈 예측 대시보드</p>
          <span className="intro-line" aria-hidden="true" />
          <Link className="intro-start" to="/dashboard"><span>ENTER DASHBOARD</span><b>START</b></Link>
        </div>

        <nav className="intro-menu" aria-label="메인 화면 바로가기">
          {menuItems.map((item) => <Link key={item.to} to={item.to} className="intro-menu-item">
            <span className="intro-menu-no">{item.no}</span>
            <span className="intro-menu-copy"><b>{item.title}</b><small>{item.subtitle}</small></span>
            <span className="intro-menu-arrow">↗</span>
          </Link>)}
        </nav>
        <footer className="intro-footer">
          <span>DATA CUTOFF · 2026.08.01</span>
          <span>수집 목표 10,000명 · 실제 수집 9,879명</span>
        </footer>
      </section>
    </div>
  )
}
