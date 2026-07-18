import axios from 'axios'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  notifySessionExpired,
  setTokens,
} from './tokenStore'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({ baseURL })

// A separate, interceptor-free client for the refresh call itself —
// otherwise a 401 on /auth/refresh would trigger the response
// interceptor below and recurse into itself.
const refreshClient = axios.create({ baseURL })

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise = null

/**
 * Ensures only one /auth/refresh call is ever in flight at a time — if
 * five requests 401 at once (e.g. a burst of dashboard widgets loading
 * right as the access token expires), they all await the same refresh
 * instead of each independently rotating the refresh token and
 * invalidating each other's attempt.
 */
async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }
      const { data } = await refreshClient.post('/auth/refresh', {
        refresh_token: refreshToken,
      })
      setTokens(data)
      return data.access_token
    })().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    const isAuthEndpoint = config?.url?.startsWith('/auth/')

    if (response?.status === 401 && !config._retried && !isAuthEndpoint) {
      config._retried = true
      try {
        const newAccessToken = await refreshAccessToken()
        config.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(config)
      } catch (refreshError) {
        clearTokens()
        notifySessionExpired()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

/**
 * Extracts a human-readable message from a FastAPI error response.
 * FastAPI's HTTPException detail is usually a plain string, but
 * validation errors (422) come back as a list of {loc, msg, type}.
 */
export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const detail = error?.response?.data?.detail
  if (!detail) return error?.message || fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  }
  return fallback
}
