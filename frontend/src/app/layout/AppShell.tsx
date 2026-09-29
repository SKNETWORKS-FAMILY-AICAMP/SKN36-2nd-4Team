import { NavLink, Outlet } from 'react-router-dom'
import { Icon, type IconName } from '../../components/common/Icon'
import { BrandEmblem } from './BrandEmblem'

const navigationItems: Array<{ to: string; icon: IconName; label: string }> = [
  { to: '/', icon: 'home', label: '전체 현황' },
  { to: '/risk-users', icon: 'risk-user', label: '위험 사용자' },
  { to: '/users', icon: 'user-detail', label: '사용자 상세' },
  { to: '/model', icon: 'analytics', label: '모델 설명' },
  { to: '/data', icon: 'document', label: '데이터 설명' },
  { to: '/survival', icon: 'analytics', label: '생존분석 확장' },
]

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">
            <BrandEmblem />
          </span>
          <span className="brand-copy">
            <strong>소환사의 여정</strong>
            <small>이탈 예측 프로젝트</small>
          </span>
        </div>

        <nav className="nav-list" aria-label="주 메뉴">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `nav-link${isActive ? ' active' : ''}`
              }
            >
              <Icon name={item.icon} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <p className="sidebar-note">
          데이터로,<br />더 오래 함께하는<br />게임의 미래를.
        </p>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
