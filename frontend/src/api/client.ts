import axios from 'axios'

// Runtime config injected by Docker container at startup
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: {
      apiUrl: string
    }
  }
}

// Priority: Runtime config > Build-time env var > Development default
const getApiBaseUrl = (): string => {
  // Check for runtime config first (production)
  if (window.__RUNTIME_CONFIG__?.apiUrl) {
    return window.__RUNTIME_CONFIG__.apiUrl
  }
  // Fall back to build-time env var (if set)
  if (import.meta.env.VITE_API_URL) {
    return `${import.meta.env.VITE_API_URL}/api/v1`
  }
  // Development default
  return 'http://localhost:8000/api/v1'
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Don't redirect if we're checking onboarding status or completing onboarding
      const isOnboardingEndpoint = error.config?.url?.includes('/onboarding')

      if (!isOnboardingEndpoint) {
        // Handle unauthorized - clear auth and redirect to login
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    } else if (error.response?.status === 500) {
      console.error('Server error:', error.response.data)
    }
    return Promise.reject(error)
  }
)
