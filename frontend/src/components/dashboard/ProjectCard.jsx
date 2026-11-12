
import { useNavigate } from 'react-router-dom'
import {
    FolderCode,
    GitBranch,
    FileArchive,
    ArrowUpRight,
    FileCode2,
    Clock3,
} from 'lucide-react'

function ProjectCard({ project }) {
    const navigate = useNavigate()

    const isGithub = project?.source_type === 'github'

    const formattedDate = project?.created_at
        ? new Date(project.created_at).toLocaleDateString()
        : 'Recently added'

    const handleExplore = () => {
        navigate(`/dashboard/projects/${project.id}`)
    }

    return (
        <article className="project-card">
            <div className="project-card-header">
                <div className="project-card-icon">
                    {isGithub ? (
                        <GitBranch size={22} />
                    ) : (
                        <FileArchive size={22} />
                    )}
                </div>

                <span className={`project-status status-${project?.status || 'unknown'}`}>
                    <span className="status-indicator"></span>
                    {project?.status || 'Unknown'}
                </span>
            </div>

            <div className="project-card-content">
                <h3>{project?.name || 'Untitled Project'}</h3>

                <p>
                    {project?.description || 'No project description provided.'}
                </p>
            </div>

            <div className="project-card-meta">
                <div>
                    <FileCode2 size={16} />
                    <span>{project?.total_files ?? 0} files</span>
                </div>

                <div>
                    <Clock3 size={16} />
                    <span>{formattedDate}</span>
                </div>
            </div>

            <div className="project-card-footer">
                <span className="project-source-label">
                    <FolderCode size={15} />
                    {isGithub ? 'GitHub Repository' : 'ZIP Upload'}
                </span>

                <button
                    className="project-explore-button"
                    onClick={handleExplore}
                    disabled={!project?.id}
                >
                    Explore
                    <ArrowUpRight size={16} />
                </button>
            </div>
        </article>
    )
}

export default ProjectCard
