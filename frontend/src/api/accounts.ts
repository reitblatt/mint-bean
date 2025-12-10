import { apiClient } from './client'
import type { Account } from './types'

export const accountsApi = {
  list: async (activeOnly = true): Promise<Account[]> => {
    const { data } = await apiClient.get<Account[]>('/accounts', {
      params: { active_only: activeOnly },
    })
    return data
  },

  get: async (id: number): Promise<Account> => {
    const { data } = await apiClient.get<Account>(`/accounts/${id}`)
    return data
  },

  update: async (id: number, updates: Partial<Account>): Promise<Account> => {
    const { data } = await apiClient.patch<Account>(`/accounts/${id}`, updates)
    return data
  },
}
