import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { transactionsApi } from '@/api/transactions'
import TransactionList from '@/components/TransactionList'
import type { Transaction, TransactionFilters } from '@/api/types'

export default function Transactions() {
  const [filters, setFilters] = useState<TransactionFilters>({
    page: 1,
    page_size: 50,
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionsApi.list(filters),
  })

  const handleTransactionClick = (transaction: Transaction) => {
    console.log('Transaction clicked:', transaction)
    // TODO: Open transaction detail modal
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
        <div className="flex gap-3">
          <button className="btn btn-secondary">Filter</button>
          <button className="btn btn-primary">Sync from Plaid</button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search transactions..."
          className="input max-w-md"
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, search: e.target.value, page: 1 }))
          }
        />
      </div>

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
    </div>
  )
}
