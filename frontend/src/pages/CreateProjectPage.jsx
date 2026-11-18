
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, Code2, GitBranch } from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import ZipUpload from '../components/upload/ZipUpload'
import GitHubImport from '../components/upload/GitHubImport'
import ImportStatus from '../components/upload/ImportStatus'

import './CreateProjectPage.css'

function CreateProjectPage() {
  const [activeTab, setActiveTab] = useState('github')
  const [importedProject, setImportedProject] = useState(null)

  const navigate = useNavigate()

  const handleImportSuccess = (project) => {
    setImportedProject(project)
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main create-project-main">
        <DashboardTopbar>
          Workspace <span>/</span> Import Project
        </DashboardTopbar>

        <div className="create-project-content">
          <button
            className="back-to-dashboard"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft size={17} />
            Back to Dashboard
          </button>

          <div className="create-project-heading">
            <div className="create-project-icon">
              <Code2 size={25} />
            </div>

            <h1>Bring your code to CodeAtlas</h1>

            <p>
              Import your codebase and start exploring its
              architecture, files and dependencies.
            </p>
          </div>

          {importedProject ? (
            <div className="create-project-card">
              <ImportStatus project={importedProject} />
            </div>
          ) : (
            <div className="create-project-card">
              <div className="import-tabs">
                <button
                  type="button"
                  className={`import-tab ${activeTab === 'github' ? 'active' : ''}`}
                  onClick={() => setActiveTab('github')}
                >
                  <GitBranch size={19} />
                  GitHub Repository
                </button>

                <button
                  type="button"
                  className={`import-tab ${activeTab === 'zip' ? 'active' : ''}`}
                  onClick={() => setActiveTab('zip')}
                >
                  <Upload size={19} />
                  ZIP Upload
                </button>
              </div>

              <div className="import-tab-content">
                {activeTab === 'github' ? (
                  <GitHubImport onSuccess={handleImportSuccess} />
                ) : (
                  <ZipUpload onSuccess={handleImportSuccess} />
                )}
              </div>
            </div>
          )}

          <div className="create-project-footer">
            <Code2 size={17} />
            <span>
              Your source code is processed securely. CodeAtlas
              does not execute uploaded project files.
            </span>
          </div>
        </div>
      </main>
    </div>
  )
}

export default CreateProjectPage
