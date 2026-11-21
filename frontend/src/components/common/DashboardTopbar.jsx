import { useEffect, useState } from 'react'
import {
  Link,
  NavLink,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import {
  LogOut,
  Menu,
  Network,
  X,
} from 'lucide-react'

import useAuth from '../../hooks/useAuth'
import { workspaceNavigation } from '../../utils/navigation'

import './DashboardTopbar.css'

function DashboardTopbar({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // The menu is tied to the path it was opened on, so navigating
  // from the breadcrumb automatically closes it.
  const [openPath, setOpenPath] = useState(null)
  const menuOpen = openPath === location.pathname

  const closeMenu = () => setOpenPath(null)

  const toggleMenu = () => {
    setOpenPath(menuOpen ? null : location.pathname)
  }

  const handleLogout = () => {
    closeMenu()
    logout()
    navigate('/login', { replace: true })
  }

  // Allow closing the menu with the Escape key.
  useEffect(() => {
    if (!menuOpen) {
      return undefined
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setOpenPath(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [menuOpen])

  const firstName = user?.full_name?.split(' ')[0] || 'Developer'

  return (
    <header className="dashboard-topbar">
      <div className="dashboard-topbar-left">
        <Link
          to="/dashboard"
          className="dashboard-mobile-brand"
          aria-label="CodeAtlas dashboard"
        >
          <span className="dashboard-mobile-brand-icon">
            <Network size={21} />
          </span>

          <span className="dashboard-mobile-brand-text">
            <strong>CodeAtlas</strong>
            <small>AI Code Intelligence</small>
          </span>
        </Link>

        <div className="dashboard-breadcrumb">{children}</div>
      </div>

      <div className="dashboard-topbar-right">
        <Link
          to="/dashboard/profile"
          className="dashboard-topbar-profile"
          title="Open your profile"
        >
          <span className="dashboard-user-email">
            {user?.email || ''}
          </span>

          <span
            className="dashboard-topbar-avatar"
            title={user?.full_name || 'Signed-in user'}
          >
            {firstName.charAt(0).toUpperCase()}
          </span>
        </Link>

        <button
          type="button"
          className="dashboard-menu-button"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          aria-controls="dashboard-mobile-menu"
          onClick={toggleMenu}
        >
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {menuOpen && (
        <div
          className="dashboard-mobile-menu"
          id="dashboard-mobile-menu"
        >
          <div className="dashboard-mobile-label">
            WORKSPACE
          </div>

          <nav className="dashboard-mobile-nav">
            {workspaceNavigation.map((item) => {
              const Icon = item.icon

              return (
                <NavLink
                  key={item.label}
                  to={item.path}
                  end={item.path === '/dashboard'}
                  className={({ isActive }) =>
                    `dashboard-mobile-link ${isActive ? 'active' : ''}`
                  }
                  onClick={closeMenu}
                >
                  <Icon size={19} />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>

          <div className="dashboard-mobile-account">
            <Link
              to="/dashboard/profile"
              className="dashboard-mobile-user"
              title="Open your profile"
              onClick={closeMenu}
            >
              <span className="dashboard-mobile-avatar">
                {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
              </span>

              <span className="dashboard-mobile-user-info">
                <strong>{user?.full_name || 'User'}</strong>
                <span>
                  {user?.email || 'Welcome to CodeAtlas'}
                </span>
              </span>
            </Link>

            <button
              type="button"
              className="dashboard-mobile-logout"
              onClick={handleLogout}
            >
              <LogOut size={18} />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </header>
  )
}

export default DashboardTopbar
