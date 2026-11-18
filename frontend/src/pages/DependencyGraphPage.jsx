import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  GitBranch,
  FileCode2,
  Files,
  Network,
  RefreshCw,
  Info,
  X,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import ProjectNav from '../components/common/ProjectNav'
import DependencyGraph from '../components/graph/DependencyGraph'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'

import graphService from '../services/graphService'

import './DependencyGraphPage.css'

// Friendly names for the dependency kinds detected by the analyzer.
const DEPENDENCY_TYPE_LABELS = {
  import: 'import',
  use: 'use',
  require: 'require',
  require_relative: 'require_relative',
  local_include: 'include',
  system_include: 'system include',
  stylesheet: 'stylesheet',
  script: 'script',
  css_import: 'CSS import',
  template_include: 'template include',
  template_extends: 'template extends',
}

const dependencyTypeLabel = (type) =>
  DEPENDENCY_TYPE_LABELS[type] || type

function DependencyGraphPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [graph, setGraph] = useState(null)
  const [selectedNodeId, setSelectedNodeId] = useState(null)

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadGraph = async () => {
    setIsLoading(true)
    setError('')
    setSelectedNodeId(null)

    try {
      const response = await graphService.getGraph(projectId)
      setGraph(response)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load the dependency graph.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadGraph()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const fileById = useMemo(() => {
    const lookup = {}

    ;(graph?.nodes || []).forEach((node) => {
      lookup[node.id] = node
    })

    return lookup
  }, [graph])

  const selectedNode = selectedNodeId
    ? fileById[selectedNodeId]
    : null

  const outgoingEdges = (graph?.edges || []).filter(
    (edge) => edge.source === selectedNodeId
  )

  const incomingEdges = (graph?.edges || []).filter(
    (edge) => edge.target === selectedNodeId
  )

  if (isLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main graph-page-main">
          <LoadingSpinner label="Building dependency graph..." />
        </main>
      </div>
    )
  }

  if (error || !graph) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main graph-page-main">
          <div className="graph-page-content">
            <ErrorMessage
              title="Unable to load graph"
              message={error || 'Project not found.'}
              onRetry={loadGraph}
            />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main graph-page-main">
        <DashboardTopbar>
          Workspace <span>/</span> Projects <span>/</span>
          {graph.project_name} <span>/</span> Dependencies
        </DashboardTopbar>

        <div className="graph-page-content">
          <button
            className="project-back-button"
            onClick={() => navigate(`/dashboard/projects/${projectId}`)}
          >
            <ArrowLeft size={17} />
            Back to Project
          </button>

          <ProjectNav projectId={projectId} />

          <section className="graph-page-heading">
            <div>
              <div className="graph-eyebrow">
                <Network size={16} />
                DEPENDENCY MAP
              </div>

              <h1>{graph.project_name} Dependencies</h1>

              <p>
                Files are nodes and resolved internal imports,
                stylesheets, scripts and template includes are directed
                edges. External libraries are excluded.
              </p>
            </div>

            <button
              className="graph-refresh"
              onClick={loadGraph}
              disabled={isLoading}
            >
              <RefreshCw size={15} />
              Refresh
            </button>
          </section>

          <section className="graph-stats">
            <div>
              <Files size={18} />
              <span>Files</span>
              <strong>{graph.total_nodes}</strong>
            </div>

            <div>
              <GitBranch size={18} />
              <span>Internal Links</span>
              <strong>{graph.total_edges}</strong>
            </div>

            <div>
              <Info size={18} />
              <span>Isolated Files</span>
              <strong>
                {Math.max(
                  graph.total_nodes -
                    new Set(graph.edges.flatMap((edge) => [
                      edge.source,
                      edge.target,
                    ])).size,
                  0
                )}
              </strong>
            </div>
          </section>

          {graph.total_nodes === 0 ? (
            <EmptyState
              icon={Network}
              title="No files to graph"
              message="Run project analysis first, or import a project that contains source files."
            />
          ) : (
            <>
              {graph.total_edges === 0 && (
                <div className="graph-notice">
                  <Info size={16} />
                  No internal dependencies were resolved. Only
                  external libraries are imported, or analysis has not
                  been run yet.
                </div>
              )}

              <section className="graph-toolbar">
                <div className="graph-legend">
                  <span>
                    <i className="legend-source" />
                    imports from
                  </span>

                  <span>
                    <i className="legend-target" />
                    imported file
                  </span>
                </div>
              </section>

              <div
                className={`graph-workspace ${
                  selectedNode ? 'with-details' : ''
                }`}
              >
                <div className="graph-canvas">
                  <DependencyGraph
                    graph={graph}
                    selectedNodeId={selectedNodeId}
                    onSelectNode={setSelectedNodeId}
                  />
                </div>

                <aside className="graph-details">
                  {!selectedNode ? (
                    <div className="graph-details-placeholder">
                      <FileCode2 size={26} />
                      <h3>Select a file</h3>
                      <p>
                        Click a node to inspect its path, language
                        and resolved dependencies.
                      </p>
                    </div>
                  ) : (
                    <>
                      <div className="graph-details-header">
                        <div>
                          <h2>{selectedNode.label}</h2>
                          <span>{selectedNode.language}</span>
                        </div>

                        <button
                          onClick={() => setSelectedNodeId(null)}
                          title="Close details"
                        >
                          <X size={16} />
                        </button>
                      </div>

                      <p className="graph-details-path">
                        {selectedNode.file_path}
                      </p>

                      <div className="graph-details-section">
                        <h3>
                          Dependencies from this file
                          <b>{outgoingEdges.length}</b>
                        </h3>

                        {outgoingEdges.length === 0 ? (
                          <p className="graph-details-empty">
                            This file has no outgoing project dependencies.
                          </p>
                        ) : (
                          outgoingEdges.map((edge) => {
                            const target = fileById[edge.target]

                            return (
                              <button
                                key={edge.id}
                                className="graph-dependency"
                                onClick={() =>
                                  setSelectedNodeId(edge.target)
                                }
                              >
                                <ArrowRight size={14} />

                                <div>
                                  <strong>
                                    {target?.file_path ||
                                      `File ${edge.target}`}
                                  </strong>

                                  <span>
                                    {edge.dependency} ·{' '}
                                    {dependencyTypeLabel(edge.type)} ·
                                    line {edge.line_number}
                                  </span>
                                </div>
                              </button>
                            )
                          })
                        )}
                      </div>

                      <div className="graph-details-section">
                        <h3>
                          Used by
                          <b>{incomingEdges.length}</b>
                        </h3>

                        {incomingEdges.length === 0 ? (
                          <p className="graph-details-empty">
                            No other project file depends on this file.
                          </p>
                        ) : (
                          incomingEdges.map((edge) => {
                            const source = fileById[edge.source]

                            return (
                              <button
                                key={edge.id}
                                className="graph-dependency"
                                onClick={() =>
                                  setSelectedNodeId(edge.source)
                                }
                              >
                                <ArrowRight size={14} />

                                <div>
                                  <strong>
                                    {source?.file_path ||
                                      `File ${edge.source}`}
                                  </strong>

                                  <span>
                                    {edge.dependency} ·{' '}
                                    {dependencyTypeLabel(edge.type)} ·
                                    line {edge.line_number}
                                  </span>
                                </div>
                              </button>
                            )
                          })
                        )}
                      </div>
                    </>
                  )}
                </aside>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default DependencyGraphPage
