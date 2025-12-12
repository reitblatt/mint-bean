import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Transaction, Category, Account } from '@/api/types'
import { categoriesApi } from '@/api/categories'
import { accountsApi } from '@/api/accounts'
import { transactionsApi } from '@/api/transactions'

interface TransactionDetailModalProps {
  transaction: Transaction | null
  isOpen: boolean
  onClose: () => void
}

export default function TransactionDetailModal({
  transaction,
  isOpen,
  onClose,
}: TransactionDetailModalProps) {
  const queryClient = useQueryClient()
  const [editMode, setEditMode] = useState(false)
  const [editedTransaction, setEditedTransaction] = useState<Partial<Transaction>>({})

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list(),
  })

  // Fetch accounts
  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list(),
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (updates: Partial<Transaction>) =>
      transactionsApi.update(transaction!.id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setEditMode(false)
      onClose()
    },
  })

  useEffect(() => {
    if (transaction) {
      setEditedTransaction({
        description: transaction.description,
        category_id: transaction.category_id,
        reviewed: transaction.reviewed,
      })
    }
  }, [transaction])

  if (!isOpen || !transaction) return null

  const category = categories?.find((c) => c.id === transaction.category_id)
  const account = accounts?.find((a) => a.id === transaction.account_id)

  const handleSave = () => {
    updateMutation.mutate(editedTransaction)
  }

  const handleCancel = () => {
    setEditMode(false)
    setEditedTransaction({
      description: transaction.description,
      category_id: transaction.category_id,
      reviewed: transaction.reviewed,
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Transaction Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Amount - Prominent Display */}
          <div className="text-center py-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Amount</div>
            <div
              className={`text-4xl font-bold ${
                transaction.amount < 0 ? 'text-red-600' : 'text-green-600'
              }`}
            >
              {transaction.amount < 0 ? '-' : '+'}${Math.abs(transaction.amount).toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-1">{transaction.currency}</div>
          </div>

          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <div className="text-gray-900">
                {new Date(transaction.date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Payee</label>
              <div className="text-gray-900">{transaction.payee || 'N/A'}</div>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            {editMode ? (
              <input
                type="text"
                value={editedTransaction.description || ''}
                onChange={(e) =>
                  setEditedTransaction({ ...editedTransaction, description: e.target.value })
                }
                className="input w-full"
              />
            ) : (
              <div className="text-gray-900">{transaction.description}</div>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            {editMode ? (
              <select
                value={editedTransaction.category_id || ''}
                onChange={(e) =>
                  setEditedTransaction({
                    ...editedTransaction,
                    category_id: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
                className="input w-full"
              >
                <option value="">No category</option>
                {categories?.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.display_name} ({cat.beancount_account})
                  </option>
                ))}
              </select>
            ) : (
              <div className="text-gray-900">
                {category ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    {category.display_name}
                  </span>
                ) : (
                  <span className="text-gray-400">Uncategorized</span>
                )}
              </div>
            )}
          </div>

          {/* Account */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Account</label>
            <div className="text-gray-900">
              {account ? (
                <div>
                  <div className="font-medium">{account.name}</div>
                  <div className="text-sm text-gray-500">{account.beancount_account}</div>
                </div>
              ) : (
                <span className="text-gray-400">Unknown account</span>
              )}
            </div>
          </div>

          {/* Plaid Categorization */}
          {(transaction.plaid_primary_category || transaction.merchant_name) && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <label className="block text-sm font-medium text-purple-900 mb-2">
                Plaid Categorization
              </label>
              <div className="space-y-2">
                {transaction.merchant_name && (
                  <div>
                    <span className="text-xs text-purple-700 font-medium">Merchant: </span>
                    <span className="text-sm text-purple-900">{transaction.merchant_name}</span>
                  </div>
                )}
                {transaction.plaid_primary_category && (
                  <div>
                    <span className="text-xs text-purple-700 font-medium">Category: </span>
                    <span className="text-sm text-purple-900">
                      {transaction.plaid_primary_category}
                      {transaction.plaid_detailed_category && ` › ${transaction.plaid_detailed_category}`}
                    </span>
                  </div>
                )}
                {transaction.plaid_confidence_level && (
                  <div>
                    <span className="text-xs text-purple-700 font-medium">Confidence: </span>
                    <span className="text-sm text-purple-900">{transaction.plaid_confidence_level}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Status Badges */}
          <div className="flex gap-2">
            {transaction.pending && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Pending
              </span>
            )}
            {transaction.reviewed ? (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Reviewed
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                Not Reviewed
              </span>
            )}
            {transaction.synced_to_beancount && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Synced to Beancount
              </span>
            )}
          </div>

          {/* Technical Details (Collapsible) */}
          <details className="bg-gray-50 rounded-lg p-4">
            <summary className="cursor-pointer font-medium text-gray-700">
              Technical Details
            </summary>
            <div className="mt-4 space-y-2 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div className="text-gray-600">Transaction ID:</div>
                <div className="text-gray-900 font-mono text-xs">{transaction.transaction_id}</div>

                <div className="text-gray-600">Beancount Account:</div>
                <div className="text-gray-900 text-xs">
                  {transaction.beancount_account || 'N/A'}
                </div>

                {transaction.plaid_transaction_id && (
                  <>
                    <div className="text-gray-600">Plaid ID:</div>
                    <div className="text-gray-900 font-mono text-xs">
                      {transaction.plaid_transaction_id}
                    </div>
                  </>
                )}

                <div className="text-gray-600">Created:</div>
                <div className="text-gray-900 text-xs">
                  {new Date(transaction.created_at).toLocaleString()}
                </div>

                <div className="text-gray-600">Updated:</div>
                <div className="text-gray-900 text-xs">
                  {new Date(transaction.updated_at).toLocaleString()}
                </div>
              </div>
            </div>
          </details>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-between items-center p-6 border-t bg-gray-50">
          <div>
            {!editMode && (
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={transaction.reviewed}
                  onChange={(e) => {
                    updateMutation.mutate({ reviewed: e.target.checked })
                  }}
                  className="rounded border-gray-300"
                />
                Mark as reviewed
              </label>
            )}
          </div>

          <div className="flex gap-3">
            {editMode ? (
              <>
                <button onClick={handleCancel} className="btn btn-secondary">
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                  className="btn btn-primary"
                >
                  {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
              </>
            ) : (
              <>
                <button onClick={onClose} className="btn btn-secondary">
                  Close
                </button>
                <button onClick={() => setEditMode(true)} className="btn btn-primary">
                  Edit Transaction
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
