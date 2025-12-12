import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '@/api/categories'
import CategoryTree from '@/components/CategoryTree'
import CategoryFormModal from '@/components/CategoryFormModal'
import type { CategoryTreeNode } from '@/api/types'

export default function Categories() {
  const queryClient = useQueryClient()
  const [selectedCategory, setSelectedCategory] = useState<CategoryTreeNode | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<CategoryTreeNode | undefined>()
  const [categoryTypeFilter, setCategoryTypeFilter] = useState<string>('expense')
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  // Fetch category tree
  const { data: categoryTree, isLoading, error } = useQuery({
    queryKey: ['categories', 'tree', categoryTypeFilter],
    queryFn: () => categoriesApi.tree(categoryTypeFilter || undefined, false),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: categoriesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setDeleteConfirmId(null)
      if (selectedCategory?.id === deleteConfirmId) {
        setSelectedCategory(null)
      }
    },
  })

  const handleEdit = (category: CategoryTreeNode) => {
    setEditingCategory(category)
    setIsModalOpen(true)
  }

  const handleDelete = (category: CategoryTreeNode) => {
    setDeleteConfirmId(category.id)
  }

  const confirmDelete = () => {
    if (deleteConfirmId) {
      deleteMutation.mutate(deleteConfirmId)
    }
  }

  const handleCreateNew = () => {
    setEditingCategory(undefined)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingCategory(undefined)
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Categories</h1>
        <button onClick={handleCreateNew} className="btn btn-primary">
          + New Category
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['expense', 'income', 'transfer'].map((type) => (
              <button
                key={type}
                onClick={() => setCategoryTypeFilter(type)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  categoryTypeFilter === type
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
            <button
              onClick={() => setCategoryTypeFilter('')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                categoryTypeFilter === ''
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Tree */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Category Hierarchy</h2>
              <p className="text-sm text-gray-600 mt-1">
                Organize your categories with parent-child relationships
              </p>
            </div>

            <div className="p-4">
              {isLoading && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <p className="text-gray-600 mt-2">Loading categories...</p>
                </div>
              )}

              {error && (
                <div className="text-center py-12 text-red-600">
                  <p>Error loading categories</p>
                  <p className="text-sm mt-1">{(error as Error).message}</p>
                </div>
              )}

              {categoryTree && (
                <CategoryTree
                  nodes={categoryTree}
                  selectedId={selectedCategory?.id}
                  onSelect={setSelectedCategory}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  showTypeTag={categoryTypeFilter === ''}
                />
              )}
            </div>
          </div>
        </div>

        {/* Details Panel */}
        <div className="lg:col-span-1">
          {selectedCategory ? (
            <div className="card">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Category Details</h2>
              </div>

              <div className="p-4 space-y-4">
                {/* Display Name */}
                <div>
                  <div className="flex items-center gap-2">
                    {selectedCategory.icon && (
                      <span className="text-2xl">{selectedCategory.icon}</span>
                    )}
                    <h3 className="text-xl font-bold text-gray-900">
                      {selectedCategory.display_name}
                    </h3>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-sm text-gray-600">Transactions</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {selectedCategory.transaction_count}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-sm text-gray-600">Children</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {selectedCategory.children?.length || 0}
                    </div>
                  </div>
                </div>

                {/* Type Badge */}
                <div>
                  <div className="text-sm text-gray-600 mb-1">Type</div>
                  <span className="inline-block px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800">
                    {selectedCategory.category_type}
                  </span>
                </div>

                {/* Actions */}
                <div className="pt-4 space-y-2">
                  <button
                    onClick={() => handleEdit(selectedCategory)}
                    className="btn btn-primary w-full"
                  >
                    Edit Category
                  </button>
                  <button
                    onClick={() => handleDelete(selectedCategory)}
                    className="btn btn-secondary w-full text-red-600 hover:bg-red-50"
                  >
                    Delete Category
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="card p-6 text-center text-gray-500">
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
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                />
              </svg>
              <p className="mt-2">Select a category to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Category Form Modal */}
      <CategoryFormModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        category={editingCategory}
        allCategories={categoryTree || []}
      />

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Category?</h3>
            <p className="text-gray-600 mb-6">
              This will mark the category as inactive. Transactions will keep their category
              assignment. Are you sure?
            </p>
            <div className="flex gap-3">
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="btn btn-primary flex-1 bg-red-600 hover:bg-red-700"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="btn btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
