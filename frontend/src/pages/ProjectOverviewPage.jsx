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
  Play,
  Code2,
  Braces,
  Layers,
  Database,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import projectService from '../services/projectService'
import analysisService from '../services/analysisService'

import './ProjectOverviewPage.css'

function ProjectOverviewPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [project, setProject] = useState(null)
  const [fileData, setFileData] = useState(null)
  const [analysisData, setAnalysisData] = useState(null)

  const [isLoading, setIsLoading] = useState(true)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const [error, setError] = useState('')
  const [analysisError, setAnalysisError] = useState('')

  const fetchProjectData = async () => {
    setIsLoading(true)
    setError('')

    try {
      const [projectResponse, filesResponse, analysisResponse] =
        await Promise.all([
          projectService.getProject(projectId),
          projectService.getProjectFiles(projectId, {
            page: 1,
            page_size: 1,
          }),
          analysisService.getProjectAnalysis(projectId),
        ])

      setProject(projectResponse)
      setFileData(filesResponse)
      setAnalysisData(analysisResponse)
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

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true)
    setAnalysisError('')

    try {
      await analysisService.analyzeProject(projectId)

      const result =
        await analysisService.getProjectAnalysis(projectId)

      setAnalysisData(result)
    } catch (err) {
      setAnalysisError(
        err.response?.data?.detail ||
        'Unable to analyze this project.'
      )
    } finally {
      setIsAnalyzing(false)
    }
  }

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

  const symbols = analysisData?.symbols || []
  const chunks = analysisData?.chunks || []
  const dependencies = analysisData?.dependencies || []

  const functionCount = symbols.filter(
    (item) => item.type === 'function'
  ).length

  const methodCount = symbols.filter(
    (item) => item.type === 'method'
  ).length

  const classCount = symbols.filter(
    (item) => item.type === 'class'
  ).length

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

          {/* Project information */}
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

          {/* Project statistics */}
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


          {/* File explorer */}
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

          {/* GitHub repository */}
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

          {/* Codebase analysis */}
          <section className="analysis-section">
            <div className="analysis-header">
              <div>
                <div className="analysis-title-label">
                  <Code2 size={17} />
                  CODE INTELLIGENCE
                </div>

                <h2>Codebase Analysis</h2>

                <p>
                  Analyze your project to discover its functions,
                  classes, methods, and code structures.
                </p>
              </div>

              <button
                className="run-analysis-button"
                onClick={handleRunAnalysis}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? (
                  <LoaderCircle size={17} className="spin" />
                ) : (
                  <Play size={17} />
                )}

                {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
              </button>
            </div>

            {analysisError && (
              <div className="analysis-error">
                <AlertCircle size={17} />
                {analysisError}
              </div>
            )}

            {/* Analysis statistics */}
            <div className="analysis-stats">
              <div className="analysis-stat-card">
                <div className="analysis-stat-icon">
                  <Code2 size={21} />
                </div>
                <span>Functions</span>
                <strong>{functionCount}</strong>
              </div>

              <div className="analysis-stat-card">
                <div className="analysis-stat-icon">
                  <Braces size={21} />
                </div>
                <span>Methods</span>
                <strong>{methodCount}</strong>
              </div>

              <div className="analysis-stat-card">
                <div className="analysis-stat-icon">
                  <Layers size={21} />
                </div>
                <span>Classes</span>
                <strong>{classCount}</strong>
              </div>

              <div className="analysis-stat-card">
                <div className="analysis-stat-icon">
                  <Database size={21} />
                </div>
                <span>Code Chunks</span>
                <strong>{analysisData?.total_chunks ?? 0}</strong>
              </div>
            </div>

            {/* Extracted symbols */}
            <div className="analysis-results">
              <div className="analysis-results-heading">
                <div>
                  <h3>Extracted Symbols</h3>
                  <p>Functions, methods, and classes discovered in your code</p>
                </div>

                <span>{symbols.length} symbols</span>
              </div>

              {symbols.length === 0 ? (
                <div className="analysis-empty">
                  No symbols found. Run analysis to inspect your codebase.
                </div>
              ) : (
                <div className="analysis-list">
                  {symbols.map((symbol) => (
                    <div
                      className="analysis-item"
                      key={symbol.id}
                    >
                      <div className="analysis-item-main">
                        <Code2 size={17} />

                        <div>
                          <strong>{symbol.name}</strong>
                          <span>{symbol.file}</span>
                        </div>
                      </div>

                      <div className="analysis-item-meta">
                        <span className="analysis-type">
                          {symbol.type}
                        </span>

                        <span>
                          Lines {symbol.start_line}–{symbol.end_line}
                        </span>
                      </div>

                      {symbol.source_code && (
                        <details className="analysis-code-details">
                          <summary>View source code</summary>
                          <pre>
                            <code>{symbol.source_code}</code>
                          </pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Extracted code chunks */}
            <div className="analysis-results">
              <div className="analysis-results-heading">
                <div>
                  <h3>Code Chunks</h3>
                  <p>Structured HTML elements, CSS rules, and SQL statements</p>
                </div>

                <span>{chunks.length} chunks</span>
              </div>

              {chunks.length === 0 ? (
                <div className="analysis-empty">
                  No code chunks found yet.
                </div>
              ) : (
                <div className="analysis-list">
                  {chunks.map((chunk) => (
                    <div
                      className="analysis-item"
                      key={chunk.id}
                    >
                      <div className="analysis-item-main">
                        <Database size={17} />

                        <div>
                          <strong>{chunk.name}</strong>
                          <span>{chunk.file}</span>
                        </div>
                      </div>

                      <div className="analysis-item-meta">
                        <span className="analysis-type">
                          {chunk.type}
                        </span>

                        <span>
                          Lines {chunk.start_line}–{chunk.end_line}
                        </span>
                      </div>

                      {chunk.content && (
                        <details className="analysis-code-details">
                          <summary>View content</summary>
                          <pre>
                            <code>{chunk.content}</code>
                          </pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>


            {/* Extracted dependencies */}
            <div className="analysis-results">
              <div className="analysis-results-heading">
                <div>
                  <h3>Dependencies</h3>
                  <p>Libraries and modules imported by your project</p>
                </div>

                <span>{dependencies.length} dependencies</span>
              </div>

              {dependencies.length === 0 ? (
                <div className="analysis-empty">
                  No dependencies found yet.
                </div>
              ) : (
                <div className="analysis-list">
                  {dependencies.map((dependency) => (
                    <div
                      className="analysis-item"
                      key={dependency.id}
                    >
                      <div className="analysis-item-main">
                        <Braces size={17} />

                        <div>
                          <strong>{dependency.name}</strong>
                          <span>{dependency.file}</span>
                        </div>
                      </div>

                      <div className="analysis-item-meta">
                        <span className="analysis-type">
                          {dependency.type}
                        </span>

                        <span>
                          Line {dependency.line_number}
                        </span>

                        {dependency.resolved_file && (
                          <span>
                            Resolved to: {dependency.resolved_file}
                          </span>
                        )}
                      </div>

                      {dependency.imported_symbols && (
                        <details className="analysis-code-details">
                          <summary>View imported symbols</summary>
                          <pre>
                            <code>{dependency.imported_symbols}</code>
                          </pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

          </section>


        </div>
      </main>
    </div>
  )
}

export default ProjectOverviewPage
