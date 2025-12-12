import { format } from 'date-fns'
import type { Transaction, Category, Account } from '@/api/types'
import clsx from 'clsx'

interface TransactionListProps {
  transactions: Transaction[]
  onTransactionClick?: (transaction: Transaction) => void
  categories?: Category[]
  accounts?: Account[]
}

export default function TransactionList({
  transactions,
  onTransactionClick,
  categories,
  accounts,
}: TransactionListProps) {
  const formatAmount = (amount: number) => {
    const absAmount = Math.abs(amount)
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(absAmount)
  }

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy')
  }

  const getCategoryName = (categoryId: number): string => {
    const category = categories?.find((cat) => cat.id === categoryId)
    return category?.display_name || `Category ${categoryId}`
  }

  const getAccountName = (accountId: number): string => {
    const account = accounts?.find((acc) => acc.id === accountId)
    return account?.name || `Account ${accountId}`
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Date
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Description
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Category
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Account
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Amount
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {transactions.map((transaction) => (
            <tr
              key={transaction.id}
              onClick={() => onTransactionClick?.(transaction)}
              className="hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {formatDate(transaction.date)}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                <div className="font-medium">{transaction.description}</div>
                {transaction.payee && (
                  <div className="text-gray-500 text-xs">{transaction.payee}</div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {transaction.category_id ? (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                    {getCategoryName(transaction.category_id)}
                  </span>
                ) : (
                  <span className="text-gray-400">Uncategorized</span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {getAccountName(transaction.account_id)}
              </td>
              <td
                className={clsx(
                  'px-6 py-4 whitespace-nowrap text-sm font-medium text-right',
                  transaction.amount < 0 ? 'text-red-600' : 'text-green-600'
                )}
              >
                {transaction.amount < 0 ? '-' : '+'}
                {formatAmount(transaction.amount)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-center">
                <div className="flex justify-center gap-1">
                  {transaction.pending && (
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">
                      Pending
                    </span>
                  )}
                  {transaction.reviewed && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                      Reviewed
                    </span>
                  )}
                  {transaction.synced_to_beancount && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      Synced
                    </span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {transactions.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No transactions found
        </div>
      )}
    </div>
  )
}
