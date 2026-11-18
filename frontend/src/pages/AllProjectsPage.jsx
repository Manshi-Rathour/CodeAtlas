import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FolderKanban,
  Plus,
  Search,
  RefreshCw,
  ArrowLeft,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import ProjectCard from '../components/dashboard/ProjectCard'
import projectService from '../services/projectService'

import './DashboardPage.css'
import './AllProjectsPage.css'

function AllProjectsPage() {
  const navigate = useNavigate()

  const [projects, setProjects] = useState([])
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const handleProjectDeleted = (deletedProjectId) => {
    setProjects((currentProjects) =>
      currentProjects.filter(
        (project) => project.id !== deletedProjectId
      )
    )
  }

  const fetchProjects = async () => {
    try {
      setIsLoading(true)
      setError('')

      const projectData = await projectService.getProjects()

      const projectsWithFiles = await Promise.all(
        projectData.map(async (project) => {
          try {
            const fileData = await projectService.getProjectFiles(
              project.id,
              { page: 1, page_size: 1 }
            )

            return {
              ...project,
              total_files: fileData.total ?? 0,
            }
          } catch {
            return {
              ...project,
              total_files: 0,
            }
          }
        })
      )

      setProjects(projectsWithFiles)
    } catch (err) {
      console.error('Projects loading error:', err)

      setError(
        err.response?.data?.detail ||
        'Unable to load your projects. Please try again.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const filteredProjects = useMemo(() => {
    const searchTerm = search.trim().toLowerCase()

    if (!searchTerm) return projects

    return projects.filter((project) =>
      [
        project.name,
        project.description,
        project.source_type,
        project.status,
      ]
        .filter(Boolean)
        .some((value) =>
          value.toLowerCase().includes(searchTerm)
        )
    )
  }, [projects, search])

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main">
        <DashboardTopbar>
          <span>Workspace</span>
          <span className="breadcrumb-separator">/</span>
          <strong>My Projects</strong>
        </DashboardTopbar>

        <div className="dashboard-content all-projects-content">

          <button
            className="all-projects-back-button"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft size={17} />
            Back to Overview
          </button>

          <section className="all-projects-heading">
            <div>
              <div className="dashboard-eyebrow">
                <FolderKanban size={15} />
                YOUR WORKSPACE
              </div>

              <h1>My Projects</h1>

              <p>
                Manage and explore all your imported codebases
                in one place.
              </p>
            </div>

            <button
              className="dashboard-primary-button"
              onClick={() => navigate('/dashboard/projects/new')}
            >
              <Plus size={18} />
              Import Project
            </button>
          </section>

          <section className="all-projects-toolbar">
            <div className="all-projects-count">
              <strong>{projects.length}</strong>
              <span>
                {projects.length === 1 ? 'Project' : 'Projects'} in your workspace
              </span>
            </div>

            <div className="all-projects-actions">
              <form
                className="all-projects-search"
                onSubmit={(event) => {
                  event.preventDefault()
                  setSearch(searchInput.trim())
                }}
              >
                <Search size={17} />

                <input
                  type="text"
                  placeholder="Search projects..."
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                />
              </form>

              <button
                className="all-projects-refresh"
                onClick={() => {
                  setSearchInput('')
                  setSearch('')
                  fetchProjects()
                }}
                disabled={isLoading}
                title="Refresh projects"
              >
                <RefreshCw
                  size={17}
                  className={isLoading ? 'refresh-spinning' : ''}
                />
              </button>
            </div>
          </section>

          {isLoading ? (
            <div className="dashboard-loading">
              <div className="dashboard-loading-spinner"></div>
              <p>Loading your projects...</p>
            </div>
          ) : error ? (
            <div className="dashboard-error">
              <p>{error}</p>
              <button onClick={fetchProjects}>
                Try Again
              </button>
            </div>
          ) : projects.length === 0 ? (
            <div className="dashboard-empty-state">
              <div className="dashboard-empty-icon">
                <FolderKanban size={30} />
              </div>

              <h3>No projects yet</h3>

              <p>
                Import your first GitHub repository or ZIP project
                to start exploring your codebase.
              </p>

              <button
                className="dashboard-primary-button"
                onClick={() => navigate('/dashboard/projects/new')}
              >
                <Plus size={18} />
                Import Your First Project
              </button>
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="dashboard-empty-state">
              <div className="dashboard-empty-icon">
                <Search size={30} />
              </div>

              <h3>No matching projects</h3>

              <p>
                We couldn't find any projects matching "{search}".
                Try a different search term.
              </p>

              <button
                className="dashboard-primary-button"
                onClick={() => {
                  setSearchInput('')
                  setSearch('')
                }}
              >
                Clear Search
              </button>
            </div>
          ) : (
            <section className="dashboard-project-grid all-projects-grid">
              {filteredProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onDelete={handleProjectDeleted}
                />
              ))}
            </section>
          )}

        </div>
      </main>
    </div>
  )
}

export default AllProjectsPage
