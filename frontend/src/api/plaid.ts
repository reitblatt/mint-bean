import { apiClient } from './client'

export interface PlaidLinkTokenResponse {
  link_token: string
  expiration: string
}

export interface PlaidItem {
  id: number
  item_id: string
  institution_id: string | null
  institution_name: string | null
  is_active: boolean
  needs_update: boolean
  error_code: string | null
  created_at: string
  updated_at: string
  last_synced_at: string | null
}

export interface PublicTokenExchangeResponse {
  item_id: string
  institution_id: string | null
  institution_name: string | null
}

export interface TransactionsSyncResponse {
  added: number
  modified: number
  removed: number
  cursor: string
}

export const plaidApi = {
  createLinkToken: async (): Promise<PlaidLinkTokenResponse> => {
    const { data } = await apiClient.post<PlaidLinkTokenResponse>('/plaid/link/token/create', {
      user_id: 'user-1',
    })
    return data
  },

  exchangePublicToken: async (publicToken: string): Promise<PublicTokenExchangeResponse> => {
    const { data } = await apiClient.post<PublicTokenExchangeResponse>(
      '/plaid/item/public_token/exchange',
      { public_token: publicToken }
    )
    return data
  },

  listItems: async (): Promise<PlaidItem[]> => {
    const { data } = await apiClient.get<PlaidItem[]>('/plaid/items')
    return data
  },

  syncTransactions: async (itemId: number): Promise<TransactionsSyncResponse> => {
    const { data} = await apiClient.post<TransactionsSyncResponse>(`/plaid/items/${itemId}/sync`)
    return data
  },

  deleteItem: async (itemId: number): Promise<void> => {
    await apiClient.delete(`/plaid/items/${itemId}`)
  },
}
