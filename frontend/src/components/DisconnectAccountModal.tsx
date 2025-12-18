import { useEffect, useState } from 'react'
import { apiClient } from '../api/client'

interface DisconnectImpact {
  plaid_item_id: number
  institution_name: string
  accounts_count: number
  transactions_count: number
  rules_affected_count: number
}

interface DisconnectAccountModalProps {
  isOpen: boolean
  plaidItemId: number | null
  institutionName: string
  onConfirm: () => void
  onCancel: () => void
}

export function DisconnectAccountModal({
  isOpen,
  plaidItemId,
  institutionName,
  onConfirm,
  onCancel,
}: DisconnectAccountModalProps) {
  const [impact, setImpact] = useState<DisconnectImpact | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && plaidItemId) {
      fetchDisconnectImpact()
    }
  }, [isOpen, plaidItemId])

  const fetchDisconnectImpact = async () => {
    if (!plaidItemId) return

    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.get<DisconnectImpact>(
        `/plaid/items/${plaidItemId}/disconnect-impact`
      )
      setImpact(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze disconnect impact')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const handleConfirm = () => {
    onConfirm()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Disconnect {institutionName}
          </h2>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Analyzing impact...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {!loading && !error && impact && (
            <div className="space-y-4">
              {/* Main warning */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="flex items-start">
                  <svg
                    className="h-5 w-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-yellow-800">
                      Are you sure you want to disconnect from {institutionName}?
                    </h3>
                    <p className="mt-1 text-sm text-yellow-700">
                      This will stop syncing data from this institution. Your data will
                      remain in the system.
                    </p>
                  </div>
                </div>
              </div>

              {/* Impact summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <h3 className="text-sm font-medium text-blue-900 mb-3">
                  Impact Summary
                </h3>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-blue-800">
                      <svg
                        className="inline h-4 w-4 mr-1 -mt-0.5"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                        <path
                          fillRule="evenodd"
                          d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {impact.accounts_count} account{impact.accounts_count !== 1 ? 's' : ''}
                    </span>
                    <span className="text-blue-600 font-medium">will stop syncing</span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-blue-800">
                      <svg
                        className="inline h-4 w-4 mr-1 -mt-0.5"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {impact.transactions_count} transaction{impact.transactions_count !== 1 ? 's' : ''}
                    </span>
                    <span className="text-blue-600 font-medium">will be preserved</span>
                  </div>

                  {impact.rules_affected_count > 0 && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-blue-800">
                        <svg
                          className="inline h-4 w-4 mr-1 -mt-0.5"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                        {impact.rules_affected_count} rule{impact.rules_affected_count !== 1 ? 's' : ''}
                      </span>
                      <span className="text-blue-600 font-medium">may need updating</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Additional info */}
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-2">
                  What happens next?
                </h3>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li className="flex items-start">
                    <svg
                      className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>
                      Accounts will stop receiving new transactions
                    </span>
                  </li>
                  <li className="flex items-start">
                    <svg
                      className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>
                      All existing transactions remain in your history
                    </span>
                  </li>
                  <li className="flex items-start">
                    <svg
                      className="h-4 w-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span>
                      You can reconnect this institution anytime
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading || !!error}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Disconnect
          </button>
        </div>
      </div>
    </div>
  )
}
