import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import type { WidgetConfig } from '@/api/types'

interface SummaryCardWidgetProps {
  title: string
  config: WidgetConfig
  startDate?: string
  endDate?: string
}

export default function SummaryCardWidget({
  title,
  config,
  startDate,
  endDate,
}: SummaryCardWidgetProps) {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['summary-metrics', startDate, endDate],
    queryFn: () => analyticsApi.getSummaryMetrics({ start_date: startDate, end_date: endDate }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num)
  }

  const getMetricValue = (): string => {
    if (!metrics || !config.metric) return '—'

    switch (config.metric) {
      case 'total_balance':
        return formatCurrency(metrics.total_balance)
      case 'total_spending':
        return formatCurrency(metrics.total_spending)
      case 'total_income':
        return formatCurrency(metrics.total_income)
      case 'transaction_count':
        return formatNumber(metrics.transaction_count)
      case 'uncategorized_count':
        return formatNumber(metrics.uncategorized_count)
      case 'account_count':
        return formatNumber(metrics.account_count)
      default:
        return '—'
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
        <div className="h-8 bg-gray-200 rounded animate-pulse" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
      <p className="text-3xl font-bold text-gray-900">{getMetricValue()}</p>
    </div>
  )
}
