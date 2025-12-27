export interface Transaction {
  id: number
  transaction_id: string
  account_id: number
  category_id?: number
  category?: {
    id: number
    display_name: string
  }
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
  conditions: Record<string, unknown>
  actions: Record<string, unknown>
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
  limit?: number
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
  category: Category  // Full category object
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

// Dashboard types
export interface DashboardWidget {
  id: number
  tab_id: number
  widget_type: string
  title: string
  grid_row: number
  grid_col: number
  grid_width: number
  grid_height: number
  config: string | null
  created_at: string
  updated_at: string
}

export interface DashboardTab {
  id: number
  user_id: number
  name: string
  display_order: number
  is_default: boolean
  icon: string | null
  created_at: string
  updated_at: string
}

export interface DashboardTabWithWidgets extends DashboardTab {
  widgets: DashboardWidget[]
}

export interface DashboardTabCreate {
  name: string
  display_order?: number
  is_default?: boolean
  icon?: string
}

export interface DashboardTabUpdate {
  name?: string
  display_order?: number
  is_default?: boolean
  icon?: string
}

export interface DashboardWidgetCreate {
  widget_type: string
  title: string
  grid_row?: number
  grid_col?: number
  grid_width?: number
  grid_height?: number
  config?: string
}

export interface DashboardWidgetUpdate {
  widget_type?: string
  title?: string
  grid_row?: number
  grid_col?: number
  grid_width?: number
  grid_height?: number
  config?: string
}

// Widget configuration types with discriminated unions for type safety

// Enums matching backend
export type MetricType =
  | 'total_balance'
  | 'net_worth'
  | 'total_spending'
  | 'total_income'
  | 'net_income'
  | 'transaction_count'
  | 'uncategorized_count'
  | 'account_count'

export type ChartType = 'line' | 'area' | 'bar' | 'pie'
export type Granularity = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
export type GroupByField = 'category' | 'account' | 'merchant' | 'date' | 'month'

export type FilterOperator =
  | 'eq'
  | 'ne'
  | 'in'
  | 'not_in'
  | 'gt'
  | 'lt'
  | 'contains'
  | 'is_null'
  | 'is_not_null'

export type FilterField =
  | 'amount'
  | 'date'
  | 'category_id'
  | 'account_id'
  | 'merchant_name'
  | 'description'
  | 'pending'
  | 'reviewed'
  | 'plaid_primary_category'
  | 'plaid_detailed_category'

export interface TransactionFilter {
  field: FilterField
  operator: FilterOperator
  value?: unknown
}

// Base widget config
interface BaseWidgetConfig {
  filters?: TransactionFilter[]
}

// Specific widget configs with discriminated union
export interface SummaryCardConfig extends BaseWidgetConfig {
  widget_type: 'summary_card'
  metric: MetricType
}

export interface TimeSeriesConfig extends BaseWidgetConfig {
  widget_type: 'time_series'
  metric: MetricType
  chart_type: ChartType
  granularity: Granularity
}

export interface BreakdownConfig extends BaseWidgetConfig {
  widget_type: 'breakdown'
  metric: MetricType
  group_by: GroupByField
  chart_type: ChartType
  limit: number
}

// Legacy widget types for backwards compatibility
export interface LegacyLineChartConfig {
  widget_type: 'line_chart'
  data_type?: string
  granularity?: string
  limit?: number
}

export interface LegacyPieChartConfig {
  widget_type: 'pie_chart'
  data_type?: string
  limit?: number
}

export interface LegacyBarChartConfig {
  widget_type: 'bar_chart'
  data_type?: string
  granularity?: string
  limit?: number
}

export interface TableConfig {
  widget_type: 'table'
  filters?: {
    limit?: number
    sort?: string
  }
}

// Union type of all possible widget configs
export type WidgetConfig =
  | SummaryCardConfig
  | TimeSeriesConfig
  | BreakdownConfig
  | LegacyLineChartConfig
  | LegacyPieChartConfig
  | LegacyBarChartConfig
  | TableConfig

// Type guard functions
export function isSummaryCardConfig(config: WidgetConfig): config is SummaryCardConfig {
  return config.widget_type === 'summary_card'
}

export function isTimeSeriesConfig(config: WidgetConfig): config is TimeSeriesConfig {
  return config.widget_type === 'time_series'
}

export function isBreakdownConfig(config: WidgetConfig): config is BreakdownConfig {
  return config.widget_type === 'breakdown'
}

export function isLegacyLineChartConfig(config: WidgetConfig): config is LegacyLineChartConfig {
  return config.widget_type === 'line_chart'
}

export function isLegacyPieChartConfig(config: WidgetConfig): config is LegacyPieChartConfig {
  return config.widget_type === 'pie_chart'
}

export function isLegacyBarChartConfig(config: WidgetConfig): config is LegacyBarChartConfig {
  return config.widget_type === 'bar_chart'
}

export function isTableConfig(config: WidgetConfig): config is TableConfig {
  return config.widget_type === 'table'
}

// Deprecated - kept for backwards compatibility
export interface WidgetConfigLegacy {
  metric?: string
  data_type?: string
  granularity?: string
  limit?: number
  filters?: Record<string, unknown>
}

// Analytics types
export interface SummaryMetrics {
  total_balance: number
  total_spending: number
  total_income: number
  transaction_count: number
  uncategorized_count: number
  account_count: number
}

export interface TimeSeriesDataPoint {
  date: string
  value: number
  label?: string
}

export interface TimeSeriesResponse {
  data: TimeSeriesDataPoint[]
  granularity: string
}

export interface CategoryBreakdown {
  category_id: number | null
  category_name: string
  amount: number
  transaction_count: number
  percentage: number
}

export interface CategoryBreakdownResponse {
  data: CategoryBreakdown[]
  total_amount: number
}

export interface MerchantBreakdown {
  merchant_name: string
  amount: number
  transaction_count: number
  percentage: number
}

export interface MerchantBreakdownResponse {
  data: MerchantBreakdown[]
  total_amount: number
}
