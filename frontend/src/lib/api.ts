import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'

// Configuración base de la API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

// Crear instancia de axios
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  // Allow a bit more time in dev to avoid spurious timeouts when the backend is busy
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para agregar el token de autorización
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const tk = localStorage.getItem('access_token') || localStorage.getItem('token')
    if (tk && config.headers) {
      config.headers.Authorization = `Bearer ${tk}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar respuestas y errores
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Si el token expiró o es inválido, limpiar el localStorage
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      // Opcional: redirigir al login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
