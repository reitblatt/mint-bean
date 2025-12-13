import { apiClient } from './client'

export interface ExportCountResponse {
  count: number
}

export const beancountApi = {
  exportFile: async (reviewedOnly = true, excludePending = true): Promise<Blob> => {
    const response = await apiClient.get('/beancount/export', {
      params: {
        reviewed_only: reviewedOnly,
        exclude_pending: excludePending,
      },
      responseType: 'blob',
    })
    return response.data
  },

  getExportCount: async (reviewedOnly = true, excludePending = true): Promise<ExportCountResponse> => {
    const response = await apiClient.get('/beancount/export-count', {
      params: {
        reviewed_only: reviewedOnly,
        exclude_pending: excludePending,
      },
    })
    return response.data
  },
}
