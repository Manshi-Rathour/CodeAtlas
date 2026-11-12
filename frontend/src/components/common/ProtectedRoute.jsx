
import { Navigate, Outlet } from 'react-router-dom'
import useAuth from '../../hooks/useAuth'

function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  // Wait until the application checks the saved login token.
  if (isLoading) {
    return (
      <div className="auth-loading-screen">
        <div className="auth-loading-spinner"></div>
        <p>Verifying your session...</p>
      </div>
    )
  }

  // Redirect unauthenticated users to the login page.
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Allow authenticated users to access the protected page.
  return <Outlet />
}

export default ProtectedRoute
