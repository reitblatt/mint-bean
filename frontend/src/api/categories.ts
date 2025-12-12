import { apiClient } from './client'
import type { Category, CategoryTreeNode, CategoryMergeRequest } from './types'

export const categoriesApi = {
  list: async (categoryType?: string): Promise<Category[]> => {
    const { data } = await apiClient.get<Category[]>('/categories', {
      params: categoryType ? { category_type: categoryType } : undefined,
    })
    return data
  },

  tree: async (categoryType?: string, includeInactive?: boolean): Promise<CategoryTreeNode[]> => {
    const { data } = await apiClient.get<CategoryTreeNode[]>('/categories/tree', {
      params: {
        ...(categoryType && { category_type: categoryType }),
        ...(includeInactive !== undefined && { include_inactive: includeInactive }),
      },
    })
    return data
  },

  get: async (id: number): Promise<Category> => {
    const { data } = await apiClient.get<Category>(`/categories/${id}`)
    return data
  },

  create: async (category: Partial<Category>): Promise<Category> => {
    const { data } = await apiClient.post<Category>('/categories', category)
    return data
  },

  update: async (id: number, updates: Partial<Category>): Promise<Category> => {
    const { data } = await apiClient.patch<Category>(`/categories/${id}`, updates)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`)
  },

  merge: async (request: CategoryMergeRequest): Promise<Category> => {
    const { data } = await apiClient.post<Category>('/categories/merge', request)
    return data
  },

  refreshStats: async (id: number): Promise<Category> => {
    const { data } = await apiClient.post<Category>(`/categories/${id}/refresh-stats`)
    return data
  },
}
