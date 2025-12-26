import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { dashboardsApi } from '@/api/dashboards'
import { categoriesApi } from '@/api/categories'
import { accountsApi } from '@/api/accounts'
import type { DashboardWidget } from '@/api/types'

interface FlexibleWidgetEditorProps {
  isOpen: boolean
  onClose: () => void
  tabId: number
  widget?: DashboardWidget
}

// Widget types
type WidgetType = 'summary_card' | 'time_series' | 'breakdown'

// Metric types
type MetricType =
  | 'total_balance'
  | 'net_worth'
  | 'total_spending'
  | 'total_income'
  | 'net_income'
  | 'transaction_count'
  | 'uncategorized_count'
  | 'account_count'

// Chart types
type ChartType = 'line' | 'bar' | 'pie' | 'area'

// Granularity
type Granularity = 'daily' | 'weekly' | 'monthly' | 'yearly'

// Group by fields
type GroupByField =
  | 'category'
  | 'merchant'
  | 'account'
  | 'plaid_primary_category'
  | 'plaid_detailed_category'

// Filter operators
type FilterOperator =
  | 'eq'
  | 'ne'
  | 'in'
  | 'not_in'
  | 'gt'
  | 'lt'
  | 'contains'
  | 'is_null'
  | 'is_not_null'

// Filter fields
type FilterField =
  | 'category_id'
  | 'account_id'
  | 'merchant_name'
  | 'amount'
  | 'description'
  | 'pending'
  | 'reviewed'
  | 'plaid_primary_category'
  | 'plaid_detailed_category'

interface Filter {
  field: FilterField
  operator: FilterOperator
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any
}

interface WidgetConfig {
  widget_type: WidgetType
  metric: MetricType
  chart_type?: ChartType
  granularity?: Granularity
  group_by?: GroupByField
  limit?: number
  filters: Filter[]
}

const METRIC_OPTIONS: { value: MetricType; label: string; description: string }[] = [
  { value: 'total_balance', label: 'Total Balance', description: 'Sum of all account balances' },
  { value: 'net_worth', label: 'Net Worth', description: 'Total net worth' },
  {
    value: 'total_spending',
    label: 'Total Spending',
    description: 'Sum of all expenses (negative transactions)',
  },
  {
    value: 'total_income',
    label: 'Total Income',
    description: 'Sum of all income (positive transactions)',
  },
  { value: 'net_income', label: 'Net Income', description: 'Income minus spending' },
  { value: 'transaction_count', label: 'Transaction Count', description: 'Number of transactions' },
  {
    value: 'uncategorized_count',
    label: 'Uncategorized Count',
    description: 'Number of uncategorized transactions',
  },
  { value: 'account_count', label: 'Account Count', description: 'Number of accounts' },
]

const FILTER_FIELD_OPTIONS: { value: FilterField; label: string }[] = [
  { value: 'category_id', label: 'Category' },
  { value: 'account_id', label: 'Account' },
  { value: 'merchant_name', label: 'Merchant Name' },
  { value: 'amount', label: 'Amount' },
  { value: 'description', label: 'Description' },
  { value: 'pending', label: 'Pending Status' },
  { value: 'reviewed', label: 'Reviewed Status' },
]

const OPERATOR_OPTIONS: { value: FilterOperator; label: string }[] = [
  { value: 'eq', label: 'Equals' },
  { value: 'ne', label: 'Not Equals' },
  { value: 'in', label: 'In List' },
  { value: 'not_in', label: 'Not In List' },
  { value: 'gt', label: 'Greater Than' },
  { value: 'lt', label: 'Less Than' },
  { value: 'contains', label: 'Contains' },
  { value: 'is_null', label: 'Is Empty' },
  { value: 'is_not_null', label: 'Is Not Empty' },
]

