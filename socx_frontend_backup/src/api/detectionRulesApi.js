import { apiClient } from './client'

export const detectionRulesApi = {
  list: ({ enabled, severity, limit = 50, offset = 0 } = {}) =>
    apiClient
      .get('/detection-rules', { params: { enabled, severity, limit, offset } })
      .then((r) => r.data),

  get: (id) => apiClient.get(`/detection-rules/${id}`).then((r) => r.data),

  create: (payload) => apiClient.post('/detection-rules', payload).then((r) => r.data),

  update: (id, payload) =>
    apiClient.patch(`/detection-rules/${id}`, payload).then((r) => r.data),

  remove: (id) => apiClient.delete(`/detection-rules/${id}`),
}
