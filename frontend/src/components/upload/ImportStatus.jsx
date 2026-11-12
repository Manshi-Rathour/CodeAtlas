
import { CheckCircle2, FolderOpen, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function ImportStatus({ project }) {
  const navigate = useNavigate()

  if (!project) return null

  return (
    <div className="import-success">
      <div className="import-success-icon">
        <CheckCircle2 size={34} />
      </div>

      <h2>Project imported successfully!</h2>

      <p>
        Your project has been uploaded and its files have
        been scanned by CodeAtlas.
      </p>

      <div className="import-success-details">
        <FolderOpen size={21} />
        <div>
          <strong>{project.name}</strong>
          <span>
            {project.source_type?.toUpperCase()} · {project.status}
          </span>
        </div>
      </div>

      <button
        className="import-submit-button"
        onClick={() =>
          navigate(`/dashboard/projects/${project.id}`)
        }
      >
        Explore Project
        <ArrowRight size={18} />
      </button>
    </div>
  )
}

export default ImportStatus
