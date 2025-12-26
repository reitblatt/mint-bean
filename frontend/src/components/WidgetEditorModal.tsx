import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardsApi } from '@/api/dashboards'
import type { DashboardWidget, DashboardWidgetCreate } from '@/api/types'

interface WidgetEditorModalProps {
  isOpen: boolean
  onClose: () => void
  tabId: number
  widget?: DashboardWidget
}

const WIDGET_TYPES = [
  { value: 'summary_card', label: 'Summary Card', description: 'Display a single metric' },
  { value: 'line_chart', label: 'Line Chart', description: 'Spending over time' },
  { value: 'bar_chart', label: 'Bar Chart', description: 'Category or merchant breakdown' },
  { value: 'pie_chart', label: 'Pie Chart', description: 'Expense breakdown' },
  { value: 'table', label: 'Transaction Table', description: 'Recent transactions' },
]

const SUMMARY_METRICS = [
  { value: 'total_balance', label: 'Total Balance' },
  { value: 'total_spending', label: 'Total Spending' },
  { value: 'total_income', label: 'Total Income' },
  { value: 'transaction_count', label: 'Transaction Count' },
  { value: 'uncategorized_count', label: 'Uncategorized Count' },
  { value: 'account_count', label: 'Account Count' },
]

export default function WidgetEditorModal({
  isOpen,
  onClose,
  tabId,
  widget,
}: WidgetEditorModalProps) {
  const queryClient = useQueryClient()
  const [widgetType, setWidgetType] = useState(widget?.widget_type || 'summary_card')
  const [title, setTitle] = useState(widget?.title || '')
  const [gridRow, setGridRow] = useState(widget?.grid_row || 1)
  const [gridCol, setGridCol] = useState(widget?.grid_col || 1)
  const [gridWidth, setGridWidth] = useState(widget?.grid_width || 1)
  const [gridHeight, setGridHeight] = useState(widget?.grid_height || 1)

  // Widget-specific config
  const [metric, setMetric] = useState('')
  const [dataType, setDataType] = useState('spending_over_time')
  const [granularity, setGranularity] = useState('daily')
  const [limit, setLimit] = useState(10)

  // Parse existing config if editing
  useState(() => {
    if (widget?.config) {
      try {
        const config = JSON.parse(widget.config)
        if (config.metric) setMetric(config.metric)
        if (config.data_type) setDataType(config.data_type)
        if (config.granularity) setGranularity(config.granularity)
        if (config.limit) setLimit(config.limit)
      } catch {
        // Ignore parse errors
      }
    }
  })

  const createMutation = useMutation({
    mutationFn: (data: DashboardWidgetCreate) => dashboardsApi.createWidget(tabId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-tab', tabId] })
      onClose()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: DashboardWidgetCreate) =>
      dashboardsApi.updateWidget(tabId, widget!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-tab', tabId] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Build config based on widget type
    let config = {}
    switch (widgetType) {
      case 'summary_card':
        config = { metric }
        break
      case 'line_chart':
        config = { data_type: dataType, granularity }
        break
      case 'bar_chart':
        config = { data_type: dataType, limit }
        break
      case 'pie_chart':
        config = { data_type: 'spending_by_category', limit }
        break
      case 'table':
        config = { filters: { limit, sort: 'date_desc' } }
        break
    }

    const widgetData: DashboardWidgetCreate = {
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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {widget ? 'Edit Widget' : 'Add New Widget'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Widget Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Widget Type</label>
            <div className="grid grid-cols-1 gap-2">
              {WIDGET_TYPES.map((type) => (
                <label
                  key={type.value}
                  className={`flex items-start p-3 border rounded-lg cursor-pointer ${
                    widgetType === type.value
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="widgetType"
                    value={type.value}
                    checked={widgetType === type.value}
                    onChange={(e) => setWidgetType(e.target.value)}
                    className="mt-1"
                  />
                  <div className="ml-3">
                    <div className="font-medium text-gray-900">{type.label}</div>
                    <div className="text-sm text-gray-500">{type.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Widget Title *</label>
            <input
              type="text"
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Total Balance, Spending Trends"
              required
            />
          </div>

          {/* Widget-specific config */}
          {widgetType === 'summary_card' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Metric *</label>
              <select
                className="input"
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                required
              >
                <option value="">Select a metric</option>
                {SUMMARY_METRICS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {widgetType === 'line_chart' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Granularity</label>
              <select
                className="input"
                value={granularity}
                onChange={(e) => setGranularity(e.target.value)}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          )}

          {widgetType === 'bar_chart' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                <select
                  className="input"
                  value={dataType}
                  onChange={(e) => setDataType(e.target.value)}
                >
                  <option value="spending_by_category">By Category</option>
                  <option value="spending_by_merchant">By Merchant</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Number of Items
                </label>
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

          {(widgetType === 'pie_chart' || widgetType === 'table') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {widgetType === 'pie_chart' ? 'Number of Categories' : 'Number of Transactions'}
              </label>
              <input
                type="number"
                className="input"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                min="1"
                max={widgetType === 'pie_chart' ? '20' : '100'}
              />
            </div>
          )}

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
                <label className="block text-sm font-medium text-gray-700 mb-1">Width (cols)</label>
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
            <p className="text-xs text-gray-500 mt-2">
              Grid is 4 columns wide. Position widgets by specifying row and column.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" className="btn btn-primary flex-1">
              {widget ? 'Update Widget' : 'Add Widget'}
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
