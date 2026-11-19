import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  Boxes,
  Code2,
  FileCode2,
  Files,
  GitBranch,
  Languages,
  LoaderCircle,
  RefreshCw,
  Sparkles,
  ArrowRight,
  FolderTree,
  AlertCircle,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import ProjectNav from '../components/common/ProjectNav'
import CollapsibleSection from '../components/common/CollapsibleSection'
import MarkdownViewer from '../components/documentation/MarkdownViewer'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'

import architectureService from '../services/architectureService'
import {
  getCachedExplanation,
  setCachedExplanation,
} from '../utils/architectureExplanationCache'

import './ArchitecturePage.css'

function ArchitecturePage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [architecture, setArchitecture] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isExplaining, setIsExplaining] = useState(false)

  const [error, setError] = useState('')
  const [explanationError, setExplanationError] = useState('')

  const loadArchitecture = async () => {
    setIsLoading(true)
    setError('')

    try {
      const response = await architectureService.getArchitecture(
        projectId,
        false
      )

      // Refreshing statistics must not discard an explanation that was
      // already generated for this project.
      setArchitecture({
        ...response,
        ai_explanation:
          getCachedExplanation(projectId) ||
          response.ai_explanation ||
          null,
      })
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load project architecture.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadArchitecture()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const handleGenerateExplanation = async () => {
    setIsExplaining(true)
    setExplanationError('')

    try {
      const response = await architectureService.getArchitecture(
        projectId,
        true
      )

      const explanation =
        response.ai_explanation || getCachedExplanation(projectId)

      if (response.ai_explanation) {
        setCachedExplanation(projectId, response.ai_explanation)
      }

      setArchitecture({
        ...response,
        ai_explanation: explanation,
      })
    } catch (err) {
      setExplanationError(
        err.response?.data?.detail ||
        'The AI could not explain this architecture. Please try again.'
      )
    } finally {
      setIsExplaining(false)
    }
  }

  if (isLoading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main architecture-page-main">
          <LoadingSpinner label="Reading project structure..." />
        </main>
      </div>
    )
  }

  if (error || !architecture) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main architecture-page-main">
          <div className="architecture-page-content">
            <ErrorMessage
              title="Unable to load architecture"
              message={error || 'Project not found.'}
              onRetry={loadArchitecture}
            />
          </div>
        </main>
      </div>
    )
  }

  const languages = architecture.languages || []
  const modules = architecture.modules || []
  const fileRelationships = architecture.file_relationships || []
  const moduleRelationships = architecture.module_relationships || []

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main architecture-page-main">
        <DashboardTopbar>
          Workspace <span>/</span> Projects <span>/</span>
          {architecture.project_name} <span>/</span> Architecture
        </DashboardTopbar>

        <div className="architecture-page-content">
          <button
            className="project-back-button"
            onClick={() => navigate(`/dashboard/projects/${projectId}`)}
          >
            <ArrowLeft size={17} />
            Back to Project
          </button>

          <ProjectNav projectId={projectId} />

          <section className="architecture-heading">
            <div>
              <div className="architecture-eyebrow">
                <Sparkles size={16} />
                ARCHITECTURE INTELLIGENCE
              </div>

              <h1>{architecture.project_name} Architecture</h1>

              <p>
                Statistics below come directly from the analysis
                database. The AI explanation only interprets these facts.
              </p>
            </div>

            <button
              className="architecture-refresh"
              onClick={loadArchitecture}
              disabled={isLoading}
            >
              <RefreshCw size={15} />
              Refresh
            </button>
          </section>

          {/* Database-derived statistics */}
          <section className="architecture-stats">
            <div className="architecture-stat">
              <Files size={20} />
              <span>Files</span>
              <strong>{architecture.total_files}</strong>
            </div>

            <div className="architecture-stat">
              <Code2 size={20} />
              <span>Symbols</span>
              <strong>{architecture.total_symbols}</strong>
            </div>

            <div className="architecture-stat">
              <Boxes size={20} />
              <span>Modules</span>
              <strong>{modules.length}</strong>
            </div>

            <div className="architecture-stat">
              <GitBranch size={20} />
              <span>Dependencies</span>
              <strong>{architecture.total_dependencies}</strong>
            </div>

            <div className="architecture-stat">
              <ArrowRight size={20} />
              <span>Internal Links</span>
              <strong>{architecture.total_internal_dependencies}</strong>
            </div>
          </section>

          {/* Languages */}
          <section className="architecture-panel">
            <div className="architecture-panel-heading">
              <div>
                <h2>
                  <Languages size={18} />
                  Languages Used
                </h2>
                <p>Programming languages detected in project files</p>
              </div>
            </div>

            {languages.length === 0 ? (
              <p className="architecture-muted">
                No programming languages were classified.
              </p>
            ) : (
              <div className="architecture-language-list">
                {languages.map((language) => (
                  <span
                    key={language.language}
                    className="architecture-language"
                  >
                    {language.language}
                    <b>{language.file_count}</b>
                  </span>
                ))}
              </div>
            )}
          </section>

          {/* Modules */}
          <CollapsibleSection
            icon={FolderTree}
            title="Project Modules"
            subtitle="Directories grouped with their files and detected symbols"
            meta={`${modules.length} module${modules.length === 1 ? '' : 's'}`}
          >
            {modules.length === 0 ? (
              <p className="architecture-muted">
                No modules were found.
              </p>
            ) : (
              <div className="architecture-modules">
                {modules.map((module) => (
                  <details
                    key={module.name}
                    className="architecture-module"
                  >
                    <summary>
                      <div>
                        <strong>
                          {module.name === 'root'
                            ? 'Project root'
                            : module.name}
                        </strong>

                        <span>
                          {module.file_count} file
                          {module.file_count === 1 ? '' : 's'}
                          {' · '}
                          {module.symbols.length} symbol
                          {module.symbols.length === 1 ? '' : 's'}
                        </span>
                      </div>

                      <div className="architecture-module-languages">
                        {module.languages.map((language) => (
                          <span key={language}>{language}</span>
                        ))}
                      </div>
                    </summary>

                    <div className="architecture-module-body">
                      <div>
                        <h4>Files</h4>
                        <ul>
                          {module.files.map((file) => (
                            <li key={file}>{file}</li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4>Symbols</h4>

                        {module.symbols.length === 0 ? (
                          <p className="architecture-muted">
                            No symbols detected in this module.
                          </p>
                        ) : (
                          <ul>
                            {module.symbols.map((symbol, index) => (
                              <li
                                key={`${symbol.name}-${symbol.start_line}-${index}`}
                              >
                                <span className="architecture-symbol-type">
                                  {symbol.type}
                                </span>
                                {symbol.name}
                                <em>
                                  lines {symbol.start_line}–
                                  {symbol.end_line}
                                </em>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            )}
          </CollapsibleSection>

          {/* Relationships */}
          <CollapsibleSection
            icon={GitBranch}
            title="Internal File Relationships"
            subtitle="Resolved imports between files in this project"
            meta={`${fileRelationships.length} link${
              fileRelationships.length === 1 ? '' : 's'
            }`}
          >
            {fileRelationships.length === 0 ? (
              <p className="architecture-muted">
                No internal file dependencies were resolved.
              </p>
            ) : (
              <div className="architecture-relationships">
                {fileRelationships.map((relationship, index) => (
                  <div
                    className="architecture-relationship"
                    key={`${relationship.source}-${relationship.target}-${index}`}
                  >
                    <FileCode2 size={16} />

                    <span className="architecture-relationship-source">
                      {relationship.source}
                    </span>

                    <ArrowRight size={14} />

                    <span className="architecture-relationship-target">
                      {relationship.target}
                    </span>

                    <span className="architecture-relationship-meta">
                      {relationship.dependency} · {relationship.type} · line{' '}
                      {relationship.line_number}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CollapsibleSection>

          {/* Module relationships */}
          <CollapsibleSection
            icon={Boxes}
            title="Module Relationships"
            subtitle="Dependencies grouped by directory"
            meta={`${moduleRelationships.length} link${
              moduleRelationships.length === 1 ? '' : 's'
            }`}
          >
            {moduleRelationships.length === 0 ? (
              <p className="architecture-muted">
                No cross-module dependencies were resolved.
              </p>
            ) : (
              <div className="architecture-module-relationships">
                {moduleRelationships.map((relationship, index) => (
                  <div
                    key={`${relationship.source}-${relationship.target}-${index}`}
                  >
                    <span>{relationship.source}</span>
                    <ArrowRight size={14} />
                    <span>{relationship.target}</span>
                    <b>
                      {relationship.dependency_count} link
                      {relationship.dependency_count === 1 ? '' : 's'}
                    </b>
                  </div>
                ))}
              </div>
            )}
          </CollapsibleSection>

          {/* AI explanation */}
          <section className="architecture-ai">
            <div className="architecture-ai-header">
              <div>
                <h2>
                  <Sparkles size={18} />
                  AI Architecture Explanation
                </h2>
                <p>
                  A local model explains the structure above. Exact
                  statistics always come from the database.
                </p>
              </div>

              <button
                onClick={handleGenerateExplanation}
                disabled={isExplaining}
              >
                {isExplaining ? (
                  <LoaderCircle size={16} className="spin" />
                ) : (
                  <Sparkles size={16} />
                )}

                {isExplaining
                  ? 'Explaining...'
                  : architecture.ai_explanation
                    ? 'Regenerate Explanation'
                    : 'Explain with AI'}
              </button>
            </div>

            {explanationError && (
              <div className="architecture-error">
                <AlertCircle size={16} />
                {explanationError}
              </div>
            )}

            {architecture.ai_explanation ? (
              <div className="architecture-ai-body">
                <MarkdownViewer
                  content={architecture.ai_explanation}
                />
              </div>
            ) : (
              !isExplaining && (
                <EmptyState
                  icon={Sparkles}
                  title="No AI explanation generated yet"
                  message="Generate a beginner-friendly explanation of the project organization, directory structure and dependency patterns shown above."
                  action={
                    <button
                      onClick={handleGenerateExplanation}
                      disabled={isExplaining}
                    >
                      <Sparkles size={15} />
                      Explain with AI
                    </button>
                  }
                />
              )
            )}
          </section>
        </div>
      </main>
    </div>
  )
}

export default ArchitecturePage
