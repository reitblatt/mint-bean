import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rulesApi } from '@/api/rules'
import { plaidMappingsApi } from '@/api/plaidMappings'
import { categoriesApi } from '@/api/categories'
import RuleFormModal from '@/components/RuleFormModal'
import PlaidMappingModal from '@/components/PlaidMappingModal'
import type { Rule, PlaidCategoryMapping, Category } from '@/api/types'

export default function Rules() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'rules' | 'plaid-mappings'>('rules')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<Rule | undefined>()
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)
  const [showInactive, setShowInactive] = useState(false)

  // Plaid mappings state
  const [isMappingModalOpen, setIsMappingModalOpen] = useState(false)
  const [editingMapping, setEditingMapping] = useState<PlaidCategoryMapping | undefined>()
  const [deleteMappingConfirmId, setDeleteMappingConfirmId] = useState<number | null>(null)

  // Fetch rules
  const { data: rules, isLoading, error } = useQuery({
    queryKey: ['rules', showInactive],
    queryFn: () => rulesApi.list(!showInactive),
  })

  // Fetch Plaid mappings
  const { data: mappings, isLoading: mappingsLoading, error: mappingsError } = useQuery({
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
    mutationFn: rulesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      setDeleteConfirmId(null)
    },
  })

  // Delete mapping mutation
  const deleteMappingMutation = useMutation({
    mutationFn: plaidMappingsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plaid-mappings'] })
      setDeleteMappingConfirmId(null)
    },
  })

  // Toggle active mutation
  const toggleActiveMutation = useMutation({
    mutationFn: (data: { id: number; active: boolean }) =>
      rulesApi.update(data.id, { active: data.active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  const handleCreateNew = () => {
    setEditingRule(undefined)
    setIsModalOpen(true)
  }

  const handleEdit = (rule: Rule) => {
    setEditingRule(rule)
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

  const handleToggleActive = (rule: Rule) => {
    toggleActiveMutation.mutate({ id: rule.id, active: !rule.active })
  }

  const handleCreateNewMapping = () => {
    setEditingMapping(undefined)
    setIsMappingModalOpen(true)
  }

  const handleEditMapping = (mapping: PlaidCategoryMapping) => {
    setEditingMapping(mapping)
    setIsMappingModalOpen(true)
  }

  const handleDeleteMapping = (id: number) => {
    setDeleteMappingConfirmId(id)
  }

  const confirmDeleteMapping = () => {
    if (deleteMappingConfirmId) {
      deleteMappingMutation.mutate(deleteMappingConfirmId)
    }
  }

  const getCategoryName = (categoryId: number): string => {
    const category = categories?.find((cat: Category) => cat.id === categoryId)
    return category?.display_name || `Category ${categoryId}`
  }

  const getConditionSummary = (conditions: Record<string, unknown>): string => {
    if (!conditions) return 'No conditions'

    // Handle field-as-key format (e.g., { "plaid_detailed_category": { "operator": "equals", "value": "..." } })
    const keys = Object.keys(conditions)
    if (keys.length === 1 && typeof conditions[keys[0]] === 'object') {
      const fieldName = keys[0]
      const condition = conditions[fieldName] as { operator?: string; value?: string }
      if (condition.operator && condition.value !== undefined) {
        const field = fieldName.replace(/_/g, ' ')
        const operator = condition.operator.replace(/_/g, ' ')
        return `${field} ${operator} "${condition.value}"`
      }
    }

    // Handle simple condition with explicit field
    const cond = conditions as { field?: string; operator?: string; value?: string }
    if (cond.field && cond.operator && cond.value !== undefined) {
      const field = cond.field.replace(/_/g, ' ')
      const operator = cond.operator.replace(/_/g, ' ')
      return `${field} ${operator} "${cond.value}"`
    }

    // Handle complex conditions
    const complexCond = conditions as { all?: unknown[]; any?: unknown[] }
    if (complexCond.all || complexCond.any) {
      const type = complexCond.all ? 'all' : 'any'
      const count = (complexCond.all || complexCond.any)?.length || 0
      return `Match ${type} of ${count} conditions`
    }

    return 'Complex conditions'
  }

  const getActionSummary = (actions: Record<string, unknown>, categoryId?: number): string => {
    if (!actions) return 'No actions'

    const actionList = []
    if (actions.set_category || categoryId) {
      actionList.push('Set category')
    }
    if (actions.set_reviewed) {
      actionList.push('Mark reviewed')
    }

    return actionList.length > 0 ? actionList.join(', ') : 'No actions'
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Categorization</h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage rules and mappings for automatic transaction categorization
          </p>
        </div>
        <button
          onClick={activeTab === 'rules' ? handleCreateNew : handleCreateNewMapping}
          className="btn btn-primary"
        >
          + {activeTab === 'rules' ? 'New Rule' : 'New Mapping'}
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('rules')}
            className={`${
              activeTab === 'rules'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Categorization Rules
          </button>
          <button
            onClick={() => setActiveTab('plaid-mappings')}
            className={`${
              activeTab === 'plaid-mappings'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Plaid Category Mappings
          </button>
        </nav>
      </div>

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <>
          {/* Filter Toggle */}
          <div className="mb-6">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
              />
              <span className="ml-2 text-sm text-gray-700">Show inactive rules</span>
            </label>
          </div>

          {/* Rules List */}
          <div className="card">
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="text-gray-600 mt-2">Loading rules...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-12 text-red-600">
            <p>Error loading rules</p>
            <p className="text-sm mt-1">{(error as Error).message}</p>
          </div>
        )}

        {rules && rules.length === 0 && (
          <div className="text-center py-12 text-gray-500">
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
            <p className="mt-2">No rules found</p>
            <p className="text-sm mt-1">Create your first rule to auto-categorize transactions</p>
          </div>
        )}

        {rules && rules.length > 0 && (
          <div className="divide-y divide-gray-200">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className={`p-4 hover:bg-gray-50 transition-colors ${!rule.active ? 'opacity-60' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{rule.name}</h3>

                      {/* Active Badge */}
                      {rule.active ? (
                        <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                          Inactive
                        </span>
                      )}

                      {/* Priority Badge */}
                      {rule.priority > 0 && (
                        <span className="inline-block px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                          Priority: {rule.priority}
                        </span>
                      )}
                    </div>

                    {rule.description && (
                      <p className="text-sm text-gray-600 mb-3">{rule.description}</p>
                    )}

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Condition:</span>
                        <span className="ml-2 text-gray-600">
                          {getConditionSummary(rule.conditions)}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Action:</span>
                        <span className="ml-2 text-gray-600">
                          {getActionSummary(rule.actions, rule.category_id)}
                        </span>
                      </div>
                    </div>

                    {/* Statistics */}
                    <div className="mt-3 flex gap-4 text-xs text-gray-500">
                      <span>Matched {rule.match_count} times</span>
                      {rule.last_matched_at && (
                        <span>
                          Last matched: {new Date(rule.last_matched_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleToggleActive(rule)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title={rule.active ? 'Deactivate' : 'Activate'}
                    >
                      {rule.active ? (
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      ) : (
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      )}
                    </button>

                    <button
                      onClick={() => handleEdit(rule)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="Edit rule"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                        />
                      </svg>
                    </button>

                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      title="Delete rule"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
          </div>
        </>
      )}

      {/* Plaid Category Mappings Tab */}
      {activeTab === 'plaid-mappings' && (
        <div className="card">
          {mappingsLoading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-2">Loading mappings...</p>
            </div>
          )}

          {mappingsError && (
            <div className="text-center py-12 text-red-600">
              <p>Error loading mappings</p>
              <p className="text-sm mt-1">{(mappingsError as Error).message}</p>
            </div>
          )}

          {mappings && mappings.length === 0 && (
            <div className="text-center py-12 text-gray-500">
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
                        {mapping.category?.display_name || `Category ${mapping.category_id}`}
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
                            onClick={() => handleEditMapping(mapping)}
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
                            onClick={() => handleDeleteMapping(mapping.id)}
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
      )}

      {/* Rule Form Modal */}
      <RuleFormModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} rule={editingRule} />

      {/* Plaid Mapping Modal */}
      <PlaidMappingModal
        isOpen={isMappingModalOpen}
        onClose={() => setIsMappingModalOpen(false)}
        mapping={editingMapping}
      />

      {/* Delete Rule Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Rule?</h3>
            <p className="text-gray-600 mb-6">
              This will permanently delete the rule. This action cannot be undone.
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

      {/* Delete Mapping Confirmation Modal */}
      {deleteMappingConfirmId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Mapping?</h3>
            <p className="text-gray-600 mb-6">
              This will permanently delete the Plaid category mapping. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={confirmDeleteMapping}
                disabled={deleteMappingMutation.isPending}
                className="btn btn-primary flex-1 bg-red-600 hover:bg-red-700"
              >
                {deleteMappingMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
              <button onClick={() => setDeleteMappingConfirmId(null)} className="btn btn-secondary flex-1">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
