import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { analyticsApi } from '@/api/analytics'
import type { WidgetConfig } from '@/api/types'

interface BarChartWidgetProps {
  title: string
  config: WidgetConfig
  startDate?: string
  endDate?: string
}

export default function BarChartWidget({
  title,
  config,
  startDate,
  endDate,
}: BarChartWidgetProps) {
  const dataType = config.data_type || 'spending_by_category'

  const { data, isLoading } = useQuery({
    queryKey: [dataType, startDate, endDate, config.limit],
    queryFn: () => {
      const params = {
        start_date: startDate,
        end_date: endDate,
        limit: config.limit || 10,
      }

      if (dataType === 'spending_by_merchant') {
        return analyticsApi.getSpendingByMerchant(params)
      }
      return analyticsApi.getSpendingByCategory(params)
    },
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
      name: 'category_name' in item ? item.category_name : item.merchant_name,
      amount: item.amount,
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
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="horizontal">
          <XAxis type="category" dataKey="name" style={{ fontSize: '12px' }} angle={-45} textAnchor="end" height={100} />
          <YAxis type="number" tickFormatter={formatCurrency} style={{ fontSize: '12px' }} />
          <Tooltip
            formatter={(value: number) => [formatCurrency(value), 'Amount']}
            cursor={{ fill: 'rgba(79, 70, 229, 0.1)' }}
          />
          <Bar dataKey="amount" fill="#4f46e5" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
