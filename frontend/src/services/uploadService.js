
import api from './api'

const uploadService = {
    uploadZip: async (projectData, file) => {
        const formData = new FormData()

        formData.append('name', projectData.name)
        formData.append('description', projectData.description || '')
        formData.append('file', file)

        const response = await api.post(
            '/api/uploads/zip',
            formData,
            {
                headers: {
                    'Content-Type': undefined,
                },
            }
        )

        return response.data
    },

    importGitHub: async (projectData) => {
        const response = await api.post(
            '/api/github/import',
            projectData
        )

        return response.data
    },
}

export default uploadService
