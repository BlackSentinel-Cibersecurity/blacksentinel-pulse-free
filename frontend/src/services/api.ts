import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

type RetriableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean }

let isRefreshing = false
let failedQueue: Array<{ resolve: (value: string | null) => void; reject: (reason?: unknown) => void }> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Request interceptor - never logs or exposes tokens
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableRequestConfig

    // Skip interceptor for login/register/refresh endpoints - let caller handle errors
    const url = originalRequest?.url || ''
    if (url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh') || url.includes('/setup/')) {
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = useAuthStore.getState().refreshToken
      if (!refreshToken) {
        useAuthStore.getState().logout()
        // Soft redirect instead of hard reload
        window.location.replace('/login')
        isRefreshing = false
        return Promise.reject(error)
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token: newRefreshToken, user: userData } = response.data
        useAuthStore.getState().login(access_token, newRefreshToken, userData || useAuthStore.getState().user!)

        originalRequest.headers.Authorization = `Bearer ${access_token}`
        processQueue(null, access_token)
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        useAuthStore.getState().logout()
        window.location.replace('/login')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (username: string, password: string, totp_code?: string) =>
    api.post('/auth/login', { username, password, totp_code }),
  register: (data: { email: string; username: string; password: string; full_name: string }) =>
    api.post('/auth/register', data),
  refreshToken: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
  getMe: () => api.get('/auth/me'),
  changePassword: (current_password: string, new_password: string) =>
    api.post('/auth/change-password', { current_password, new_password }),
  forceChangePassword: (new_password: string) =>
    api.post('/auth/force-change-password', { new_password }),
  setupTOTP: () => api.post('/auth/totp/setup'),
  verifyTOTP: (code: string) => api.post('/auth/totp/verify', { code }),
  disableTOTP: () => api.post('/auth/totp/disable'),
}

// Health API
export const healthAPI = {
  check: () => api.get('/health'),
  readiness: () => api.get('/health/ready'),
}

// Assets API
export const assetsAPI = {
  list: (params?: Record<string, string | number | boolean | undefined>) => api.get('/assets', { params }),
  get: (id: number) => api.get(`/assets/${id}`),
  create: (data: Record<string, unknown>) => api.post('/assets', data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/assets/${id}`, data),
  delete: (id: number) => api.delete(`/assets/${id}`),
  getStats: () => api.get('/assets/stats'),
  getRelated: (id: number, depth?: number) =>
    api.get(`/assets/${id}/related`, { params: { depth } }),
}

// Scans API
export const scansAPI = {
  list: (params?: Record<string, string | number | boolean | undefined>) => api.get('/scans', { params }),
  get: (id: string) => api.get(`/scans/${id}`),
  create: (data: Record<string, unknown>) => api.post('/scans', data),
  cancel: (id: string) => api.post(`/scans/${id}/cancel`),
  getResults: (id: string) => api.get(`/scans/${id}/results`),
}

// Vulnerabilities API
export const vulnsAPI = {
  list: (params?: Record<string, string | number | boolean | undefined>) => api.get('/vulnerabilities', { params }),
  get: (id: number) => api.get(`/vulnerabilities/${id}`),
  getStats: () => api.get('/vulnerabilities/stats'),
  updateStatus: (id: number, status: string) =>
    api.put(`/vulnerabilities/${id}/status`, { status }),
}

// Alerts API
export const alertsAPI = {
  list: (params?: Record<string, string | number | boolean | undefined>) => api.get('/alerts', { params }),
  get: (id: string) => api.get(`/alerts/${id}`),
  getStats: () => api.get('/alerts/stats'),
  acknowledge: (id: string) => api.put(`/alerts/${id}/acknowledge`),
  resolve: (id: string, notes?: string) =>
    api.put(`/alerts/${id}/resolve`, { notes }),
  markFalsePositive: (id: string) => api.put(`/alerts/${id}/false-positive`),
}

// Dashboard API
export const dashboardAPI = {
  getData: (days?: number) => api.get('/dashboard', { params: { days } }),
  getRealtime: () => api.get('/dashboard/realtime'),
}

// Discovery API
export const discoveryAPI = {
  start: (data: Record<string, unknown>) => api.post('/discovery/start', data),
  getStatus: (id: string) => api.get(`/discovery/status/${id}`),
  getResults: (id: string) => api.get(`/discovery/results/${id}`),
  scanDomain: (domain: string, deep?: boolean) =>
    api.post(`/discovery/scan-domain?domain=${domain}&deep=${deep || false}`),
  scanIP: (ip: string, ports?: string) =>
    api.post(`/discovery/scan-ip?ip_range=${ip}&ports=${ports || 'top-1000'}`),
  scanCloud: (provider: string, credentials: Record<string, string>) =>
    api.post('/discovery/scan-cloud', { provider, credentials }),
  getCapabilities: () => api.get('/discovery/capabilities'),
}

// Integrations API
export const integrationsAPI = {
  list: () => api.get('/integrations'),
  configure: (data: { provider: string; name: string; config: Record<string, string>; is_enabled?: boolean }) =>
    api.post('/integrations/configure', data),
  get: (provider: string) => api.get(`/integrations/${provider}`),
  test: (provider: string) => api.post(`/integrations/${provider}/test`),
  sync: (provider: string) => api.post(`/integrations/${provider}/sync`),
  delete: (provider: string) => api.delete(`/integrations/${provider}`),
}

// Reports API
export const reportsAPI = {
  getExecutive: (days?: number) =>
    api.get('/reports/executive', { params: { days } }),
  getAssets: () => api.get('/reports/assets'),
}

// Users API
export const usersAPI = {
  list: () => api.get('/users'),
  get: (id: number) => api.get(`/users/${id}`),
  create: (data: { email: string; first_name: string; last_name: string; role: string }) =>
    api.post('/users', data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
}

// WebSocket helper - uses first-message auth instead of query string
export const createWebSocket = (): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws`)

  // Send auth as first message after connection opens
  ws.onopen = () => {
    const token = useAuthStore.getState().token
    if (token) {
      ws.send(JSON.stringify({ type: 'auth', token }))
    }
  }

  return ws
}

export default api
