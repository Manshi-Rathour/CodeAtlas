import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    FolderCode,
    GitBranch,
    FileArchive,
    ArrowUpRight,
    FileCode2,
    Clock3,
    Trash2,
    LoaderCircle,
} from 'lucide-react'

import projectService from '../../services/projectService'

function ProjectCard({ project, onDelete }) {
    const navigate = useNavigate()

    const [isDeleting, setIsDeleting] = useState(false)
    const [deleteError, setDeleteError] = useState('')

    const isGithub = project?.source_type === 'github'

    // A project only counts as ready once codebase analysis has run.
    const statusKey = project?.has_analysis
        ? 'analyzed'
        : project?.status === 'failed'
            ? 'failed'
            : project?.status === 'importing'
                ? 'importing'
                : 'awaiting-analysis'

    const statusLabel = project?.has_analysis
        ? 'Completed'
        : project?.status === 'failed'
            ? 'Failed'
            : project?.status === 'importing'
                ? 'Importing'
                : 'Awaiting analysis'

    const formattedDate = project?.created_at
        ? new Date(project.created_at).toLocaleDateString()
        : 'Recently added'

    const handleExplore = () => {
        navigate(`/dashboard/projects/${project.id}`)
    }

    const handleDelete = async () => {
        const confirmed = window.confirm(
            `Are you sure you want to delete "${project.name}"? This action cannot be undone.`
        )

        if (!confirmed) return

        try {
            setIsDeleting(true)
            setDeleteError('')

            await projectService.deleteProject(project.id)

            if (onDelete) {
                onDelete(project.id)
            }
        } catch (error) {
            console.error('Project deletion error:', error)

            setDeleteError(
                error.response?.data?.detail ||
                'Unable to delete this project. Please try again.'
            )
        } finally {
            setIsDeleting(false)
        }
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

                <span className={`project-status status-${statusKey}`}>
                    <span className="status-indicator"></span>
                    {statusLabel}
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

            {deleteError && (
                <p className="project-delete-error">
                    {deleteError}
                </p>
            )}

            <div className="project-card-footer">
                <span className="project-source-label">
                    <FolderCode size={15} />
                    {isGithub ? 'GitHub Repository' : 'ZIP Upload'}
                </span>

                <div className="project-card-actions">
                    <button
                        className="project-delete-button"
                        onClick={handleDelete}
                        disabled={isDeleting}
                        title="Delete project"
                        aria-label={`Delete ${project?.name || 'project'}`}
                    >
                        {isDeleting ? (
                            <LoaderCircle size={17} className="refresh-spinning" />
                        ) : (
                            <Trash2 size={17} />
                        )}
                    </button>

                    <button
                        className="project-explore-button"
                        onClick={handleExplore}
                        disabled={!project?.id || isDeleting}
                    >
                        Explore
                        <ArrowUpRight size={16} />
                    </button>
                </div>
            </div>
        </article>
    )
}

export default ProjectCard
