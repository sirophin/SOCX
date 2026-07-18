import { apiClient } from './client'

export const alertsApi = {
  list: ({ severity, status, source, ruleId, analystId, limit = 50, offset = 0 } = {}) =>
    apiClient
      .get('/alerts', {
        params: {
          severity: severity || undefined,
          status: status || undefined,
          source: source || undefined,
          rule_id: ruleId || undefined,
          analyst_id: analystId || undefined,
          limit,
          offset,
        },
      })
      .then((r) => r.data),

  get: (id) => apiClient.get(`/alerts/${id}`).then((r) => r.data),

  acknowledge: (id) => apiClient.patch(`/alerts/${id}/acknowledge`).then((r) => r.data),

  close: (id) => apiClient.patch(`/alerts/${id}/close`).then((r) => r.data),
}
