import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiAuth, type User, type LoginRequest, type RegisterRequest } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUser(userData: User) {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function login(email: string, password: string) {
    try {
      loading.value = true
      error.value = null
      
      const response = await apiAuth.login({ username: email, password })
      setToken(response.access_token)
      setUser(response.user)
      
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error al iniciar sesión'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, email: string, password: string) {
    try {
      loading.value = true
      error.value = null
      
      const response = await apiAuth.register({ username, email, password })
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error al registrarse'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function verifyEmail(token: string) {
    try {
      loading.value = true
      error.value = null
      
      const response = await apiAuth.verifyEmail(token)
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error al verificar email'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function resendVerification(email: string) {
    try {
      loading.value = true
      error.value = null
      
      const response = await apiAuth.resendVerification(email)
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error al reenviar verificación'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getCurrentUser() {
    if (!token.value) return null
    
    try {
      const userData = await apiAuth.getCurrentUser()
      setUser(userData)
      return userData
    } catch (error) {
      // If token is invalid, logout
      logout()
      throw error
    }
  }

  // Initialize user if token exists
  if (token.value) {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      user.value = JSON.parse(savedUser)
    }
    // Optionally refresh user data
    getCurrentUser().catch(() => {
      // If token is invalid, logout silently
      logout()
    })
  }

  return {
    token,
    user,
    loading,
    error,
    isAuthenticated,
    setToken,
    setUser,
    logout,
    login,
    register,
    verifyEmail,
    resendVerification,
    getCurrentUser
  }
})
