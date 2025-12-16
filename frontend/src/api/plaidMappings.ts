import { apiClient } from './client'
import type {
  PlaidCategoryMapping,
  PlaidCategoryMappingCreate,
  PlaidCategoryMappingUpdate,
} from './types'

export const plaidMappingsApi = {
  list: async (filters?: {
    plaid_primary_category?: string
    auto_apply_only?: boolean
  }): Promise<PlaidCategoryMapping[]> => {
    const params = new URLSearchParams()
    if (filters?.plaid_primary_category) {
      params.append('plaid_primary_category', filters.plaid_primary_category)
    }
    if (filters?.auto_apply_only) {
      params.append('auto_apply_only', 'true')
    }

    const queryString = params.toString()
    const url = `/plaid-category-mappings${queryString ? `?${queryString}` : ''}`
    const response = await apiClient.get<PlaidCategoryMapping[]>(url)
    return response.data
  },

  get: async (id: number): Promise<PlaidCategoryMapping> => {
    const response = await apiClient.get<PlaidCategoryMapping>(
      `/plaid-category-mappings/${id}`
    )
    return response.data
  },

  create: async (mapping: PlaidCategoryMappingCreate): Promise<PlaidCategoryMapping> => {
    const response = await apiClient.post<PlaidCategoryMapping>(
      '/plaid-category-mappings',
      mapping
    )
    return response.data
  },

  update: async (id: number, updates: PlaidCategoryMappingUpdate): Promise<PlaidCategoryMapping> => {
    const response = await apiClient.patch<PlaidCategoryMapping>(
      `/plaid-category-mappings/${id}`,
      updates
    )
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/plaid-category-mappings/${id}`)
  },

  bulkCreate: async (
    mappings: PlaidCategoryMappingCreate[],
    skipExisting = true
  ): Promise<PlaidCategoryMapping[]> => {
    const response = await apiClient.post<PlaidCategoryMapping[]>(
      `/plaid-category-mappings/bulk?skip_existing=${skipExisting}`,
      mappings
    )
    return response.data
  },
}
