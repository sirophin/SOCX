import { apiClient } from './client'

export const investigationApi = {
  list: (filters = {}) =>
    apiClient
      .get('/investigation/entries', {
        params: {
          username: filters.username || undefined,
          source_ip: filters.sourceIp || undefined,
          hostname: filters.hostname || undefined,
          event_id: filters.eventId || undefined,
          severity: filters.severity || undefined,
          timestamp_from: filters.timestampFrom || undefined,
          timestamp_to: filters.timestampTo || undefined,
          log_id: filters.logId || undefined,
          limit: filters.limit ?? 50,
          offset: filters.offset ?? 0,
        },
      })
      .then((r) => r.data),

  get: (id) => apiClient.get(`/investigation/entries/${id}`).then((r) => r.data),
}
