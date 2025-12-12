import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'
import { transactionsApi } from '@/api/transactions'
import { getAccountTypeInfo } from '@/utils/accountTypes'
import TransactionDetailModal from '@/components/TransactionDetailModal'
import type { Transaction } from '@/api/types'

export default function Dashboard() {
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  // Fetch accounts
  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list(),
  })

  // Fetch recent transactions
  const { data: recentTransactionsResponse } = useQuery({
    queryKey: ['transactions', { limit: 10 }],
    queryFn: () => transactionsApi.list({ limit: 10 }),
  })

  // Fetch all transactions for calculations
  const { data: allTransactionsResponse } = useQuery({
    queryKey: ['transactions', { limit: 1000 }],
    queryFn: () => transactionsApi.list({ limit: 1000 }),
  })

  const transactions = allTransactionsResponse?.transactions || []
  const recentTransactions = recentTransactionsResponse?.transactions || []

  // Calculate total balance (assets - liabilities)
  const totalBalance = accounts?.reduce((sum, account) => {
    const balance = account.current_balance ?? 0
    const typeInfo = getAccountTypeInfo(account.type, account.subtype)
    // Subtract credit/loan balances, add everything else
    return typeInfo.category === 'credit' || typeInfo.category === 'loan'
      ? sum - Math.abs(balance)
      : sum + balance
  }, 0) ?? 0

  // Get current month date range
  const now = new Date()
  const currentMonthStart = new Date(now.getFullYear(), now.getMonth(), 1)
  const currentMonthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59)
  const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59)

  // Calculate this month's spending and income
  const thisMonthTransactions = transactions.filter((txn) => {
    const txnDate = new Date(txn.date)
    return txnDate >= currentMonthStart && txnDate <= currentMonthEnd
  })

  const thisMonthSpending = thisMonthTransactions
    .filter((txn) => txn.amount < 0)
    .reduce((sum, txn) => sum + Math.abs(txn.amount), 0)

  const thisMonthIncome = thisMonthTransactions
    .filter((txn) => txn.amount > 0)
    .reduce((sum, txn) => sum + txn.amount, 0)

  // Calculate last month's spending and income for comparison
  const lastMonthTransactions = transactions.filter((txn) => {
    const txnDate = new Date(txn.date)
    return txnDate >= lastMonthStart && txnDate <= lastMonthEnd
  })

  const lastMonthSpending = lastMonthTransactions
    .filter((txn) => txn.amount < 0)
    .reduce((sum, txn) => sum + Math.abs(txn.amount), 0)

  const lastMonthIncome = lastMonthTransactions
    .filter((txn) => txn.amount > 0)
    .reduce((sum, txn) => sum + txn.amount, 0)

  // Count uncategorized transactions
  const uncategorizedCount = transactions.filter((txn) => !txn.category_id).length

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  // Calculate percentage change
  const getChangeText = (current: number, previous: number) => {
    if (previous === 0) return 'vs $0.00 last month'
    const change = ((current - previous) / previous) * 100
    const direction = change > 0 ? '+' : ''
    return `${direction}${change.toFixed(1)}% vs last month`
  }

  // Handle transaction click
  const handleTransactionClick = (transaction: Transaction) => {
    setSelectedTransaction(transaction)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedTransaction(null)
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Summary Cards */}
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Total Balance</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatCurrency(totalBalance)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Across {accounts?.length || 0} accounts
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">This Month Spending</div>
          <div className="text-2xl font-bold text-red-600">
            {formatCurrency(thisMonthSpending)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {getChangeText(thisMonthSpending, lastMonthSpending)}
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">This Month Income</div>
          <div className="text-2xl font-bold text-green-600">
            {formatCurrency(thisMonthIncome)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {getChangeText(thisMonthIncome, lastMonthIncome)}
          </div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Uncategorized</div>
          <div className="text-2xl font-bold text-gray-900">{uncategorizedCount}</div>
          <div className="text-xs text-gray-500 mt-1">transactions</div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Transactions</h2>
        {recentTransactions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No transactions yet. Connect your accounts to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recentTransactions.map((txn) => (
                  <tr
                    key={txn.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleTransactionClick(txn)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {new Date(txn.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <div className="flex items-center gap-2">
                        {txn.description}
                        {txn.pending && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                            Pending
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {txn.category?.display_name || (
                        <span className="text-gray-400 italic">Uncategorized</span>
                      )}
                    </td>
                    <td
                      className={`px-4 py-3 whitespace-nowrap text-sm font-medium text-right ${
                        txn.amount < 0 ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {formatCurrency(txn.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href="/accounts"
          className="card hover:shadow-md transition-shadow text-left cursor-pointer"
        >
          <div className="font-medium text-gray-900 mb-1">Manage Accounts</div>
          <div className="text-sm text-gray-600">View and sync your connected accounts</div>
        </a>

        <a
          href="/transactions"
          className="card hover:shadow-md transition-shadow text-left cursor-pointer"
        >
          <div className="font-medium text-gray-900 mb-1">Review Transactions</div>
          <div className="text-sm text-gray-600">
            Categorize and review {uncategorizedCount > 0 ? `${uncategorizedCount} pending` : 'your'}{' '}
            transactions
          </div>
        </a>

        <button className="card hover:shadow-md transition-shadow text-left" disabled>
          <div className="font-medium text-gray-400 mb-1">Sync to Beancount</div>
          <div className="text-sm text-gray-400">Coming soon</div>
        </button>
      </div>

      {/* Transaction Detail Modal */}
      <TransactionDetailModal
        transaction={selectedTransaction}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  )
}
