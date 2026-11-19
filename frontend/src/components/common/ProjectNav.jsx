import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderOpen,
  MessageSquare,
  Network,
  Sparkles,
  FileText,
  Route,
} from 'lucide-react'

import './ProjectNav.css'

function ProjectNav({ projectId }) {
  const base = `/dashboard/projects/${projectId}`

  const items = [
    { label: 'Overview', path: base, icon: LayoutDashboard, end: true },
    { label: 'Files', path: `${base}/files`, icon: FolderOpen },
    { label: 'AI Chat', path: `${base}/chat`, icon: MessageSquare },
    { label: 'Architecture', path: `${base}/architecture`, icon: Sparkles },
    { label: 'Documentation', path: `${base}/documentation`, icon: FileText },
    { label: 'Dependencies', path: `${base}/graph`, icon: Network },
    { label: 'APIs & Metrics', path: `${base}/apis`, icon: Route },
  ]

  return (
    <nav className="project-tools-nav" aria-label="Project tools">
      {items.map((item) => {
        const Icon = item.icon

        return (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            className={({ isActive }) =>
              `project-tool-tab ${isActive ? 'active' : ''}`
            }
          >
            <Icon size={16} />
            <span>{item.label}</span>
          </NavLink>
        )
      })}
    </nav>
  )
}

export default ProjectNav
