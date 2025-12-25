import { apiClient } from './client'
import type {
  CategoryBreakdownResponse,
  MerchantBreakdownResponse,
  SummaryMetrics,
  TimeSeriesResponse,
} from './types'

export interface AnalyticsParams {
  start_date?: string
  end_date?: string
  granularity?: string
  limit?: number
}

export const analyticsApi = {
  getSummaryMetrics: async (params?: AnalyticsParams): Promise<SummaryMetrics> => {
    const response = await apiClient.get<SummaryMetrics>('/analytics/summary-metrics', { params })
    return response.data
  },

  getSpendingOverTime: async (params?: AnalyticsParams): Promise<TimeSeriesResponse> => {
    const response = await apiClient.get<TimeSeriesResponse>('/analytics/spending-over-time', {
      params,
    })
    return response.data
  },

  getSpendingByCategory: async (params?: AnalyticsParams): Promise<CategoryBreakdownResponse> => {
    const response = await apiClient.get<CategoryBreakdownResponse>(
      '/analytics/spending-by-category',
      { params },
    )
    return response.data
  },

  getSpendingByMerchant: async (params?: AnalyticsParams): Promise<MerchantBreakdownResponse> => {
    const response = await apiClient.get<MerchantBreakdownResponse>(
      '/analytics/spending-by-merchant',
      { params },
    )
    return response.data
  },
}
