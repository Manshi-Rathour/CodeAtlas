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

const getProjectApis = async (projectId) => {
  const response = await api.get(
    `/api/projects/${projectId}/apis`
  )

  return response.data
}

const getProjectMetrics = async (projectId) => {
  const response = await api.get(
    `/api/projects/${projectId}/metrics`
  )

  return response.data
}

const analysisService = {
  analyzeProject,
  getProjectAnalysis,
  getProjectApis,
  getProjectMetrics,
}

export default analysisService
