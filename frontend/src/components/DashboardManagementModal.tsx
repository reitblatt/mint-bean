import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboardsApi } from '@/api/dashboards'
import type { DashboardTab, DashboardTabCreate, DashboardTabUpdate } from '@/api/types'

interface DashboardManagementModalProps {
  isOpen: boolean
  onClose: () => void
  tabs: DashboardTab[]
  currentTabId?: number
}

export default function DashboardManagementModal({
  isOpen,
  onClose,
  tabs,
  currentTabId,
}: DashboardManagementModalProps) {
  const queryClient = useQueryClient()
  const [editingTab, setEditingTab] = useState<DashboardTab | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    icon: '',
    is_default: false,
  })

  const createTabMutation = useMutation({
    mutationFn: (data: DashboardTabCreate) => dashboardsApi.createTab(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-tabs'] })
      resetForm()
    },
  })

  const updateTabMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: DashboardTabUpdate }) =>
      dashboardsApi.updateTab(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-tabs'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-tab'] })
      resetForm()
    },
  })

  const deleteTabMutation = useMutation({
    mutationFn: (id: number) => dashboardsApi.deleteTab(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-tabs'] })
    },
  })

  const resetForm = () => {
    setFormData({ name: '', icon: '', is_default: false })
    setEditingTab(null)
    setIsCreating(false)
  }

  const handleEdit = (tab: DashboardTab) => {
    setEditingTab(tab)
    setFormData({
      name: tab.name,
      icon: tab.icon || '',
      is_default: tab.is_default,
    })
    setIsCreating(false)
  }

  const handleCreate = () => {
    setIsCreating(true)
    setEditingTab(null)
    setFormData({ name: '', icon: '', is_default: false })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (editingTab) {
      updateTabMutation.mutate({
        id: editingTab.id,
        data: {
          name: formData.name,
          icon: formData.icon || undefined,
          is_default: formData.is_default,
        },
      })
    } else if (isCreating) {
      // Calculate next display order
      const maxOrder = Math.max(...tabs.map((t) => t.display_order), -1)
      createTabMutation.mutate({
        name: formData.name,
        icon: formData.icon || undefined,
        is_default: formData.is_default,
        display_order: maxOrder + 1,
      })
    }
  }

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this dashboard tab? All widgets will be deleted.')) {
      deleteTabMutation.mutate(id)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Manage Dashboards</h2>
        </div>

        <div className="p-6">
          {/* Tab List */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-700">Your Dashboard Tabs</h3>
              <button
                onClick={handleCreate}
                className="btn btn-primary text-sm"
                disabled={isCreating || !!editingTab}
              >
                + New Tab
              </button>
            </div>

            <div className="space-y-2">
              {tabs.map((tab) => (
                <div
                  key={tab.id}
                  className={`flex items-center justify-between p-3 border rounded-lg ${
                    tab.id === currentTabId ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {tab.icon && <span className="text-lg">{tab.icon}</span>}
                    <div>
                      <div className="font-medium text-gray-900">{tab.name}</div>
                      {tab.is_default && (
                        <span className="text-xs text-indigo-600">Default</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(tab)}
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      Edit
                    </button>
                    {tabs.length > 1 && (
                      <button
                        onClick={() => handleDelete(tab.id)}
                        className="text-sm text-red-600 hover:text-red-800"
                        disabled={deleteTabMutation.isPending}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Create/Edit Form */}
          {(isCreating || editingTab) && (
            <form onSubmit={handleSubmit} className="border-t pt-6">
              <h3 className="text-sm font-medium text-gray-700 mb-4">
                {editingTab ? 'Edit Tab' : 'Create New Tab'}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tab Name *
                  </label>
                  <input
                    type="text"
                    className="input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Overview, Spending Analysis"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Icon (optional)
                  </label>
                  <input
                    type="text"
                    className="input"
                    value={formData.icon}
                    onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                    placeholder="e.g., 📊, 💰, 📈"
                    maxLength={2}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Enter an emoji to display next to the tab name
                  </p>
                </div>

                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_default}
                      onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700">Set as default tab</span>
                  </label>
                </div>

                <div className="flex gap-3 pt-4">
                  <button type="submit" className="btn btn-primary flex-1">
                    {editingTab ? 'Update Tab' : 'Create Tab'}
                  </button>
                  <button
                    type="button"
                    onClick={resetForm}
                    className="btn btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end">
          <button onClick={onClose} className="btn btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
