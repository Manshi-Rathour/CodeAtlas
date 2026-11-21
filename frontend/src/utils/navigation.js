import {
  LayoutDashboard,
  FolderKanban,
} from 'lucide-react'

// Workspace navigation shared by the desktop sidebar and the
// mobile hamburger menu in the top bar.
export const workspaceNavigation = [
  {
    label: 'Overview',
    path: '/dashboard',
    icon: LayoutDashboard,
    available: true,
  },
  {
    label: 'My Projects',
    path: '/dashboard/projects',
    icon: FolderKanban,
    available: true,
  },
]
