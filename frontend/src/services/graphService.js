import api from './api'

const graphService = {
  // Internal file dependency graph.
  getGraph: async (projectId) => {
    const response = await api.get(
      `/api/projects/${projectId}/graph`
    )

    return response.data
  },
}

export default graphService
