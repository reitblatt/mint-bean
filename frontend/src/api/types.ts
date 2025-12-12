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
  plaid_primary_category?: string
  plaid_detailed_category?: string
  plaid_confidence_level?: string
  merchant_name?: string
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
  parent_id?: number
  icon?: string
  color?: string
  description?: string
  display_order: number
  is_active: boolean
  is_system: boolean
  transaction_count: number
  last_used_at?: string
  created_at: string
  updated_at: string
}

export interface CategoryTreeNode {
  id: number
  name: string
  display_name: string
  category_type: string
  icon?: string
  color?: string
  parent_id?: number
  transaction_count: number
  children: CategoryTreeNode[]
}

export interface CategoryMergeRequest {
  source_category_ids: number[]
  target_category_id: number
  delete_source_categories?: boolean
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

export interface PlaidCategoryMapping {
  id: number
  plaid_primary_category: string
  plaid_detailed_category?: string
  category_id: number
  confidence: number
  auto_apply: boolean
  match_count: number
  last_matched_at?: string
  created_at: string
  updated_at: string
}

export interface PlaidCategoryMappingCreate {
  plaid_primary_category: string
  plaid_detailed_category?: string
  category_id: number
  confidence?: number
  auto_apply?: boolean
}

export interface PlaidCategoryMappingUpdate {
  category_id?: number
  confidence?: number
  auto_apply?: boolean
}
