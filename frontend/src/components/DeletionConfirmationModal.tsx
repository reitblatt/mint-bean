import { useEffect, useState, useCallback } from 'react'
import { apiClient } from '../api/client'

interface DeletionImpact {
  entity_type: string
  entity_id: number
  cascades: Record<string, number>
  total_affected: number
  warnings: string[]
}

interface DeletionConfirmationModalProps {
  isOpen: boolean
  entityType: string
  entityId: number
  entityName: string
  onConfirm: () => void
  onCancel: () => void
}

export function DeletionConfirmationModal({
  isOpen,
  entityType,
  entityId,
  entityName,
  onConfirm,
  onCancel,
}: DeletionConfirmationModalProps) {
  const [impact, setImpact] = useState<DeletionImpact | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDeletionImpact = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.get<DeletionImpact>(
        `/deletion/impact/${entityType}/${entityId}`
      )
      setImpact(response.data)
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Failed to analyze deletion impact')
    } finally {
      setLoading(false)
    }
  }, [entityType, entityId])

  useEffect(() => {
    if (isOpen && entityId) {
      fetchDeletionImpact()
    }
  }, [isOpen, entityId, fetchDeletionImpact])

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
            Confirm Deletion
          </h2>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Analyzing deletion impact...</p>
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
                      Are you sure you want to delete "{entityName}"?
                    </h3>
                    <p className="mt-1 text-sm text-yellow-700">
                      This action cannot be undone.
                    </p>
                  </div>
                </div>
              </div>

              {/* Impact summary */}
              {impact.total_affected > 1 && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <h3 className="text-sm font-medium text-red-900 mb-2">
                    Deletion Impact
                  </h3>
                  <p className="text-sm text-red-800 mb-3">
                    <span className="font-semibold">
                      {impact.total_affected} object{impact.total_affected !== 1 ? 's' : ''}
                    </span>{' '}
                    will be affected by this deletion:
                  </p>

                  {/* Cascades */}
                  {Object.keys(impact.cascades).length > 0 && (
                    <div className="space-y-1">
                      {Object.entries(impact.cascades).map(([type, count]) => (
                        <div
                          key={type}
                          className="flex items-center justify-between text-sm"
                        >
                          <span className="text-red-800">
                            {count} {type}
                            {count !== 1 ? 's' : ''}
                          </span>
                          <span className="text-red-600 font-medium">
                            will be deleted
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Warnings */}
              {impact.warnings.length > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-md p-4">
                  <h3 className="text-sm font-medium text-orange-900 mb-2">
                    Important Warnings
                  </h3>
                  <ul className="space-y-2">
                    {impact.warnings.map((warning, index) => (
                      <li
                        key={index}
                        className="flex items-start text-sm text-orange-800"
                      >
                        <svg
                          className="h-4 w-4 text-orange-600 mt-0.5 mr-2 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span>{warning}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* No impact message */}
              {impact.total_affected === 1 && impact.warnings.length === 0 && (
                <div className="bg-green-50 border border-green-200 rounded-md p-4">
                  <p className="text-sm text-green-800">
                    This deletion will not affect any other objects.
                  </p>
                </div>
              )}
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
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
