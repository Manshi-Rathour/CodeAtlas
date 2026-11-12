
import { createContext, useCallback, useEffect, useState } from 'react'
import authService from '../services/authService'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  // Restore the user's session when the application loads.
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
    } catch (error) {
      authService.logout()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Login an existing user.
  const login = async (credentials) => {
    const response = await authService.login(credentials)
    setUser(response.user)
    return response.user
  }

  // Register a new user.
  const signup = async (userData) => {
    const response = await authService.signup(userData)
    setUser(response.user)
    return response.user
  }

  // Logout the current user.
  const logout = () => {
    authService.logout()
    setUser(null)
  }

  const value = {
    user,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    signup,
    logout,
    checkAuth,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
