export interface Transaction {
  id: number
  transaction_id: string
  account_id: number
  category_id?: number
  date: string
  amount: number
  description: string
  payee?: string
  narration?: string
  currency: string
  pending: boolean
  reviewed: boolean
  beancount_account?: string
  plaid_transaction_id?: string
  synced_to_beancount: boolean
  created_at: string
  updated_at: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Account {
  id: number
  account_id: string
  name: string
  official_name?: string
  type: string
  subtype?: string
  beancount_account: string
  plaid_account_id?: string
  institution_name?: string
  current_balance?: number
  available_balance?: number
  currency: string
  active: boolean
  needs_reconnection: boolean
  last_synced_at?: string
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  name: string
  display_name: string
  beancount_account: string
  category_type: string
  parent_category?: string
  icon?: string
  color?: string
  description?: string
  created_at: string
  updated_at: string
}

export interface Rule {
  id: number
  name: string
  description?: string
  conditions: Record<string, any>
  actions: Record<string, any>
  category_id?: number
  priority: number
  active: boolean
  match_count: number
  last_matched_at?: string
  created_at: string
  updated_at: string
}

export interface TransactionFilters {
  page?: number
  page_size?: number
  account_id?: number
  category_id?: number
  start_date?: string
  end_date?: string
  search?: string
}
