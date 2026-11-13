import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  FolderOpen,
  FileCode2,
  GitBranch,
  CalendarDays,
  ExternalLink,
  Search,
  LoaderCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import projectService from '../services/projectService'

import './ProjectOverviewPage.css'

function ProjectOverviewPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [project, setProject] = useState(null)
  const [fileData, setFileData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchProjectData = async () => {
    setIsLoading(true)
    setError('')

    try {
      const [projectResponse, filesResponse] = await Promise.all([
        projectService.getProject(projectId),
        projectService.getProjectFiles(projectId, {
          page: 1,
          page_size: 1,
        }),
      ])

      setProject(projectResponse)
      setFileData(filesResponse)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load project information.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchProjectData()
  }, [projectId])

  const getSourceLabel = (sourceType) => {
    if (sourceType === 'github') return 'GitHub Repository'
    if (sourceType === 'zip') return 'ZIP Upload'
    return 'Manual Project'
  }

  const formatDate = (date) => {
    if (!date) return 'Not available'

    return new Date(date).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  }

  if (isLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main project-overview-main">
          <div className="project-page-loading">
            <LoaderCircle size={32} className="spin" />
            <p>Loading project information...</p>
          </div>
        </main>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main project-overview-main">
          <div className="project-page-error">
            <AlertCircle size={32} />
            <h2>Unable to load project</h2>
            <p>{error || 'Project not found.'}</p>
            <button onClick={fetchProjectData}>
              <RefreshCw size={16} />
              Try Again
            </button>
            <button onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </button>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main project-overview-main">
        <header className="dashboard-topbar">
          <div className="dashboard-breadcrumb">
            Workspace <span>/</span> Projects <span>/</span> {project.name}
          </div>
        </header>

        <div className="project-overview-content">
          <button
            className="project-back-button"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft size={17} />
            Back to Dashboard
          </button>

          <section className="project-hero">
            <div className="project-hero-main">
              <div className="project-hero-icon">
                <FolderOpen size={30} />
              </div>

              <div>
                <div className="project-source-label">
                  <GitBranch size={14} />
                  {getSourceLabel(project.source_type)}
                </div>

                <h1>{project.name}</h1>

                <p>
                  {project.description ||
                    'Explore your codebase and discover its structure.'}
                </p>
              </div>
            </div>

            <span
              className={`project-status-badge status-${project.status}`}
            >
              {project.status}
            </span>
          </section>

          <section className="project-overview-stats">
            <div className="project-overview-stat">
              <div className="project-stat-icon">
                <FileCode2 size={21} />
              </div>
              <span>Total Files</span>
              <strong>{fileData?.total ?? 0}</strong>
            </div>

            <div className="project-overview-stat">
              <div className="project-stat-icon">
                <CalendarDays size={21} />
              </div>
              <span>Created On</span>
              <strong className="project-date-value">
                {formatDate(project.created_at)}
              </strong>
            </div>

            <div className="project-overview-stat">
              <div className="project-stat-icon">
                <GitBranch size={21} />
              </div>
              <span>Import Source</span>
              <strong className="project-source-value">
                {getSourceLabel(project.source_type)}
              </strong>
            </div>
          </section>

          <section className="project-overview-section">
            <div>
              <h2>Explore your codebase</h2>
              <p>
                Browse project files and inspect source code.
              </p>
            </div>

            <button
              className="open-explorer-button"
              onClick={() =>
                navigate(`/dashboard/projects/${project.id}/files`)
              }
            >
              <Search size={17} />
              Open File Explorer
              <ExternalLink size={15} />
            </button>
          </section>

          {project.repository_url && (
            <section className="project-repository-section">
              <div>
                <GitBranch size={19} />
                <span>GitHub Repository</span>
              </div>

              <a
                href={project.repository_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {project.repository_url}
                <ExternalLink size={14} />
              </a>
            </section>
          )}
        </div>
      </main>
    </div>
  )
}

export default ProjectOverviewPage
