
import api from './api'

const projectService = {
  // Fetch all projects belonging to the logged-in user.
  getProjects: async () => {
    const response = await api.get('/api/projects/')
    return response.data
  },

  // Fetch projects with file counts in one request (dashboard).
  getProjectSummaries: async () => {
    const response = await api.get('/api/projects/summary')
    return response.data
  },

  // Fetch a particular project.
  getProject: async (projectId) => {
    const response = await api.get(`/api/projects/${projectId}`)
    return response.data
  },

  // Create a new project.
  createProject: async (projectData) => {
    const response = await api.post('/api/projects/', projectData)
    return response.data
  },

  // Update an existing project.
  updateProject: async (projectId, projectData) => {
    const response = await api.patch(
      `/api/projects/${projectId}`,
      projectData
    )
    return response.data
  },

  // Delete a project.
  deleteProject: async (projectId) => {
    const response = await api.delete(`/api/projects/${projectId}`)
    return response.data
  },

  // Fetch the file inventory of a project.
  getProjectFiles: async (projectId, params = {}) => {
    const response = await api.get(
      `/api/projects/${projectId}/files`,
      { params }
    )
    return response.data
  },

  // Fetch every project file so the explorer can build a folder tree.
  getProjectFileTree: async (projectId, params = {}) => {
    const response = await api.get(
      `/api/projects/${projectId}/file-tree`,
      { params }
    )
    return response.data
  },

  // Retrieves the source code and metadata of a specific project file
  getProjectFileContent: async (projectId, fileId) => {
  const response = await api.get(
    `/api/projects/${projectId}/files/${fileId}/content`
  )

  return response.data
},
}

export default projectService
