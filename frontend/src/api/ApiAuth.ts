import { apiClient } from '../lib/api'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    username: string
    email: string
    is_verified: boolean
  }
}

export interface User {
  id: string
  username: string
  email: string
  is_verified: boolean
}

class ApiAuth {
  // Login
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post('/auth/login', {
      email: credentials.username,
      password: credentials.password
    })
    
    return response.data
  }

  // Register
  async register(userData: RegisterRequest): Promise<{ message: string }> {
    const response = await apiClient.post('/auth/register', userData)
    return response.data
  }

  // Verify email
  async verifyEmail(token: string): Promise<{ message: string }> {
    const response = await apiClient.post('/auth/verify-email', { token })
    return response.data
  }

  // Get current user
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/me')
    return response.data
  }

  // Resend verification email
  async resendVerification(email: string): Promise<{ message: string }> {
    const response = await apiClient.post('/auth/resend-verification', { email })
    return response.data
  }
}

export const apiAuth = new ApiAuth()
export default apiAuth
