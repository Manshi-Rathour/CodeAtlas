import api from './api'

const documentationService = {
  getDocumentation: async (projectId) => {
    const response = await api.get(
      `/api/projects/${projectId}/documentation`
    )

    return response.data
  },

  getStatus: async (projectId) => {
    const response = await api.get(
      `/api/projects/${projectId}/documentation/status`
    )

    return response.data
  },

  generateDocumentation: async (projectId) => {
    const response = await api.post(
      `/api/projects/${projectId}/documentation`,
      null,
      { timeout: 0 }
    )

    return response.data
  },
}

export default documentationService
