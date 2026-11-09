import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/authContext'
import { ROLE_LABEL } from '../utils/labels'
import { navItems } from './nav'
import { NotificationBell } from './NotificationBell'
import { UnreadProvider } from './UnreadProvider'

export function AppShell() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [signingOut, setSigningOut] = useState(false)
  const location = useLocation()
  const mainRef = useRef<HTMLElement>(null)

  useEffect(() => {
    setMenuOpen(false)
  }, [location.pathname])

  if (!user) return null

  async function signOut() {
    setSigningOut(true)
    try {
      await logout()
    } finally {
      setSigningOut(false)
    }
  }

  return (
    <UnreadProvider>
      <a className="skip-link" href="#main" onClick={() => mainRef.current?.focus()}>
        Skip to main content
      </a>
      <div className="shell">
        <aside className={menuOpen ? 'sidebar sidebar-open' : 'sidebar'}>
          <div className="brand">
            <span className="brand-name">InfraDesk</span>
          </div>
          <nav id="primary-nav" aria-label="Main">
            <ul className="nav-list">
              {navItems(user.role).map((item) => (
                <li key={item.to}>
                  <NavLink to={item.to} end={item.end} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <p className="sidebar-foot">{ROLE_LABEL[user.role]} workspace</p>
        </aside>
        <div className="shell-main">
          <div className="topbar">
            <button
              type="button"
              className="btn menu-button"
              aria-expanded={menuOpen}
              aria-controls="primary-nav"
              onClick={() => setMenuOpen((o) => !o)}
            >
              Menu
            </button>
            <span className="topbar-spacer" />
            <NotificationBell role={user.role} />
            <div className="whoami">
              <span className="whoami-name">{user.display_name}</span>
              <span className="whoami-role">{ROLE_LABEL[user.role]}</span>
            </div>
            <button type="button" className="btn btn-small" onClick={signOut} disabled={signingOut}>
              {signingOut ? 'Signing out...' : 'Sign out'}
            </button>
          </div>
          <main id="main" ref={mainRef} tabIndex={-1} className="content">
            <Outlet />
          </main>
        </div>
      </div>
    </UnreadProvider>
  )
}
