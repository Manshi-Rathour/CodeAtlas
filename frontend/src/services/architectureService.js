import api from './api'

const architectureService = {
  // Database-derived architecture facts, optionally with AI explanation.
  getArchitecture: async (projectId, includeAi = false) => {
    const response = await api.get(
      `/api/projects/${projectId}/architecture`,
      { params: { include_ai: includeAi } }
    )

    return response.data
  },
}

export default architectureService
