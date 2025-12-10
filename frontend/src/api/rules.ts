import { apiClient } from './client'
import type { Rule } from './types'

export const rulesApi = {
  list: async (activeOnly = true): Promise<Rule[]> => {
    const { data } = await apiClient.get<Rule[]>('/rules', {
      params: { active_only: activeOnly },
    })
    return data
  },

  get: async (id: number): Promise<Rule> => {
    const { data } = await apiClient.get<Rule>(`/rules/${id}`)
    return data
  },

  create: async (rule: Partial<Rule>): Promise<Rule> => {
    const { data } = await apiClient.post<Rule>('/rules', rule)
    return data
  },

  update: async (id: number, updates: Partial<Rule>): Promise<Rule> => {
    const { data } = await apiClient.patch<Rule>(`/rules/${id}`, updates)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/rules/${id}`)
  },
}
