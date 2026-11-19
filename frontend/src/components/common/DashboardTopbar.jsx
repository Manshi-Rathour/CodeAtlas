import { Link } from 'react-router-dom'

import useAuth from '../../hooks/useAuth'

import './DashboardTopbar.css'

function DashboardTopbar({ children }) {
  const { user } = useAuth()

  const firstName = user?.full_name?.split(' ')[0] || 'Developer'

  return (
    <header className="dashboard-topbar">
      <div className="dashboard-breadcrumb">{children}</div>

      <Link
        to="/dashboard/profile"
        className="dashboard-topbar-right"
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
    </header>
  )
}

export default DashboardTopbar
