
import api from './api'

const authService = {
  // Register a new user
  signup: async (userData) => {
    const response = await api.post('/api/auth/signup', userData)

    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
    }

    return response.data
  },

  // Login an existing user
  login: async (credentials) => {
    const response = await api.post('/api/auth/login', credentials)

    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
    }

    return response.data
  },

  // Fetch the currently authenticated user
  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  // Logout the user
  logout: () => {
    localStorage.removeItem('access_token')
  },
}

export default authService
