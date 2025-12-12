import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api/categories'
import type { Category, CategoryTreeNode } from '@/api/types'

interface CategoryFormModalProps {
  isOpen: boolean
  onClose: () => void
  category?: Category | CategoryTreeNode
  allCategories: CategoryTreeNode[]
}

export default function CategoryFormModal({
  isOpen,
  onClose,
  category,
  allCategories,
}: CategoryFormModalProps) {
  const queryClient = useQueryClient()
  const isEdit = !!category

  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    beancount_account: '',
    category_type: 'expense',
    parent_id: undefined as number | undefined,
    icon: '',
    color: '',
    description: '',
  })

  useEffect(() => {
    if (category) {
      setFormData({
        name: category.name,
        display_name: category.display_name,
        beancount_account: 'beancount_account' in category ? category.beancount_account : '',
        category_type: category.category_type,
        parent_id: category.parent_id,
        icon: category.icon || '',
        color: category.color || '',
        description: 'description' in category ? category.description || '' : '',
      })
    } else {
      setFormData({
        name: '',
        display_name: '',
        beancount_account: '',
        category_type: 'expense',
        parent_id: undefined,
        icon: '',
        color: '',
        description: '',
      })
    }
  }, [category, isOpen])

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      onClose()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: { id: number; updates: Partial<Category> }) =>
      categoriesApi.update(data.id, data.updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (isEdit && 'id' in category) {
      updateMutation.mutate({
        id: category.id,
        updates: formData,
      })
    } else {
      createMutation.mutate(formData)
    }
  }

  // Flatten tree for parent selection dropdown
  const flattenTree = (nodes: CategoryTreeNode[], prefix = ''): Array<{ id: number; label: string }> => {
    return nodes.flatMap((node) => {
      const current = { id: node.id, label: prefix + node.display_name }
      if (node.children && node.children.length > 0) {
        return [current, ...flattenTree(node.children, prefix + '  ')]
      }
      return [current]
    })
  }

  const parentOptions = flattenTree(allCategories)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {isEdit ? 'Edit Category' : 'Create Category'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Display Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Display Name *
              </label>
              <input
                type="text"
                required
                className="input"
                value={formData.display_name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, display_name: e.target.value }))
                }
                placeholder="e.g., Groceries"
              />
            </div>

            {/* Name (ID) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name (ID) *
              </label>
              <input
                type="text"
                required
                className="input"
                value={formData.name}
                onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., groceries"
              />
              <p className="text-xs text-gray-500 mt-1">
                Lowercase, no spaces. Used as unique identifier.
              </p>
            </div>

            {/* Category Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category Type *
              </label>
              <select
                required
                className="input"
                value={formData.category_type}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, category_type: e.target.value }))
                }
              >
                <option value="expense">Expense</option>
                <option value="income">Income</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>

            {/* Parent Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Parent Category
              </label>
              <select
                className="input"
                value={formData.parent_id || ''}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    parent_id: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
              >
                <option value="">None (Top Level)</option>
                {parentOptions
                  .filter((opt) => !isEdit || opt.id !== category.id) // Don't allow selecting self as parent
                  .map((opt) => (
                    <option key={opt.id} value={opt.id}>
                      {opt.label}
                    </option>
                  ))}
              </select>
            </div>

            {/* Beancount Account */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beancount Account *
              </label>
              <input
                type="text"
                required
                className="input"
                value={formData.beancount_account}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, beancount_account: e.target.value }))
                }
                placeholder="e.g., Expenses:Food:Groceries"
              />
            </div>

            {/* Icon & Color */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Icon</label>
                <input
                  type="text"
                  className="input"
                  value={formData.icon}
                  onChange={(e) => setFormData((prev) => ({ ...prev, icon: e.target.value }))}
                  placeholder="e.g., 🛒"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                <input
                  type="text"
                  className="input"
                  value={formData.color}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, color: e.target.value }))
                  }
                  placeholder="e.g., #3B82F6"
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                className="input"
                rows={3}
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, description: e.target.value }))
                }
                placeholder="Optional description..."
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button type="submit" className="btn btn-primary flex-1" disabled={createMutation.isPending || updateMutation.isPending}>
                {createMutation.isPending || updateMutation.isPending ? 'Saving...' : isEdit ? 'Update Category' : 'Create Category'}
              </button>
              <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
                Cancel
              </button>
            </div>

            {/* Error */}
            {(createMutation.isError || updateMutation.isError) && (
              <div className="text-sm text-red-600 mt-2">
                Error: {(createMutation.error || updateMutation.error)?.message}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}
