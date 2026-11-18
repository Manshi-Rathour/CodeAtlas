import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  FileText,
  LoaderCircle,
  RefreshCw,
  Sparkles,
  CalendarDays,
  AlertCircle,
  Wand2,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import ProjectNav from '../components/common/ProjectNav'
import MarkdownViewer from '../components/documentation/MarkdownViewer'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'

import projectService from '../services/projectService'
import documentationService from '../services/documentationService'

import './DocumentationPage.css'

function DocumentationPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [project, setProject] = useState(null)
  const [documentation, setDocumentation] = useState(null)

  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)

  const [error, setError] = useState('')
  const [generationError, setGenerationError] = useState('')

  const loadPage = async () => {
    setIsLoading(true)
    setError('')

    try {
      const [projectResponse, statusResponse] = await Promise.all([
        projectService.getProject(projectId),
        documentationService.getStatus(projectId),
      ])

      setProject(projectResponse)

      if (statusResponse.exists) {
        const documentationResponse =
          await documentationService.getDocumentation(projectId)

        setDocumentation(documentationResponse)
      } else {
        setDocumentation(null)
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load project documentation.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadPage()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const handleGenerate = async () => {
    setIsGenerating(true)
    setGenerationError('')

    try {
      const response =
        await documentationService.generateDocumentation(projectId)

      setDocumentation(response)
    } catch (err) {
      setGenerationError(
        err.response?.data?.detail ||
        'Documentation generation failed. Please try again.'
      )
    } finally {
      setIsGenerating(false)
    }
  }

  const formatDate = (date) => {
    if (!date) return 'Unknown'

    return new Date(date).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main documentation-page-main">
          <LoadingSpinner label="Loading documentation..." />
        </main>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main documentation-page-main">
          <div className="documentation-page-content">
            <ErrorMessage
              title="Unable to load documentation"
              message={error || 'Project not found.'}
              onRetry={loadPage}
            />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main documentation-page-main">
        <DashboardTopbar>
          Workspace <span>/</span> Projects <span>/</span>
          {project.name} <span>/</span> Documentation
        </DashboardTopbar>

        <div className="documentation-page-content">
          <button
            className="project-back-button"
            onClick={() => navigate(`/dashboard/projects/${projectId}`)}
          >
            <ArrowLeft size={17} />
            Back to Project
          </button>

          <ProjectNav projectId={projectId} />

          <section className="documentation-heading">
            <div>
              <div className="documentation-eyebrow">
                <Sparkles size={16} />
                AI DOCUMENTATION
              </div>

              <h1>{project.name} Documentation</h1>

              <p>
                Generate developer documentation from the analyzed
                files, symbols and dependencies of this project.
              </p>
            </div>

            <div className="documentation-actions">
              {documentation && (
                <button
                  className="documentation-refresh"
                  onClick={loadPage}
                  disabled={isGenerating}
                >
                  <RefreshCw size={15} />
                  Refresh
                </button>
              )}

              <button
                className="documentation-generate"
                onClick={handleGenerate}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <LoaderCircle size={16} className="spin" />
                ) : (
                  <Wand2 size={16} />
                )}

                {isGenerating
                  ? 'Generating...'
                  : documentation
                    ? 'Regenerate'
                    : 'Generate Documentation'}
              </button>
            </div>
          </section>

          {generationError && (
            <div className="documentation-error">
              <AlertCircle size={17} />
              {generationError}
            </div>
          )}

          {isGenerating && (
            <div className="documentation-progress">
              <LoaderCircle size={19} className="spin" />

              <div>
                <strong>Writing documentation from your codebase</strong>
                <span>
                  It can take up to a minute. Keep this tab
                  open while the model reads the analyzed context.
                </span>
              </div>
            </div>
          )}

          {documentation ? (
            <article className="documentation-card">
              <header className="documentation-card-header">
                <div>
                  <FileText size={19} />
                  <div>
                    <h2>Project Documentation</h2>
                    <span>Generated Markdown</span>
                  </div>
                </div>

                <div className="documentation-meta">
                  <CalendarDays size={14} />
                  Updated {formatDate(documentation.updated_at)}
                </div>
              </header>

              <div className="documentation-body">
                <MarkdownViewer content={documentation.content} />
              </div>
            </article>
          ) : (
            !isGenerating && (
              <EmptyState
                icon={FileText}
                title="No documentation generated yet"
                message="CodeAtlas will use this project's analyzed files, functions, classes, dependencies and detected technologies to write documentation. Nothing is invented beyond the available code context."
                action={
                  <button onClick={handleGenerate} disabled={isGenerating}>
                    <Wand2 size={15} />
                    Generate Documentation
                  </button>
                }
              />
            )
          )}
        </div>
      </main>
    </div>
  )
}

export default DocumentationPage
