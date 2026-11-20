import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  LogOut,
  Network,
} from 'lucide-react'

import useAuth from '../../hooks/useAuth'
import './Sidebar.css'

function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  // Project tools are opened from the project tabs on each project page.
  const navigationItems = [
    {
      label: 'Overview',
      path: '/dashboard',
      icon: LayoutDashboard,
      available: true,
    },
    {
      label: 'My Projects',
      path: '/dashboard/projects',
      icon: FolderKanban,
      available: true,
    },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="dashboard-sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <Network size={23} />
        </div>

        <div className="sidebar-brand-text">
          <h2>CodeAtlas</h2>
          <span>AI Code Intelligence</span>
        </div>
      </div>

      <div className="sidebar-section-label">
        WORKSPACE
      </div>

      <nav className="sidebar-navigation">
        {navigationItems.map((item) => {
          const Icon = item.icon

          if (!item.available) {
            return (
              <div
                key={item.label}
                className="sidebar-nav-link sidebar-nav-disabled"
                aria-disabled="true"
              >
                <Icon size={19} />
                <span>{item.label}</span>
                <span className="sidebar-coming-soon">
                  Soon
                </span>
              </div>
            )
          }

          return (
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === '/dashboard'}
              className={({ isActive }) =>
                `sidebar-nav-link ${isActive ? 'active' : ''}`
              }
            >
              <Icon size={19} />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      <div className="sidebar-bottom">
        <NavLink
          to="/dashboard/profile"
          className="sidebar-user"
          title="Open your profile"
        >
          <div className="sidebar-user-avatar">
            {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
          </div>

          <div className="sidebar-user-info">
            <strong>{user?.full_name || 'User'}</strong>
            <span>{user?.email || 'Welcome to CodeAtlas'}</span>
          </div>
        </NavLink>

        <button
          className="sidebar-logout-button"
          onClick={handleLogout}
        >
          <LogOut size={18} />
          <span>Sign out</span>
        </button>

        {/* <div className="sidebar-version">
          CodeAtlas
        </div> */}
      </div>
    </aside>
  )
}

export default Sidebar
