import { useQuery } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { analyticsApi } from '@/api/analytics'
import type { WidgetConfig } from '@/api/types'

interface LineChartWidgetProps {
  title: string
  config: WidgetConfig
  startDate?: string
  endDate?: string
}

export default function LineChartWidget({
  title,
  config,
  startDate,
  endDate,
}: LineChartWidgetProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['spending-over-time', startDate, endDate, config.granularity],
    queryFn: () =>
      analyticsApi.getSpendingOverTime({
        start_date: startDate,
        end_date: endDate,
        granularity: config.granularity || 'daily',
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

  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), 'MMM d')
    } catch {
      return dateString
    }
  }

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
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data.data}>
          <XAxis dataKey="date" tickFormatter={formatDate} style={{ fontSize: '12px' }} />
          <YAxis tickFormatter={formatCurrency} style={{ fontSize: '12px' }} />
          <Tooltip
            formatter={(value: number) => [formatCurrency(value), 'Spending']}
            labelFormatter={(label) => formatDate(label as string)}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#4f46e5"
            strokeWidth={2}
            dot={{ fill: '#4f46e5', r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
