
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

  // Update the signed-in user's profile details
  updateProfile: async (profileData) => {
    const response = await api.patch('/api/users/me', profileData)
    return response.data
  },

  // Change password without email verification
  changePassword: async (passwordData) => {
    const response = await api.post(
      '/api/users/me/password',
      passwordData
    )

    return response.data
  },

  // Permanently delete the signed-in user's account
  deleteAccount: async () => {
    const response = await api.delete('/api/users/me')
    return response.data
  },

  // Logout the user
  logout: () => {
    localStorage.removeItem('access_token')
  },
}

export default authService
