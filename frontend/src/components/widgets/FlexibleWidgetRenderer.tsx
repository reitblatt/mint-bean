import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { DashboardWidget } from '@/api/types'
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
  // Parse widget config
  const config = widget.config ? JSON.parse(widget.config) : {}
  // For backwards compatibility, check both config.widget_type and widget.widget_type
  const widgetType = config.widget_type || widget.widget_type || 'summary_card'

  // Build query parameters
  const params = new URLSearchParams()
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)

  // Fetch data based on widget type
  const { data, isLoading, error } = useQuery({
    queryKey: ['widget-data', widget.id, widgetType, startDate, endDate],
    queryFn: async () => {
      if (widgetType === 'summary_card') {
        const response = await apiClient.post(
          `/analytics/query/metric?${params}`,
          {
            metric: config.metric || 'total_balance',
            filters: Array.isArray(config.filters) ? config.filters : [],
          }
        )
        return response.data
      } else if (widgetType === 'time_series') {
        const response = await apiClient.post(
          `/analytics/query/time-series?${params}`,
          {
            metric: config.metric || 'total_spending',
            chart_type: config.chart_type || 'line',
            granularity: config.granularity || 'daily',
            filters: Array.isArray(config.filters) ? config.filters : [],
          }
        )
        return response.data
      } else if (widgetType === 'breakdown') {
        const response = await apiClient.post(
          `/analytics/query/breakdown?${params}`,
          {
            metric: config.metric || 'total_spending',
            group_by: config.group_by || 'category',
            chart_type: config.chart_type || 'bar',
            limit: config.limit || 10,
            filters: Array.isArray(config.filters) ? config.filters : [],
          }
        )
        return response.data
      }
      return null
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

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
  if (widgetType === 'summary_card' && data) {
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

  // Render time series
  if (widgetType === 'time_series' && data && data.data) {
    const chartData = data.data
    const ChartComponent =
      config.chart_type === 'area'
        ? AreaChart
        : config.chart_type === 'bar'
        ? BarChart
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
            {config.chart_type === 'area' ? (
              <Area type="monotone" dataKey="value" fill="#4f46e5" stroke="#4f46e5" />
            ) : config.chart_type === 'bar' ? (
              <Bar dataKey="value" fill="#4f46e5" />
            ) : (
              <Line type="monotone" dataKey="value" stroke="#4f46e5" strokeWidth={2} />
            )}
          </ChartComponent>
        </ResponsiveContainer>
        {config.filters && config.filters.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            {config.filters.length} filter{config.filters.length > 1 ? 's' : ''} applied
          </p>
        )}
      </div>
    )
  }

  // Render breakdown
  if (widgetType === 'breakdown' && data && data.data) {
    const breakdownData = data.data

    if (config.chart_type === 'pie') {
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              <Pie
                data={breakdownData}
                dataKey="value"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry: any) => `${entry.label}: ${formatCurrency(entry.value)}`}
              >
                {breakdownData.map((_: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number | undefined) => formatCurrency(value || 0)} />
            </PieChart>
          </ResponsiveContainer>
          {config.filters && config.filters.length > 0 && (
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
          {config.filters && config.filters.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              {config.filters.length} filter{config.filters.length > 1 ? 's' : ''} applied
            </p>
          )}
        </div>
      )
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{widget.title}</h3>
      <p className="text-gray-500">No data available</p>
    </div>
  )
}
