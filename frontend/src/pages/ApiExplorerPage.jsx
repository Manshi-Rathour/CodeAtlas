import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Activity,
  ArrowLeft,
  BookOpen,
  Braces,
  Boxes,
  FileCode2,
  Files,
  GitBranch,
  MessagesSquare,
  RefreshCw,
  Route,
  Search,
  Server,
  X,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import ProjectNav from '../components/common/ProjectNav'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'

import analysisService from '../services/analysisService'

import './ApiExplorerPage.css'

function formatBytes(bytes) {  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(value) {
  if (!value) return 'Not generated yet'

  return new Date(value).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function StatCard({ icon: Icon, label, value, detail }) {
  return (
    <div className="api-stat-card">
      <div className="api-stat-icon">
        <Icon size={18} />
      </div>

      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        {detail && <small>{detail}</small>}
      </div>
    </div>
  )
}

function ApiExplorerPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [endpoints, setEndpoints] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [frameworks, setFrameworks] = useState([])

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const [searchInput, setSearchInput] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [method, setMethod] = useState('ALL')

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setError('')

    try {
      const [apiResponse, metricsResponse] = await Promise.all([
        analysisService.getProjectApis(projectId),
        analysisService.getProjectMetrics(projectId),
      ])

      setEndpoints(apiResponse.endpoints || [])
      setFrameworks(apiResponse.frameworks || [])
      setMetrics(metricsResponse)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load API and project metrics.'
      )
    } finally {
      setIsLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const filteredEndpoints = useMemo(() => {
    const term = appliedSearch.toLowerCase()

    return endpoints.filter((endpoint) => {
      if (method !== 'ALL' && endpoint.method !== method) return false

      if (!term) return true

      return (
        endpoint.path.toLowerCase().includes(term) ||
        endpoint.file.toLowerCase().includes(term) ||
        endpoint.framework.toLowerCase().includes(term)
      )
    })
  }, [endpoints, method, appliedSearch])

  const methodCounts = useMemo(() => {
    const counts = {}

    endpoints.forEach((endpoint) => {
      counts[endpoint.method] = (counts[endpoint.method] || 0) + 1
    })

    return counts
  }, [endpoints])

  const availableMethods = [
    'ALL',
    ...Object.keys(methodCounts).sort(),
  ]

  const handleSearch = (event) => {
    event.preventDefault()
    setAppliedSearch(searchInput.trim())
  }

  const handleClearFilters = () => {
    setSearchInput('')
    setAppliedSearch('')
    setMethod('ALL')
  }

  if (isLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main api-page-main">
          <LoadingSpinner label="Detecting API routes and metrics..." />
        </main>
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main api-page-main">
          <div className="api-page-content">
            <ErrorMessage
              title="Unable to load API details"
              message={error || 'Project not found.'}
              onRetry={loadData}
            />
          </div>
        </main>
      </div>
    )
  }

  const symbolCoverage = metrics.total_files
    ? Math.round(
        (metrics.symbols.files_with_symbols / metrics.total_files) * 100
      )
    : 0

  const topLanguages = (metrics.languages || []).slice(0, 6)
  const biggestLanguage = Math.max(
    ...topLanguages.map((language) => language.files),
    1
  )

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main api-page-main">
        <DashboardTopbar>
          Workspace <span>/</span> Projects <span>/</span>
          {metrics.project_name} <span>/</span> APIs & Metrics
        </DashboardTopbar>

        <div className="api-page-content">
          <button
            className="project-back-button"
            onClick={() =>
              navigate(`/dashboard/projects/${projectId}`)
            }
          >
            <ArrowLeft size={17} />
            Back to Project
          </button>

          <ProjectNav projectId={projectId} />

          <section className="api-page-heading">
            <div>
              <div className="api-eyebrow">
                <Route size={16} />
                API & PROJECT METRICS
              </div>

              <h1>{metrics.project_name} APIs</h1>

              <p>
                HTTP routes detected from framework decorators and route
                registrations, alongside analysis metrics stored for this
                project.
              </p>
            </div>

            <button
              className="api-refresh"
              onClick={loadData}
              disabled={isLoading}
            >
              <RefreshCw size={15} />
              Refresh
            </button>
          </section>

          <section className="api-stat-grid">
            <StatCard
              icon={Route}
              label="API Endpoints"
              value={endpoints.length}
              detail={
                frameworks.length
                  ? frameworks.join(', ')
                  : 'No framework routes found'
              }
            />
            <StatCard
              icon={Files}
              label="Files"
              value={metrics.total_files.toLocaleString('en-IN')}
              detail={formatBytes(metrics.total_bytes)}
            />
            <StatCard
              icon={Braces}
              label="Symbols"
              value={metrics.symbols.total.toLocaleString('en-IN')}
              detail={`${symbolCoverage}% of files have symbols`}
            />
            <StatCard
              icon={GitBranch}
              label="Dependencies"
              value={metrics.dependencies.total.toLocaleString('en-IN')}
              detail={`${metrics.dependencies.resolved} resolved internally`}
            />
            <StatCard
              icon={MessagesSquare}
              label="Conversations"
              value={metrics.conversations}
              detail="AI chat threads"
            />
            <StatCard
              icon={BookOpen}
              label="Documentation"
              value={metrics.documentation.exists ? 'Ready' : 'Missing'}
              detail={formatDate(metrics.documentation.updated_at)}
            />
          </section>

          <section className="api-endpoints-section">
            <div className="api-section-heading">
              <div>
                <h2>
                  <Server size={19} />
                  Detected API Endpoints
                </h2>
              </div>

              <span className="api-section-count">
                {filteredEndpoints.length} of {endpoints.length}
              </span>
            </div>

            <form className="api-toolbar" onSubmit={handleSearch}>
              <div className="api-search">
                <Search size={16} />

                <input
                  type="search"
                  value={searchInput}
                  onChange={(event) =>
                    setSearchInput(event.target.value)
                  }
                  placeholder="Search path, file or framework"
                  aria-label="Search API endpoints"
                />

                {searchInput && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchInput('')
                      setAppliedSearch('')
                    }}
                    title="Clear search"
                  >
                    <X size={15} />
                  </button>
                )}
              </div>

              <select
                className="api-method-filter"
                value={method}
                onChange={(event) => setMethod(event.target.value)}
                aria-label="Filter by HTTP method"
              >
                {availableMethods.map((option) => (
                  <option key={option} value={option}>
                    {option === 'ALL'
                      ? 'All methods'
                      : `${option} (${methodCounts[option] || 0})`}
                  </option>
                ))}
              </select>

              <button type="submit">Search</button>

              {(appliedSearch || method !== 'ALL') && (
                <button
                  type="button"
                  className="api-clear"
                  onClick={handleClearFilters}
                >
                  Clear
                </button>
              )}
            </form>

            {endpoints.length === 0 ? (
              <EmptyState
                icon={Route}
                title="No API endpoints detected"
                message="This project does not define HTTP routes in a supported framework, or it is a library rather than a web service."
              />
            ) : filteredEndpoints.length === 0 ? (
              <EmptyState
                icon={Search}
                title="No matching endpoints"
                message="Try a different path, file or HTTP method."
              />
            ) : (
              <div className="api-endpoint-list">
                <div className="api-endpoint-header">
                  <span>Method</span>
                  <span>Path</span>
                  <span>Framework</span>
                  <span>Source</span>
                </div>

                {filteredEndpoints.map((endpoint) => (
                  <div
                    className="api-endpoint-row"
                    key={`${endpoint.method}-${endpoint.path}-${endpoint.file}-${endpoint.line}`}
                  >
                    <span
                      className={`api-method api-method-${endpoint.method.toLowerCase()}`}
                    >
                      {endpoint.method}
                    </span>

                    <code className="api-path">{endpoint.path}</code>

                    <span className="api-framework">
                      {endpoint.framework}
                    </span>

                    <span className="api-source" title={endpoint.file}>
                      <FileCode2 size={14} />
                      {endpoint.file}
                      <b>:{endpoint.line}</b>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="api-metrics-section">
            <div className="api-section-heading">
              <div>
                <h2>
                  <Activity size={19} />
                  Analysis Metrics
                </h2>
                <p>
                  Symbols, chunks and dependency resolution from the last
                  stored analysis run.
                </p>
              </div>
            </div>

            <div className="api-metrics-grid">
              <div className="api-metric-panel">
                <h3>
                  <Boxes size={17} />
                  Languages
                </h3>

                {topLanguages.length === 0 ? (
                  <p className="api-metric-empty">
                    No files have been imported.
                  </p>
                ) : (
                  <div className="api-language-list">
                    {topLanguages.map((language) => (
                      <div
                        className="api-language-row"
                        key={language.language}
                      >
                        <div className="api-language-meta">
                          <span>{language.language}</span>
                          <b>{language.files} files</b>
                        </div>

                        <div className="api-language-track">
                          <div
                            className="api-language-bar"
                            style={{
                              width: `${
                                (language.files / biggestLanguage) * 100
                              }%`,
                            }}
                          />
                        </div>

                        <small>{formatBytes(language.bytes)}</small>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="api-metric-panel">
                <h3>
                  <Braces size={17} />
                  Code Symbols
                </h3>

                <div className="api-symbol-grid">
                  <div>
                    <span>Functions</span>
                    <strong>{metrics.symbols.functions}</strong>
                  </div>
                  <div>
                    <span>Methods</span>
                    <strong>{metrics.symbols.methods}</strong>
                  </div>
                  <div>
                    <span>Classes</span>
                    <strong>{metrics.symbols.classes}</strong>
                  </div>
                  <div>
                    <span>Other</span>
                    <strong>{metrics.symbols.other}</strong>
                  </div>
                </div>

                <p className="api-metric-note">
                  {metrics.chunks.total.toLocaleString('en-IN')} searchable
                  chunks across {metrics.chunks.files_with_chunks} files.
                </p>
              </div>

              <div className="api-metric-panel">
                <h3>
                  <GitBranch size={17} />
                  Dependencies
                </h3>

                <div className="api-dependency-bar">
                  <div
                    className="api-dependency-resolved"
                    style={{
                      width: `${
                        metrics.dependencies.total
                          ? (metrics.dependencies.resolved /
                              metrics.dependencies.total) *
                            100
                          : 0
                      }%`,
                    }}
                  />
                </div>

                <div className="api-dependency-legend">
                  <span>
                    <i className="legend-resolved" />
                    Internal · {metrics.dependencies.resolved}
                  </span>
                  <span>
                    <i className="legend-external" />
                    External · {metrics.dependencies.external}
                  </span>
                </div>

                <p className="api-metric-note">
                  {metrics.api_endpoints} API endpoints found across{' '}
                  {metrics.total_files.toLocaleString('en-IN')} files.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default ApiExplorerPage
