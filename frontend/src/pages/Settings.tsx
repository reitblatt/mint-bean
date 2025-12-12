import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { plaidMappingsApi } from '@/api/plaidMappings'
import { categoriesApi } from '@/api/categories'
import PlaidMappingModal from '@/components/PlaidMappingModal'
import type { PlaidCategoryMapping, Category } from '@/api/types'

export default function Settings() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingMapping, setEditingMapping] = useState<PlaidCategoryMapping | undefined>()
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  // Fetch Plaid mappings
  const { data: mappings, isLoading, error } = useQuery({
    queryKey: ['plaid-mappings'],
    queryFn: () => plaidMappingsApi.list(),
  })

  // Fetch categories for display
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list({ includeInactive: false }),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: plaidMappingsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plaid-mappings'] })
      setDeleteConfirmId(null)
    },
  })

  const handleCreateNew = () => {
    setEditingMapping(undefined)
    setIsModalOpen(true)
  }

  const handleEdit = (mapping: PlaidCategoryMapping) => {
    setEditingMapping(mapping)
    setIsModalOpen(true)
  }

  const handleDelete = (id: number) => {
    setDeleteConfirmId(id)
  }

  const confirmDelete = () => {
    if (deleteConfirmId) {
      deleteMutation.mutate(deleteConfirmId)
    }
  }

  const getCategoryName = (categoryId: number): string => {
    const category = categories?.find((cat: Category) => cat.id === categoryId)
    return category?.display_name || `Category ${categoryId}`
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      <div className="max-w-4xl space-y-6">
        {/* Beancount Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Beancount Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beancount File Path
              </label>
              <input type="text" className="input" placeholder="/path/to/main.beancount" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Repository Path
              </label>
              <input type="text" className="input" placeholder="/path/to/beancount/repo" />
            </div>
          </div>
        </div>

        {/* Plaid Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Plaid Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
              <select className="input">
                <option value="sandbox">Sandbox</option>
                <option value="development">Development</option>
                <option value="production">Production</option>
              </select>
            </div>
          </div>
        </div>

        {/* Plaid Category Mappings */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Plaid Category Mappings</h2>
              <p className="text-sm text-gray-600 mt-1">
                Map Plaid categories to your custom categories for automatic categorization
              </p>
            </div>
            <button onClick={handleCreateNew} className="btn btn-primary">
              + New Mapping
            </button>
          </div>

          {/* Mappings List */}
          {isLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-2">Loading mappings...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-8 text-red-600">
              <p>Error loading mappings</p>
              <p className="text-sm mt-1">{(error as Error).message}</p>
            </div>
          )}

          {mappings && mappings.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="mt-2">No Plaid category mappings configured</p>
              <p className="text-sm mt-1">Create your first mapping to auto-categorize transactions</p>
            </div>
          )}

          {mappings && mappings.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Plaid Category
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      MintBean Category
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confidence
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Auto Apply
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stats
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {mappings.map((mapping) => (
                    <tr key={mapping.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">
                        <div>
                          <div className="font-medium text-gray-900">
                            {mapping.plaid_primary_category}
                          </div>
                          {mapping.plaid_detailed_category && (
                            <div className="text-xs text-gray-500">
                              {mapping.plaid_detailed_category}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {getCategoryName(mapping.category_id)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${mapping.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-600">
                            {(mapping.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {mapping.auto_apply ? (
                          <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-800">
                            Yes
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                            No
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        <div className="text-xs">
                          <div>{mapping.match_count} matches</div>
                          {mapping.last_matched_at && (
                            <div className="text-gray-400">
                              Last: {new Date(mapping.last_matched_at).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => handleEdit(mapping)}
                            className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                            title="Edit mapping"
                          >
                            <svg
                              className="w-4 h-4"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                              />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDelete(mapping.id)}
                            className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                            title="Delete mapping"
                          >
                            <svg
                              className="w-4 h-4"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                              />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Save Settings Button */}
        <div className="flex justify-end">
          <button className="btn btn-primary">Save Settings</button>
        </div>
      </div>

      {/* Plaid Mapping Modal */}
      <PlaidMappingModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        mapping={editingMapping}
      />

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Mapping?</h3>
            <p className="text-gray-600 mb-6">
              This will permanently delete the Plaid category mapping. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="btn btn-primary flex-1 bg-red-600 hover:bg-red-700"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
              <button onClick={() => setDeleteConfirmId(null)} className="btn btn-secondary flex-1">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
