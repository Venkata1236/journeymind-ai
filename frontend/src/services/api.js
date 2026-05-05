import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 minutes — crew takes time
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Request Interceptor ──────────────────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// ─── Response Interceptor ─────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'Something went wrong'
    console.error(`[API Error] ${message}`)
    return Promise.reject(new Error(message))
  }
)


// ─── Trip Planning ────────────────────────────────────────────────────────────

export const planTrip = async (tripRequest) => {
  const response = await api.post('/api/plan-trip', tripRequest)
  return response.data
}


// ─── History ──────────────────────────────────────────────────────────────────

export const getHistory = async (limit = 20, offset = 0) => {
  const response = await api.get('/api/history', {
    params: { limit, offset },
  })
  return response.data
}

export const getTripById = async (tripId) => {
  const response = await api.get(`/api/history/${tripId}`)
  return response.data
}

export const deleteTrip = async (tripId) => {
  await api.delete(`/api/history/${tripId}`)
}


// ─── Health ───────────────────────────────────────────────────────────────────

export const checkHealth = async () => {
  const response = await api.get('/health')
  return response.data
}