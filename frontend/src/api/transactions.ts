import { apiClient } from './client'
import type { Transaction, TransactionListResponse, TransactionFilters } from './types'

export const transactionsApi = {
  list: async (filters?: TransactionFilters): Promise<TransactionListResponse> => {
    const { data } = await apiClient.get<TransactionListResponse>('/transactions', {
      params: filters,
    })
    return data
  },

  get: async (id: number): Promise<Transaction> => {
    const { data } = await apiClient.get<Transaction>(`/transactions/${id}`)
    return data
  },

  update: async (id: number, updates: Partial<Transaction>): Promise<Transaction> => {
    const { data } = await apiClient.patch<Transaction>(`/transactions/${id}`, updates)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/transactions/${id}`)
  },
}
