import { apiClient } from './client'

export interface SyncResponse {
  synced: number
  failed: number
  message: string
}

export interface UnsyncedCountResponse {
  count: number
}

export const beancountApi = {
  syncToFile: async (): Promise<SyncResponse> => {
    const response = await apiClient.post('/beancount/sync-to-file')
    return response.data
  },

  getUnsyncedCount: async (): Promise<UnsyncedCountResponse> => {
    const response = await apiClient.get('/beancount/unsynced-count')
    return response.data
  },
}
