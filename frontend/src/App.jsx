import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import AllProjectsPage from './pages/AllProjectsPage'
import CreateProjectPage from './pages/CreateProjectPage'
import ProfilePage from './pages/ProfilePage'
import ProjectOverviewPage from './pages/ProjectOverviewPage'
import FileExplorerPage from './pages/FileExplorerPage'
import CodebaseChatPage from './pages/CodebaseChatPage'
import ArchitecturePage from './pages/ArchitecturePage'
import DocumentationPage from './pages/DocumentationPage'
import DependencyGraphPage from './pages/DependencyGraphPage'
import ApiExplorerPage from './pages/ApiExplorerPage'

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
              path="/dashboard/profile"
              element={<ProfilePage />}
            />

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

            <Route
              path="/dashboard/projects/:projectId/chat"
              element={<CodebaseChatPage />}
            />

            <Route
              path="/dashboard/projects/:projectId/architecture"
              element={<ArchitecturePage />}
            />

            <Route
              path="/dashboard/projects/:projectId/documentation"
              element={<DocumentationPage />}
            />

            <Route
              path="/dashboard/projects/:projectId/graph"
              element={<DependencyGraphPage />}
            />

            <Route
              path="/dashboard/projects/:projectId/apis"
              element={<ApiExplorerPage />}
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
