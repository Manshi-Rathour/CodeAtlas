import useAuth from '../../hooks/useAuth'

import './DashboardTopbar.css'

function DashboardTopbar({ children }) {
  const { user } = useAuth()

  const firstName = user?.full_name?.split(' ')[0] || 'Developer'

  return (
    <header className="dashboard-topbar">
      <div className="dashboard-breadcrumb">{children}</div>

      <div className="dashboard-topbar-right">
        <span className="dashboard-user-email">
          {user?.email || ''}
        </span>

        <div
          className="dashboard-topbar-avatar"
          title={user?.full_name || 'Signed-in user'}
        >
          {firstName.charAt(0).toUpperCase()}
        </div>
      </div>
    </header>
  )
}

export default DashboardTopbar
