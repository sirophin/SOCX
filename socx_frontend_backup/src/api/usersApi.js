import { apiClient } from './client'

export const usersApi = {
  list: () => apiClient.get('/users').then((r) => r.data),

  deactivate: (id) => apiClient.patch(`/users/${id}/deactivate`).then((r) => r.data),
}
