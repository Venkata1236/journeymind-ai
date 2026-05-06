import axios from 'axios'

const BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

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

export const planTrip = async (tripRequest) => {
  const response = await api.post('/plan-trip', tripRequest)
  return response.data
}

export const getHistory = async (limit = 20, offset = 0) => {
  const response = await api.get('/history', {
    params: { limit, offset },
  })
  return response.data
}

export const getTripById = async (tripId) => {
  const response = await api.get(`/history/${tripId}`)
  return response.data
}

export const deleteTrip = async (tripId) => {
  await api.delete(`/history/${tripId}`)
}

export const checkHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

export default api