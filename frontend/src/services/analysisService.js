import api from './api'

const analyzeProject = async (projectId) => {
  const response = await api.post(
    `/api/projects/${projectId}/analyze`
  )

  return response.data
}

const getProjectAnalysis = async (projectId) => {
  const response = await api.get(
    `/api/projects/${projectId}/analysis`
  )

  return response.data
}

const analysisService = {
  analyzeProject,
  getProjectAnalysis,
}

export default analysisService
