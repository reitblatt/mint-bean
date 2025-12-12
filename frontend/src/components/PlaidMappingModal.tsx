import { useState, useEffect } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { plaidMappingsApi } from '@/api/plaidMappings'
import { categoriesApi } from '@/api/categories'
import type { PlaidCategoryMapping, Category } from '@/api/types'

interface PlaidMappingModalProps {
  isOpen: boolean
  onClose: () => void
  mapping?: PlaidCategoryMapping
}

export default function PlaidMappingModal({ isOpen, onClose, mapping }: PlaidMappingModalProps) {
  const queryClient = useQueryClient()
  const isEdit = !!mapping

  // Form state
  const [plaidPrimaryCategory, setPlaidPrimaryCategory] = useState('')
  const [plaidDetailedCategory, setPlaidDetailedCategory] = useState('')
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [confidence, setConfidence] = useState(1.0)
  const [autoApply, setAutoApply] = useState(true)

  // Fetch categories for dropdown
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list({ includeInactive: false }),
  })

  // Initialize form when editing
  useEffect(() => {
    if (mapping) {
      setPlaidPrimaryCategory(mapping.plaid_primary_category)
      setPlaidDetailedCategory(mapping.plaid_detailed_category || '')
      setCategoryId(mapping.category_id)
      setConfidence(mapping.confidence)
      setAutoApply(mapping.auto_apply)
    } else {
      // Reset form for create
      setPlaidPrimaryCategory('')
      setPlaidDetailedCategory('')
      setCategoryId(undefined)
      setConfidence(1.0)
      setAutoApply(true)
    }
  }, [mapping, isOpen])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: plaidMappingsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plaid-mappings'] })
      onClose()
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: any }) =>
      plaidMappingsApi.update(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plaid-mappings'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!categoryId) {
      alert('Please select a category')
      return
    }

    const mappingData = {
      plaid_primary_category: plaidPrimaryCategory,
      plaid_detailed_category: plaidDetailedCategory || undefined,
      category_id: categoryId,
      confidence,
      auto_apply: autoApply,
    }

    if (isEdit && mapping) {
      updateMutation.mutate({
        id: mapping.id,
        updates: {
          category_id: categoryId,
          confidence,
          auto_apply: autoApply,
        },
      })
    } else {
      createMutation.mutate(mappingData)
    }
  }

  if (!isOpen) return null

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {isEdit ? 'Edit Plaid Category Mapping' : 'Create Plaid Category Mapping'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Plaid Primary Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Plaid Primary Category *
            </label>
            <input
              type="text"
              className="input"
              value={plaidPrimaryCategory}
              onChange={(e) => setPlaidPrimaryCategory(e.target.value)}
              placeholder="e.g., FOOD_AND_DRINK"
              required
              disabled={isEdit}
            />
            <p className="text-xs text-gray-500 mt-1">
              The primary category from Plaid (e.g., FOOD_AND_DRINK, TRANSFER, etc.)
            </p>
          </div>

          {/* Plaid Detailed Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Plaid Detailed Category (Optional)
            </label>
            <input
              type="text"
              className="input"
              value={plaidDetailedCategory}
              onChange={(e) => setPlaidDetailedCategory(e.target.value)}
              placeholder="e.g., FOOD_AND_DRINK_RESTAURANTS"
              disabled={isEdit}
            />
            <p className="text-xs text-gray-500 mt-1">
              Optional detailed category for more specific matching
            </p>
          </div>

          {/* MintBean Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              MintBean Category *
            </label>
            <select
              className="input"
              value={categoryId || ''}
              onChange={(e) => setCategoryId(Number(e.target.value))}
              required
            >
              <option value="">Select a category</option>
              {categories?.map((cat: Category) => (
                <option key={cat.id} value={cat.id}>
                  {cat.display_name} ({cat.category_type})
                </option>
              ))}
            </select>
          </div>

          {/* Confidence */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confidence: {confidence.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              className="w-full"
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
            />
            <p className="text-xs text-gray-500 mt-1">
              How confident you are in this mapping (0.0 - 1.0)
            </p>
          </div>

          {/* Auto Apply */}
          <div>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                checked={autoApply}
                onChange={(e) => setAutoApply(e.target.checked)}
              />
              <span className="ml-2 text-sm text-gray-700">
                Auto-apply to new transactions
              </span>
            </label>
            <p className="text-xs text-gray-500 mt-1 ml-6">
              Automatically categorize transactions matching this Plaid category
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button type="submit" disabled={isPending} className="btn btn-primary flex-1">
              {isPending ? 'Saving...' : isEdit ? 'Update Mapping' : 'Create Mapping'}
            </button>
            <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