export default function FlexibleWidgetEditor({
  isOpen,
  onClose,
  tabId,
  widget,
}: FlexibleWidgetEditorProps) {
  const queryClient = useQueryClient()

  // Fetch categories and accounts for filter dropdowns
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list(),
  })

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list(),
  })

  // Form state
  const [title, setTitle] = useState('')
  const [widgetType, setWidgetType] = useState<WidgetType>('summary_card')
  const [metric, setMetric] = useState<MetricType>('total_spending')
  const [chartType, setChartType] = useState<ChartType>('line')
  const [granularity, setGranularity] = useState<Granularity>('daily')
  const [groupBy, setGroupBy] = useState<GroupByField>('category')
  const [limit, setLimit] = useState(10)
  const [filters, setFilters] = useState<Filter[]>([])
  const [gridRow, setGridRow] = useState(1)
  const [gridCol, setGridCol] = useState(1)
  const [gridWidth, setGridWidth] = useState(2)
  const [gridHeight, setGridHeight] = useState(1)

  // Parse existing widget config
  useEffect(() => {
    if (widget) {
      setTitle(widget.title)
      setGridRow(widget.grid_row)
      setGridCol(widget.grid_col)
      setGridWidth(widget.grid_width)
      setGridHeight(widget.grid_height)

      if (widget.config) {
        try {
          const config = JSON.parse(widget.config) as WidgetConfig
          setWidgetType(config.widget_type)
          setMetric(config.metric)
          if (config.chart_type) setChartType(config.chart_type)
          if (config.granularity) setGranularity(config.granularity)
          if (config.group_by) setGroupBy(config.group_by)
          if (config.limit) setLimit(config.limit)
          if (config.filters) setFilters(config.filters)
        } catch {
          // Ignore parse errors
        }
      }
    } else {
      // Reset for new widget
      setTitle('')
      setWidgetType('summary_card')
      setMetric('total_spending')
      setFilters([])
      setGridRow(1)
      setGridCol(1)
      setGridWidth(2)
      setGridHeight(1)
    }
  }, [widget])

  const createMutation = useMutation({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    mutationFn: (data: any) => dashboardsApi.createWidget(tabId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-tab', tabId] })
      onClose()
    },
  })

  const updateMutation = useMutation({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    mutationFn: (data: any) => dashboardsApi.updateWidget(tabId, widget!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-tab', tabId] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const config: WidgetConfig = {
      widget_type: widgetType,
      metric,
      filters,
    }

    if (widgetType === 'time_series') {
      config.chart_type = chartType
      config.granularity = granularity
    } else if (widgetType === 'breakdown') {
      config.chart_type = chartType
      config.group_by = groupBy
      config.limit = limit
    }

    const widgetData = {
      widget_type: widgetType,
      title,
      grid_row: gridRow,
      grid_col: gridCol,
      grid_width: gridWidth,
      grid_height: gridHeight,
      config: JSON.stringify(config),
    }

    if (widget) {
      updateMutation.mutate(widgetData)
    } else {
      createMutation.mutate(widgetData)
    }
  }

  const addFilter = () => {
    setFilters([...filters, { field: 'category_id', operator: 'not_in', value: [] }])
  }

  const removeFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index))
  }

  const updateFilter = (index: number, updates: Partial<Filter>) => {
    setFilters(filters.map((f, i) => (i === index ? { ...f, ...updates } : f)))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {widget ? 'Edit Widget' : 'Create Custom Widget'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Widget Title *</label>
            <input
              type="text"
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Total Expenses (excluding groceries)"
              required
            />
          </div>

          {/* Widget Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Widget Type *</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setWidgetType('summary_card')}
                className={`p-3 border rounded-lg text-left ${
                  widgetType === 'summary_card'
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium">Summary Card</div>
                <div className="text-xs text-gray-500">Single metric value</div>
              </button>
              <button
                type="button"
                onClick={() => setWidgetType('time_series')}
                className={`p-3 border rounded-lg text-left ${
                  widgetType === 'time_series'
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium">Time Series</div>
                <div className="text-xs text-gray-500">Trend over time</div>
              </button>
              <button
                type="button"
                onClick={() => setWidgetType('breakdown')}
                className={`p-3 border rounded-lg text-left ${
                  widgetType === 'breakdown'
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium">Breakdown</div>
                <div className="text-xs text-gray-500">Group by field</div>
              </button>
            </div>
          </div>

          {/* Metric */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Metric *</label>
            <select
              className="input"
              value={metric}
              onChange={(e) => setMetric(e.target.value as MetricType)}
              required
            >
              {METRIC_OPTIONS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label} - {m.description}
                </option>
              ))}
            </select>
          </div>

          {/* Time Series Options */}
          {widgetType === 'time_series' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Chart Type</label>
                <select
                  className="input"
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value as ChartType)}
                >
                  <option value="line">Line Chart</option>
                  <option value="area">Area Chart</option>
                  <option value="bar">Bar Chart</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Granularity</label>
                <select
                  className="input"
                  value={granularity}
                  onChange={(e) => setGranularity(e.target.value as Granularity)}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </>
          )}

          {/* Breakdown Options */}
          {widgetType === 'breakdown' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Chart Type</label>
                <select
                  className="input"
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value as ChartType)}
                >
                  <option value="bar">Bar Chart</option>
                  <option value="pie">Pie Chart</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Group By</label>
                <select
                  className="input"
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value as GroupByField)}
                >
                  <option value="category">Category</option>
                  <option value="merchant">Merchant</option>
                  <option value="account">Account</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Number of Items</label>
                <input
                  type="number"
                  className="input"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                  min="1"
                  max="50"
                />
              </div>
            </>
          )}

          {/* Filters */}
          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-700">Filters (Optional)</h3>
              <button type="button" onClick={addFilter} className="btn btn-secondary text-sm">
                + Add Filter
              </button>
            </div>

            {filters.length === 0 && (
              <p className="text-sm text-gray-500 italic">No filters. Widget will include all data.</p>
            )}

            <div className="space-y-3">
              {filters.map((filter, index) => (
                <div key={index} className="flex gap-2 items-start p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1 grid grid-cols-3 gap-2">
                    {/* Field */}
                    <select
                      className="input"
                      value={filter.field}
                      onChange={(e) =>
                        updateFilter(index, { field: e.target.value as FilterField })
                      }
                    >
                      {FILTER_FIELD_OPTIONS.map((f) => (
                        <option key={f.value} value={f.value}>
                          {f.label}
                        </option>
                      ))}
                    </select>

                    {/* Operator */}
                    <select
                      className="input"
                      value={filter.operator}
                      onChange={(e) =>
                        updateFilter(index, { operator: e.target.value as FilterOperator })
                      }
                    >
                      {OPERATOR_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>

                    {/* Value */}
                    <div>
                      {(filter.operator === 'in' || filter.operator === 'not_in') &&
                      filter.field === 'category_id' ? (
                        <select
                          multiple
                          className="input"
                          value={filter.value || []}
                          onChange={(e) =>
                            updateFilter(index, {
                              value: Array.from(e.target.selectedOptions, (o) =>
                                parseInt(o.value)
                              ),
                            })
                          }
                          size={3}
                        >
                          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                          {categories?.map((cat: any) => (
                            <option key={cat.id} value={cat.id}>
                              {cat.display_name || cat.name}
                            </option>
                          ))}
                        </select>
                      ) : (filter.operator === 'in' || filter.operator === 'not_in') &&
                        filter.field === 'account_id' ? (
                        <select
                          multiple
                          className="input"
                          value={filter.value || []}
                          onChange={(e) =>
                            updateFilter(index, {
                              value: Array.from(e.target.selectedOptions, (o) =>
                                parseInt(o.value)
                              ),
                            })
                          }
                          size={3}
                        >
                          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                          {accounts?.map((acc: any) => (
                            <option key={acc.id} value={acc.id}>
                              {acc.name}
                            </option>
                          ))}
                        </select>
                      ) : filter.operator === 'is_null' || filter.operator === 'is_not_null' ? (
                        <input
                          type="text"
                          className="input"
                          value="(no value needed)"
                          disabled
                        />
                      ) : (
                        <input
                          type={filter.field === 'amount' ? 'number' : 'text'}
                          className="input"
                          value={filter.value || ''}
                          onChange={(e) => updateFilter(index, { value: e.target.value })}
                          placeholder="Value"
                        />
                      )}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => removeFilter(index)}
                    className="text-red-600 hover:text-red-800 mt-1"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Grid Position */}
          <div className="border-t pt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-4">Layout</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Row</label>
                <input
                  type="number"
                  className="input"
                  value={gridRow}
                  onChange={(e) => setGridRow(parseInt(e.target.value))}
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Column</label>
                <input
                  type="number"
                  className="input"
                  value={gridCol}
                  onChange={(e) => setGridCol(parseInt(e.target.value))}
                  min="1"
                  max="4"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Width (cols)
                </label>
                <input
                  type="number"
                  className="input"
                  value={gridWidth}
                  onChange={(e) => setGridWidth(parseInt(e.target.value))}
                  min="1"
                  max="4"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Height (rows)
                </label>
                <input
                  type="number"
                  className="input"
                  value={gridHeight}
                  onChange={(e) => setGridHeight(parseInt(e.target.value))}
                  min="1"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn btn-primary flex-1">
              {widget ? 'Update Widget' : 'Create Widget'}
            </button>
            <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
