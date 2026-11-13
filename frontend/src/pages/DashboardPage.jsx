import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    FolderKanban,
    FileCode2,
    CheckCircle2,
    LoaderCircle,
    Plus,
    RefreshCw,
    ArrowRight,
    Sparkles,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import StatCard from '../components/dashboard/StatCard'
import ProjectCard from '../components/dashboard/ProjectCard'
import projectService from '../services/projectService'
import useAuth from '../hooks/useAuth'

import './DashboardPage.css'

function DashboardPage() {
    const { user } = useAuth()
    const navigate = useNavigate()

    const [projects, setProjects] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')
    const [totalFiles, setTotalFiles] = useState(0)

    // Remove a successfully deleted project from the dashboard.
    const handleProjectDeleted = (deletedProjectId) => {
        setProjects((currentProjects) => {
            const updatedProjects = currentProjects.filter(
                (project) => project.id !== deletedProjectId
            )

            const updatedFileCount = updatedProjects.reduce(
                (total, project) => total + (project.total_files || 0),
                0
            )

            setTotalFiles(updatedFileCount)

            return updatedProjects
        })
    }

    const fetchDashboardData = async () => {
        try {
            setIsLoading(true)
            setError('')

            // Fetch all projects belonging to the logged-in user.
            const projectData = await projectService.getProjects()

            // Fetch file counts for each project.
            const projectsWithFiles = await Promise.all(
                projectData.map(async (project) => {
                    try {
                        const fileData = await projectService.getProjectFiles(
                            project.id,
                            { page: 1, page_size: 1 }
                        )

                        return {
                            ...project,
                            total_files: fileData.total ?? 0,
                        }
                    } catch {
                        return {
                            ...project,
                            total_files: 0,
                        }
                    }
                })
            )

            setProjects(projectsWithFiles)

            const fileCount = projectsWithFiles.reduce(
                (total, project) => total + project.total_files,
                0
            )

            setTotalFiles(fileCount)
        } catch (err) {
            console.error('Dashboard loading error:', err)

            setError(
                err.response?.data?.detail ||
                'Unable to load dashboard data. Please try again.'
            )
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchDashboardData()
    }, [])

    const completedProjects = projects.filter(
        (project) => project.status === 'ready'
    ).length

    const processingProjects = projects.filter(
        (project) =>
            !['ready', 'failed'].includes(project.status)
    ).length

    const firstName = user?.full_name?.split(' ')[0] || 'Developer'

    return (
        <div className="dashboard-layout">
            <Sidebar />

            <main className="dashboard-main">
                <header className="dashboard-topbar">
                    <div className="dashboard-breadcrumb">
                        <span>Workspace</span>
                        <span className="breadcrumb-separator">/</span>
                        <strong>Overview</strong>
                    </div>

                    <div className="dashboard-topbar-right">
                        <span className="dashboard-user-email">
                            {user?.email}
                        </span>

                        <div className="dashboard-topbar-avatar">
                            {firstName.charAt(0).toUpperCase()}
                        </div>
                    </div>
                </header>

                <div className="dashboard-content">
                    <section className="dashboard-welcome">
                        <div>
                            <div className="dashboard-eyebrow">
                                <Sparkles size={15} />
                                YOUR DEVELOPMENT WORKSPACE
                            </div>

                            <h1>
                                Welcome back, <span>{firstName}</span>
                            </h1>

                            <p>
                                Understand your codebase better. Explore projects,
                                analyze files, and discover how everything connects.
                            </p>
                        </div>

                        <button
                            className="dashboard-primary-button"
                            onClick={() => navigate('/dashboard/projects/new')}
                        >
                            <Plus size={19} />
                            Import Project
                        </button>
                    </section>

                    <section className="dashboard-stats-grid">
                        <StatCard
                            title="Total Projects"
                            value={projects.length}
                            description="Projects in your workspace"
                            icon={FolderKanban}
                            accent="blue"
                        />

                        <StatCard
                            title="Total Files"
                            value={totalFiles.toLocaleString()}
                            description="Files discovered across projects"
                            icon={FileCode2}
                            accent="cyan"
                        />

                        <StatCard
                            title="Completed"
                            value={completedProjects}
                            description="Successfully imported projects"
                            icon={CheckCircle2}
                            accent="green"
                        />

                        <StatCard
                            title="In Progress"
                            value={processingProjects}
                            description="Projects being processed"
                            icon={LoaderCircle}
                            accent="orange"
                        />
                    </section>

                    <section className="dashboard-projects-section">
                        <div className="dashboard-section-header">
                            <div>
                                <h2>Recent Projects</h2>
                                <p>
                                    Your recently imported codebases
                                </p>
                            </div>

                            <div className="dashboard-section-actions">
                                <button
                                    className="dashboard-refresh-button"
                                    onClick={fetchDashboardData}
                                    disabled={isLoading}
                                    title="Refresh projects"
                                >
                                    <RefreshCw
                                        size={17}
                                        className={isLoading ? 'refresh-spinning' : ''}
                                    />
                                </button>

                                <button
                                    className="dashboard-view-all-button"
                                    onClick={() => navigate('/dashboard/projects')}
                                >
                                    View all
                                    <ArrowRight size={16} />
                                </button>
                            </div>
                        </div>

                        {isLoading ? (
                            <div className="dashboard-loading">
                                <div className="dashboard-loading-spinner"></div>
                                <p>Loading your projects...</p>
                            </div>
                        ) : error ? (
                            <div className="dashboard-error">
                                <p>{error}</p>

                                <button onClick={fetchDashboardData}>
                                    Try again
                                </button>
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="dashboard-empty-state">
                                <div className="dashboard-empty-icon">
                                    <FolderKanban size={30} />
                                </div>

                                <h3>No projects yet</h3>

                                <p>
                                    Import your first GitHub repository or ZIP project
                                    to start exploring your codebase.
                                </p>

                                <button
                                    className="dashboard-primary-button"
                                    onClick={() => navigate('/dashboard/projects/new')}
                                >
                                    <Plus size={18} />
                                    Import Your First Project
                                </button>
                            </div>
                        ) : (
                            <div className="dashboard-project-grid">
                                {projects.slice(0, 6).map((project) => (
                                    <ProjectCard
                                        key={project.id}
                                        project={project}
                                        onDelete={handleProjectDeleted}
                                    />
                                ))}
                            </div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    )
}

export default DashboardPage
