import { apiClient } from './client'

// Source types the backend's upload module actually accepts (see
// app/core/file_validation.py ACCEPTED_SOURCE_TYPES on the backend —
// windows_security and application_log exist in the DB enum for future
// modules but are rejected with 415 by the upload endpoint today).
export const UPLOADABLE_SOURCE_TYPES = [
  { value: 'evtx', label: 'Windows EVTX', extensions: '.evtx' },
  { value: 'linux_auth_log', label: 'Linux auth.log', extensions: '.log, .txt' },
  { value: 'apache_access', label: 'Apache Access Log', extensions: '.log, .txt' },
  { value: 'nginx', label: 'Nginx Access Log', extensions: '.log, .txt' },
  { value: 'json', label: 'JSON', extensions: '.json' },
  { value: 'csv', label: 'CSV', extensions: '.csv' },
]

export const logsApi = {
  upload: (file, sourceType, onUploadProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_type', sourceType)
    return apiClient
      .post('/logs/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress,
      })
      .then((r) => r.data)
  },

  list: ({ sourceType, mineOnly, limit = 50, offset = 0 } = {}) =>
    apiClient
      .get('/logs', {
        params: {
          source_type: sourceType || undefined,
          mine_only: mineOnly || undefined,
          limit,
          offset,
        },
      })
      .then((r) => r.data),

  get: (id) => apiClient.get(`/logs/${id}`).then((r) => r.data),

  parse: (id, force = false) =>
    apiClient.post(`/logs/${id}/parse`, { force }).then((r) => r.data),
}
