import { useQuery } from '@tanstack/react-query'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { analyticsApi } from '@/api/analytics'
import type { WidgetConfig } from '@/api/types'

interface PieChartWidgetProps {
  title: string
  config: WidgetConfig
  startDate?: string
  endDate?: string
}

const COLORS = [
  '#4f46e5',
  '#06b6d4',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#6366f1',
]

export default function PieChartWidget({
  title,
  config,
  startDate,
  endDate,
}: PieChartWidgetProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['spending-by-category', startDate, endDate, config.limit],
    queryFn: () =>
      analyticsApi.getSpendingByCategory({
        start_date: startDate,
        end_date: endDate,
        limit: config.limit || 8,
      }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const chartData =
    data?.data.map((item) => ({
      name: item.category_name,
      value: item.amount,
      percentage: item.percentage,
    })) || []

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-medium text-gray-900 mb-4">{title}</h3>
        <div className="h-64 bg-gray-200 rounded animate-pulse" />
      </div>
    )
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-medium text-gray-900 mb-4">{title}</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          No data available for this time period
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-900 mb-4">{title}</h3>
      <div className="flex items-center">
        <ResponsiveContainer width="60%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={({ percentage }) => `${percentage.toFixed(1)}%`}
            >
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
          </PieChart>
        </ResponsiveContainer>
        <div className="w-40% pl-4">
          <div className="space-y-2">
            {chartData.slice(0, 8).map((item, index) => (
              <div key={item.name} className="flex items-center gap-2 text-sm">
                <div
                  className="w-3 h-3 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-gray-700 truncate flex-1">{item.name}</span>
                <span className="text-gray-500 text-xs">{item.percentage.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
