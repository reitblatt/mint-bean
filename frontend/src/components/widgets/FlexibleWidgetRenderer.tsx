import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { DashboardWidget, WidgetConfig, BreakdownDataPoint } from '@/api/types'
import {
  isSummaryCardConfig,
  isTimeSeriesConfig,
  isBreakdownConfig,
  isLegacyLineChartConfig,
  isLegacyPieChartConfig,
  isLegacyBarChartConfig,
  isTableConfig,
} from '@/api/types'
import TransactionTableWidget from './TransactionTableWidget'
import {
  ResponsiveContainer,
  LineChart,
  AreaChart,
  BarChart,
  PieChart,
  Line,
  Area,
  Bar,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'

interface FlexibleWidgetRendererProps {
  widget: DashboardWidget
  startDate?: string
  endDate?: string
}

const COLORS = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1']

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const formatNumber = (value: number) => {
  return new Intl.NumberFormat('en-US').format(value)
}

export default function FlexibleWidgetRenderer({
  widget,
  startDate,
  endDate,
}: FlexibleWidgetRendererProps) {
  // Parse widget config with type safety
  const parsedConfig: WidgetConfig | null = widget.config
    ? (() => {
        try {
          const config = JSON.parse(widget.config)
          // For backwards compatibility, merge widget_type from database column if not in config
          return {
            ...config,
            widget_type: config.widget_type || widget.widget_type || 'summary_card',
          }
        } catch {
          return null
        }
      })()
    : null

  // Build query parameters
  const params = new URLSearchParams()
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)

  // Fetch data based on widget type with type guards
  const { data, isLoading, error } = useQuery({
    queryKey: ['widget-data', widget.id, parsedConfig?.widget_type, startDate, endDate],
    queryFn: async () => {
      if (!parsedConfig) return null

      // Handle legacy line/bar chart widgets
      if (isLegacyLineChartConfig(parsedConfig)) {
        const response = await apiClient.post(`/analytics/query/time-series?${params}`, {
          metric: 'total_spending',
          chart_type: 'line',
          granularity: parsedConfig.granularity || 'daily',
          filters: [],
        })
        return response.data
      }

      if (isLegacyBarChartConfig(parsedConfig)) {
        const response = await apiClient.post(`/analytics/query/time-series?${params}`, {
          metric: 'total_spending',
          chart_type: 'bar',
          granularity: parsedConfig.granularity || 'daily',
          filters: [],
        })
        return response.data
      }

      // Handle legacy pie chart widgets
      if (isLegacyPieChartConfig(parsedConfig)) {
        const response = await apiClient.post(`/analytics/query/breakdown?${params}`, {
          metric: 'total_spending',
          group_by: 'category',
          chart_type: 'pie',
          limit: parsedConfig.limit || 10,
          filters: [],
        })
        return response.data
      }

      // Handle summary card widgets
      if (isSummaryCardConfig(parsedConfig)) {
        const response = await apiClient.post(`/analytics/query/metric?${params}`, {
          metric: parsedConfig.metric,
          filters: parsedConfig.filters || [],
        })
        return response.data
      }

      // Handle time series widgets
      if (isTimeSeriesConfig(parsedConfig)) {
        const response = await apiClient.post(`/analytics/query/time-series?${params}`, {
          metric: parsedConfig.metric,
          chart_type: parsedConfig.chart_type,
          granularity: parsedConfig.granularity,
          filters: parsedConfig.filters || [],
        })
        return response.data
      }

      // Handle breakdown widgets
      if (isBreakdownConfig(parsedConfig)) {
        const response = await apiClient.post(`/analytics/query/breakdown?${params}`, {
          metric: parsedConfig.metric,
          group_by: parsedConfig.group_by,
          chart_type: parsedConfig.chart_type,
          limit: parsedConfig.limit,
          filters: parsedConfig.filters || [],
        })
        return response.data
      }

      return null
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const config = parsedConfig

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
        <div className="h-64 bg-gray-200 rounded animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
        <div className="text-red-600">Error loading widget data</div>
      </div>
    )
  }

  // Render summary card
  if (config && isSummaryCardConfig(config) && data) {
    const isBalance = config.metric === 'total_balance' || config.metric === 'net_worth'
    const isCurrency =
      isBalance ||
      config.metric === 'total_spending' ||
      config.metric === 'total_income' ||
      config.metric === 'net_income'

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">{widget.title}</h3>
        <p className="text-3xl font-bold text-gray-900">
          {isCurrency ? formatCurrency(data.value) : formatNumber(data.value)}
        </p>
        {config.filters && config.filters.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            {config.filters.length} filter{config.filters.length > 1 ? 's' : ''} applied
          </p>
        )}
      </div>
    )
  }

  // Render time series (both new and legacy)
  if (
    config &&
    (isTimeSeriesConfig(config) || isLegacyLineChartConfig(config) || isLegacyBarChartConfig(config)) &&
    data &&
    data.data
  ) {
    const chartData = data.data
    const ChartComponent =
      isLegacyLineChartConfig(config) || (isTimeSeriesConfig(config) && config.chart_type === 'line')
        ? LineChart
        : isLegacyBarChartConfig(config) || (isTimeSeriesConfig(config) && config.chart_type === 'bar')
        ? BarChart
        : isTimeSeriesConfig(config) && config.chart_type === 'area'
        ? AreaChart
        : LineChart

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <ChartComponent data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={formatCurrency} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value: number | undefined) => formatCurrency(value || 0)} />
            {isTimeSeriesConfig(config) && config.chart_type === 'area' ? (
              <Area type="monotone" dataKey="value" fill="#4f46e5" stroke="#4f46e5" />
            ) : isLegacyBarChartConfig(config) || (isTimeSeriesConfig(config) && config.chart_type === 'bar') ? (
              <Bar dataKey="value" fill="#4f46e5" />
            ) : (
              <Line type="monotone" dataKey="value" stroke="#4f46e5" strokeWidth={2} />
            )}
          </ChartComponent>
        </ResponsiveContainer>
        {isTimeSeriesConfig(config) && config.filters && config.filters.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            {config.filters.length} filter{config.filters.length > 1 ? 's' : ''} applied
          </p>
        )}
      </div>
    )
  }

  // Render breakdown (both new and legacy)
  if (config && (isBreakdownConfig(config) || isLegacyPieChartConfig(config)) && data && data.data) {
    const breakdownData = data.data

    if (isLegacyPieChartConfig(config) || (isBreakdownConfig(config) && config.chart_type === 'pie')) {
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={breakdownData}
                dataKey="value"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry) => {
                  const dataPoint = entry as unknown as BreakdownDataPoint
                  return `${dataPoint.label}: ${formatCurrency(dataPoint.value)}`
                }}
              >
                {breakdownData.map((_: BreakdownDataPoint, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number | undefined) => formatCurrency(value || 0)} />
            </PieChart>
          </ResponsiveContainer>
          {isBreakdownConfig(config) && config.filters && config.filters.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              {config.filters.length} filter{config.filters.length > 1 ? 's' : ''} applied
            </p>
          )}
        </div>
      )
    } else {
      // Bar chart
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={breakdownData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={formatCurrency} tick={{ fontSize: 12 }} />
              <YAxis dataKey="label" type="category" width={150} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value: number | undefined) => formatCurrency(value || 0)} />
              <Bar dataKey="value" fill="#4f46e5" />
            </BarChart>
          </ResponsiveContainer>
          {isBreakdownConfig(config) && config.filters && config.filters.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              {config.filters.length} filter{config.filters.length > 1 ? 's' : ''} applied
            </p>
          )}
        </div>
      )
    }
  }

  // Render table widget
  if (config && isTableConfig(config)) {
    return <TransactionTableWidget title={widget.title} config={config} startDate={startDate} endDate={endDate} />
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
      <p className="text-gray-500">No data available</p>
    </div>
  )
}
