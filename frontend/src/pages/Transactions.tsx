import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { transactionsApi } from '@/api/transactions'
import { categoriesApi } from '@/api/categories'
import { accountsApi } from '@/api/accounts'
import TransactionList from '@/components/TransactionList'
import TransactionDetailModal from '@/components/TransactionDetailModal'
import TransactionFiltersPanel from '@/components/TransactionFilters'
import type { Transaction, TransactionFilters } from '@/api/types'

export default function Transactions() {
  const [filters, setFilters] = useState<TransactionFilters>({
    page: 1,
    page_size: 50,
  })
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isFiltersOpen, setIsFiltersOpen] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionsApi.list(filters),
  })

  // Fetch categories for display
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list({ includeInactive: false }),
  })

  // Fetch accounts for display
  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list(),
  })

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
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
        <div className="flex gap-3">
          <button className="btn btn-primary">Sync from Plaid</button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search transactions..."
          className="input max-w-md"
          value={filters.search || ''}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, search: e.target.value, page: 1 }))
          }
        />
      </div>

      {/* Filters Panel */}
      <TransactionFiltersPanel
        filters={filters}
        onFiltersChange={setFilters}
        isOpen={isFiltersOpen}
        onToggle={() => setIsFiltersOpen(!isFiltersOpen)}
      />

      {/* Transaction List */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="text-gray-600">Loading transactions...</div>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <div className="text-red-600">Error loading transactions</div>
          <div className="text-sm text-gray-600 mt-2">{String(error)}</div>
        </div>
      )}

      {data && (
        <>
          <TransactionList
            transactions={data.transactions}
            onTransactionClick={handleTransactionClick}
            categories={categories}
            accounts={accounts}
          />

          {/* Pagination */}
          {data.total_pages > 1 && (
            <div className="mt-6 flex justify-between items-center">
              <div className="text-sm text-gray-600">
                Showing {(data.page - 1) * data.page_size + 1} to{' '}
                {Math.min(data.page * data.page_size, data.total)} of {data.total} transactions
              </div>

              <div className="flex gap-2">
                <button
                  className="btn btn-secondary"
                  disabled={data.page === 1}
                  onClick={() => setFilters((prev) => ({ ...prev, page: prev.page! - 1 }))}
                >
                  Previous
                </button>
                <button
                  className="btn btn-secondary"
                  disabled={data.page === data.total_pages}
                  onClick={() => setFilters((prev) => ({ ...prev, page: prev.page! + 1 }))}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Transaction Detail Modal */}
      <TransactionDetailModal
        transaction={selectedTransaction}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  )
}
