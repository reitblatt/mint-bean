import { useQuery } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { transactionsApi } from '@/api/transactions'
import type { WidgetConfig } from '@/api/types'

interface TransactionTableWidgetProps {
  title: string
  config: WidgetConfig
  startDate?: string
  endDate?: string
}

export default function TransactionTableWidget({
  title,
  config,
  startDate,
  endDate,
}: TransactionTableWidgetProps) {
  const limit = config.filters?.limit || 10

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', startDate, endDate, limit],
    queryFn: () =>
      transactionsApi.list({
        start_date: startDate,
        end_date: endDate,
        page_size: limit as number,
        page: 1,
      }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), 'MMM d, yyyy')
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

  if (!data || data.transactions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-medium text-gray-900 mb-4">{title}</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          No transactions for this time period
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-900 mb-4">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.transactions.map((transaction) => (
              <tr key={transaction.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                  {formatDate(transaction.date)}
                </td>
                <td className="px-4 py-2 text-sm text-gray-900">
                  <div className="max-w-xs truncate">{transaction.description}</div>
                  {transaction.merchant_name && (
                    <div className="text-xs text-gray-500">{transaction.merchant_name}</div>
                  )}
                </td>
                <td className="px-4 py-2 text-sm text-gray-600">
                  {transaction.category?.display_name || (
                    <span className="text-gray-400 italic">Uncategorized</span>
                  )}
                </td>
                <td
                  className={`px-4 py-2 text-sm text-right whitespace-nowrap font-medium ${
                    transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatCurrency(transaction.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
