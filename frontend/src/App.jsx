import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import AllProjectsPage from './pages/AllProjectsPage'
import CreateProjectPage from './pages/CreateProjectPage'
import ProjectOverviewPage from './pages/ProjectOverviewPage'
import FileExplorerPage from './pages/FileExplorerPage'

import ProtectedRoute from './components/common/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />

            <Route
              path="/dashboard/projects"
              element={<AllProjectsPage />}
            />

            <Route
              path="/dashboard/projects/new"
              element={<CreateProjectPage />}
            />

            <Route
              path="/dashboard/projects/:projectId"
              element={<ProjectOverviewPage />}
            />

            <Route
              path="/dashboard/projects/:projectId/files"
              element={<FileExplorerPage />}
            />
          </Route>

          {/* Unknown routes */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
