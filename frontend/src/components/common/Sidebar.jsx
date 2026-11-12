
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  GitBranch,
  MessageSquare,
  FileText,
  Settings,
  LogOut,
  Network,
  ChevronLeft,
} from 'lucide-react'

import useAuth from '../../hooks/useAuth'
import './Sidebar.css'

function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const navigationItems = [
    {
      label: 'Overview',
      path: '/dashboard',
      icon: LayoutDashboard,
    },
    {
      label: 'My Projects',
      path: '/dashboard/projects',
      icon: FolderKanban,
    },
    {
      label: 'Dependency Graph',
      path: '/dashboard/graph',
      icon: GitBranch,
    },
    {
      label: 'AI Code Chat',
      path: '/dashboard/chat',
      icon: MessageSquare,
    },
    {
      label: 'Documentation',
      path: '/dashboard/documentation',
      icon: FileText,
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

          return (
            <NavLink
              key={item.path}
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
          className={({ isActive }) =>
            `sidebar-nav-link ${isActive ? 'active' : ''}`
          }
        >
          <Settings size={19} />
          <span>Settings</span>
        </NavLink>

        <div className="sidebar-user">
          <div className="sidebar-user-avatar">
            {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
          </div>

          <div className="sidebar-user-info">
            <strong>{user?.full_name || 'User'}</strong>
            <span>{user?.email || 'Welcome to CodeAtlas'}</span>
          </div>
        </div>

        <button
          className="sidebar-logout-button"
          onClick={handleLogout}
        >
          <LogOut size={18} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
