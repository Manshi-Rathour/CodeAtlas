import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  LoaderCircle,
  AlertCircle,
  X,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import FileTree from '../components/explorer/FileTree'
import CodeViewer from '../components/explorer/CodeViewer'
import projectService from '../services/projectService'

import './FileExplorerPage.css'

function FileExplorerPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [project, setProject] = useState(null)
  const [fileData, setFileData] = useState(null)

  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)

  const [searchInput, setSearchInput] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [language, setLanguage] = useState('')

  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [isContentLoading, setIsContentLoading] = useState(false)
  const [contentError, setContentError] = useState('')

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  // Load project information.
  useEffect(() => {
    let isActive = true

    const fetchProject = async () => {
      try {
        const response = await projectService.getProject(projectId)

        if (isActive) {
          setProject(response)
        }
      } catch (err) {
        if (isActive) {
          setError(
            err.response?.data?.detail ||
            'Unable to load project information.'
          )
        }
      }
    }

    fetchProject()

    return () => {
      isActive = false
    }
  }, [projectId])

  // Load the requested page of project files.
  const fetchFiles = useCallback(async () => {
    setIsLoading(true)
    setError('')

    try {
      const response = await projectService.getProjectFiles(projectId, {
        page,
        page_size: pageSize,
        ...(language ? { language } : {}),
        ...(appliedSearch ? { search: appliedSearch } : {}),
      })

      setFileData(response)
    } catch (err) {
      setFileData(null)
      setError(
        err.response?.data?.detail ||
        'Unable to load project files.'
      )
    } finally {
      setIsLoading(false)
    }
  }, [projectId, page, pageSize, language, appliedSearch])

  useEffect(() => {
    fetchFiles()
  }, [fetchFiles])

  // Clear the previous selection when filters or pages change.
  useEffect(() => {
    setSelectedFile(null)
    setFileContent('')
    setContentError('')
  }, [projectId, page, language, appliedSearch])

  // Fetch source code for the selected file.
  useEffect(() => {
    if (!selectedFile) return

    let isActive = true

    const fetchContent = async () => {
      setIsContentLoading(true)
      setContentError('')
      setFileContent('')

      try {
        const response = await projectService.getProjectFileContent(
          projectId,
          selectedFile.id
        )

        if (isActive) {
          setFileContent(response.content)
        }
      } catch (err) {
        if (isActive) {
          setContentError(
            err.response?.data?.detail ||
            'Unable to load this file.'
          )
        }
      } finally {
        if (isActive) {
          setIsContentLoading(false)
        }
      }
    }

    fetchContent()

    return () => {
      isActive = false
    }
  }, [projectId, selectedFile])

  const handleSearch = (event) => {
    event.preventDefault()
    setPage(1)
    setAppliedSearch(searchInput.trim())
  }

  const handleLanguageChange = (event) => {
    setPage(1)
    setLanguage(event.target.value)
  }

  const handleClearFilters = () => {
    setSearchInput('')
    setAppliedSearch('')
    setLanguage('')
    setPage(1)
  }

  const handleSelectFile = (file) => {
    setSelectedFile(file)
  }

  const totalPages = fileData?.total_pages ?? 0
  const totalFiles = fileData?.total ?? 0

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main file-explorer-main">
        <header className="dashboard-topbar">
          <div className="dashboard-breadcrumb">
            Workspace <span>/</span> Projects <span>/</span>
            {project?.name || 'Project'} <span>/</span> Files
          </div>
        </header>

        <div className="file-explorer-content">
          <button
            className="file-explorer-back"
            onClick={() => navigate(`/dashboard/projects/${projectId}`)}
          >
            <ArrowLeft size={17} />
            Back to Project
          </button>

          <section className="file-explorer-heading">
            <div>
              <div className="file-explorer-eyebrow">
                <FolderOpen size={16} />
                CODEBASE EXPLORER
              </div>

              <h1>{project?.name || 'File Explorer'}</h1>

              <p>
                Browse your project files and inspect source code.
              </p>
            </div>

            <button
              className="file-explorer-refresh"
              onClick={fetchFiles}
              disabled={isLoading}
              title="Refresh files"
            >
              <RefreshCw
                size={17}
                className={isLoading ? 'spin' : ''}
              />
              Refresh
            </button>
          </section>

          <section className="file-explorer-toolbar">
            <form
              className="file-explorer-search"
              onSubmit={handleSearch}
            >
              <Search size={18} />

              <input
                type="text"
                placeholder="Search files or folder paths..."
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
              />

              {searchInput && (
                <button
                  type="button"
                  onClick={() => {
                    setSearchInput('')
                    setPage(1)
                    setAppliedSearch('')
                  }}
                  title="Clear search"
                >
                  <X size={16} />
                </button>
              )}

              <button type="submit">Search</button>
            </form>

            <select
              className="file-explorer-language"
              value={language}
              onChange={handleLanguageChange}
            >
              <option value="">All Languages</option>
              <option value="Python">Python</option>
              <option value="JavaScript">JavaScript</option>
              <option value="TypeScript">TypeScript</option>
              <option value="Java">Java</option>
              <option value="C">C</option>
              <option value="C++">C++</option>
              <option value="C#">C#</option>
              <option value="Go">Go</option>
              <option value="Rust">Rust</option>
              <option value="HTML">HTML</option>
              <option value="CSS">CSS</option>
              <option value="JSON">JSON</option>
              <option value="Markdown">Markdown</option>
              <option value="Other">Other</option>
            </select>

            {(appliedSearch || language) && (
              <button
                className="file-explorer-clear"
                onClick={handleClearFilters}
              >
                Clear filters
              </button>
            )}
          </section>

          <div className="file-explorer-summary">
            <span>
              {totalFiles.toLocaleString('en-IN')} files found
            </span>

            {fileData && (
              <span>
                Page {fileData.page} of {totalPages || 1}
              </span>
            )}
          </div>

          {error ? (
            <div className="file-explorer-error">
              <AlertCircle size={28} />
              <h3>Unable to load files</h3>
              <p>{error}</p>
              <button onClick={fetchFiles}>
                <RefreshCw size={16} />
                Try Again
              </button>
            </div>
          ) : (
            <section className="file-explorer-workspace">
              <aside className="file-explorer-sidebar">
                {isLoading ? (
                  <div className="file-explorer-loading">
                    <LoaderCircle size={25} className="spin" />
                    <span>Loading files...</span>
                  </div>
                ) : (
                  <FileTree
                    files={fileData?.files || []}
                    selectedFile={selectedFile}
                    onSelectFile={handleSelectFile}
                  />
                )}
              </aside>

              <div className="file-explorer-viewer">
                <CodeViewer
                  file={selectedFile}
                  content={fileContent}
                  isLoading={isContentLoading}
                  error={contentError}
                />
              </div>
            </section>
          )}

          {!error && totalPages > 1 && (
            <div className="file-explorer-pagination">
              <button
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={page <= 1 || isLoading}
              >
                <ChevronLeft size={17} />
                Previous
              </button>

              <span>
                Page <strong>{page}</strong> of{' '}
                <strong>{totalPages}</strong>
              </span>

              <button
                onClick={() =>
                  setPage((current) => Math.min(totalPages, current + 1))
                }
                disabled={page >= totalPages || isLoading}
              >
                Next
                <ChevronRight size={17} />
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default FileExplorerPage
