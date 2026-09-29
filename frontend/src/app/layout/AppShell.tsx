import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Icon, type IconName } from '../../components/common/Icon'
import { BrandEmblem } from './BrandEmblem'

const navigationItems: Array<{ to: string; icon: IconName; label: string }> = [
  { to: '/dashboard', icon: 'home', label: '전체 현황' },
  { to: '/risk-users', icon: 'risk-user', label: '위험 사용자' },
  { to: '/users', icon: 'user-detail', label: '사용자 상세' },
  { to: '/model', icon: 'analytics', label: '모델 성능' },
  { to: '/data', icon: 'document', label: '데이터 설명' },
  { to: '/survival', icon: 'analytics', label: '생존분석 확장' },
]

export function AppShell() {
  const isHome = useLocation().pathname === '/'
  return (
    <div className={`app-shell hud-shell${isHome ? ' home-shell' : ''}`}>
      {!isHome && <header className="hud-nav">
        <NavLink to="/" end className="hud-brand" aria-label="전체 현황으로 이동">
          <span className="hud-brand-emblem">
            <BrandEmblem />
          </span>
          <span className="hud-brand-copy">
            <strong>MIA 보호소</strong>
            <small>이탈 예측 프로젝트</small>
          </span>
        </NavLink>

        <nav className="hud-nav-list" aria-label="주 메뉴">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `hud-nav-link${isActive ? ' active' : ''}`
              }
            >
              <Icon name={item.icon} className="hud-nav-icon" />
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="hud-system-status" aria-label="시스템 상태">
          <span className="hud-status-dot" />
          <span><b>LIVE · 2026</b><small>CHURN ANALYTICS</small></span>
        </div>
      </header>}

      <main className={`main-content${isHome ? ' home-main' : ''}`}>
        <Outlet />
      </main>
    </div>
  )
}
