import { useState, useEffect } from 'react'
import { apiClient } from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'

interface PlaidSettings {
  client_id: string
  sandbox_secret: string
  production_secret: string
  environment: 'sandbox' | 'production'
}

interface PlaidSettingsResponse {
  client_id: string
  sandbox_secret_masked: string | null
  production_secret_masked: string | null
  environment: string
}

interface User {
  id: number
  email: string
  is_admin: boolean
  is_active: boolean
  archived_at: string | null
  created_at: string
  updated_at: string
}

export default function Admin() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'users' | 'plaid'>('users')

  // Plaid settings state
  const [plaidSettings, setPlaidSettings] = useState<PlaidSettings>({
    client_id: '',
    sandbox_secret: '',
    production_secret: '',
    environment: 'sandbox',
  })
  const [currentPlaidSettings, setCurrentPlaidSettings] = useState<PlaidSettingsResponse | null>(null)
  const [plaidLoading, setPlaidLoading] = useState(false)
  const [plaidError, setPlaidError] = useState<string | null>(null)
  const [plaidSuccess, setPlaidSuccess] = useState<string | null>(null)

  // Users state
  const [users, setUsers] = useState<User[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [usersError, setUsersError] = useState<string | null>(null)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [newUser, setNewUser] = useState({ email: '', password: '', is_admin: false })
  const [deleteModalUser, setDeleteModalUser] = useState<User | null>(null)
  const [restoreModalUser, setRestoreModalUser] = useState<User | null>(null)

  const loadPlaidSettings = async () => {
    try {
      const response = await apiClient.get<PlaidSettingsResponse>('/settings/plaid')
      setCurrentPlaidSettings(response.data)
      setPlaidSettings({
        client_id: response.data.client_id,
        sandbox_secret: '', // Don't pre-fill secrets for security
        production_secret: '', // Don't pre-fill secrets for security
        environment: response.data.environment as 'sandbox' | 'production',
      })
    } catch (error) {
      console.error('Failed to load Plaid settings:', error)
    }
  }

  const loadUsers = async () => {
    setUsersLoading(true)
    setUsersError(null)
    try {
      const response = await apiClient.get<User[]>('/admin/users')
      setUsers(response.data)
    } catch (error) {
      setUsersError('Failed to load users')
      console.error('Failed to load users:', error)
    } finally {
      setUsersLoading(false)
    }
  }

  // Load data on mount
  useEffect(() => {
    loadPlaidSettings()
    loadUsers()
  }, [])

  // Check if user is admin
  if (!user?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">You do not have permission to access this page.</p>
        </div>
      </div>
    )
  }

  const handlePlaidSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPlaidLoading(true)
    setPlaidError(null)
    setPlaidSuccess(null)

    try {
      // Only send non-empty fields to avoid overwriting existing secrets with empty strings
      const payload: Partial<PlaidSettings> = {
        client_id: plaidSettings.client_id || undefined,
        environment: plaidSettings.environment,
      }
      // Only include secrets if they're non-empty (user is actually updating them)
      if (plaidSettings.sandbox_secret) {
        payload.sandbox_secret = plaidSettings.sandbox_secret
      }
      if (plaidSettings.production_secret) {
        payload.production_secret = plaidSettings.production_secret
      }

      const response = await apiClient.put<PlaidSettingsResponse>('/settings/plaid', payload)
      setCurrentPlaidSettings(response.data)
      setPlaidSuccess('Plaid settings updated successfully!')
      // Clear the secret fields
      setPlaidSettings({
        ...plaidSettings,
        sandbox_secret: '',
        production_secret: ''
      })
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      setPlaidError(error.response?.data?.detail || 'Failed to update settings')
    } finally {
      setPlaidLoading(false)
    }
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setUsersError(null)

    try {
      await apiClient.post('/admin/users', newUser)
      setShowCreateUser(false)
      setNewUser({ email: '', password: '', is_admin: false })
      loadUsers()
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      setUsersError(error.response?.data?.detail || 'Failed to create user')
    }
  }

  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await apiClient.patch(`/admin/users/${userId}`, { is_active: !currentStatus })
      loadUsers()
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      setUsersError(error.response?.data?.detail || 'Failed to update user status')
    }
  }

  const handleDeleteUser = async (userId: number, hardDelete: boolean) => {
    try {
      await apiClient.delete(`/admin/users/${userId}`, {
        data: { hard_delete: hardDelete }
      })
      setDeleteModalUser(null)
      loadUsers()
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      setUsersError(error.response?.data?.detail || 'Failed to delete user')
    }
  }

  const handleRestoreUser = async (userId: number, restoreData: boolean) => {
    try {
      await apiClient.post(`/admin/users/${userId}/restore`, {
        restore_data: restoreData
      })
      setRestoreModalUser(null)
      loadUsers()
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      setUsersError(error.response?.data?.detail || 'Failed to restore user')
    }
  }

  const handleResetPassword = async (userId: number) => {
    const newPassword = prompt('Enter new password for this user:')
    if (!newPassword) return

    try {
      await apiClient.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword })
      alert('Password reset successfully!')
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      alert(error.response?.data?.detail || 'Failed to reset password')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('users')}
            className={`${
              activeTab === 'users'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            User Management
          </button>
          <button
            onClick={() => setActiveTab('plaid')}
            className={`${
              activeTab === 'plaid'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Plaid Settings
          </button>
        </nav>
      </div>

      {/* Plaid Settings Tab */}
      {activeTab === 'plaid' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Plaid API Configuration</h2>

          {plaidError && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800">{plaidError}</p>
            </div>
          )}

          {plaidSuccess && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="text-sm text-green-800">{plaidSuccess}</p>
            </div>
          )}

          <form onSubmit={handlePlaidSubmit} className="space-y-6">
            {/* Client ID (shared across environments) */}
            <div>
              <label htmlFor="client_id" className="block text-sm font-medium text-gray-700 mb-1">
                Client ID
              </label>
              <input
                type="text"
                id="client_id"
                value={plaidSettings.client_id}
                onChange={(e) => setPlaidSettings({ ...plaidSettings, client_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter Plaid client ID"
              />
              <p className="mt-1 text-sm text-gray-500">
                Same client ID is used for all environments
              </p>
            </div>

            {/* Sandbox Secret */}
            <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
              <h3 className="text-md font-semibold text-gray-900 mb-3">Sandbox Secret</h3>
              <div>
                <label htmlFor="sandbox_secret" className="block text-sm font-medium text-gray-700 mb-1">
                  Secret
                </label>
                <input
                  type="password"
                  id="sandbox_secret"
                  value={plaidSettings.sandbox_secret}
                  onChange={(e) => setPlaidSettings({ ...plaidSettings, sandbox_secret: e.target.value })}
                  placeholder={currentPlaidSettings?.sandbox_secret_masked || 'Enter sandbox secret'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">Leave blank to keep current secret</p>
              </div>
            </div>

            {/* Production Secret */}
            <div className="border border-red-200 rounded-md p-4 bg-red-50">
              <h3 className="text-md font-semibold text-gray-900 mb-3">Production Secret</h3>
              <div>
                <label htmlFor="production_secret" className="block text-sm font-medium text-gray-700 mb-1">
                  Secret
                </label>
                <input
                  type="password"
                  id="production_secret"
                  value={plaidSettings.production_secret}
                  onChange={(e) => setPlaidSettings({ ...plaidSettings, production_secret: e.target.value })}
                  placeholder={currentPlaidSettings?.production_secret_masked || 'Enter production secret'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">Leave blank to keep current secret</p>
              </div>
            </div>

            {/* Current Environment */}
            <div>
              <label htmlFor="environment" className="block text-sm font-medium text-gray-700 mb-1">
                Active Environment
              </label>
              <select
                id="environment"
                value={plaidSettings.environment}
                onChange={(e) =>
                  setPlaidSettings({
                    ...plaidSettings,
                    environment: e.target.value as 'sandbox' | 'production',
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="sandbox">Sandbox</option>
                <option value="production">Production</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">
                This determines which credentials are used and which data is displayed
              </p>
            </div>

            <button
              type="submit"
              disabled={plaidLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {plaidLoading ? 'Saving...' : 'Save Plaid Settings'}
            </button>
          </form>
        </div>
      )}

      {/* Delete User Modal */}
      {deleteModalUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete User</h3>
            <p className="text-gray-600 mb-2">
              What would you like to do with <strong>{deleteModalUser.email}</strong>?
            </p>

            <div className="space-y-4 mt-6">
              <button
                onClick={() => handleDeleteUser(deleteModalUser.id, false)}
                className="w-full bg-yellow-600 text-white py-2 px-4 rounded-md hover:bg-yellow-700 text-left"
              >
                <div className="font-semibold">Archive User</div>
                <div className="text-sm text-yellow-100">
                  Deactivate account and keep all data. Can be restored later.
                </div>
              </button>

              <button
                onClick={() => {
                  if (confirm(`Are you sure you want to permanently delete ${deleteModalUser.email}? This action cannot be undone and will remove all user data.`)) {
                    handleDeleteUser(deleteModalUser.id, true)
                  }
                }}
                className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 text-left"
              >
                <div className="font-semibold">Delete Permanently</div>
                <div className="text-sm text-red-100">
                  Permanently remove user and all associated data. Cannot be undone.
                </div>
              </button>

              <button
                onClick={() => setDeleteModalUser(null)}
                className="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Restore User Modal */}
      {restoreModalUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Restore User</h3>
            <p className="text-gray-600 mb-2">
              How would you like to restore <strong>{restoreModalUser.email}</strong>?
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Archived on: {new Date(restoreModalUser.archived_at!).toLocaleDateString()}
            </p>

            <div className="space-y-4 mt-6">
              <button
                onClick={() => handleRestoreUser(restoreModalUser.id, true)}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 text-left"
              >
                <div className="font-semibold">Restore with Data</div>
                <div className="text-sm text-green-100">
                  Reactivate account with all historical data intact.
                </div>
              </button>

              <button
                onClick={() => {
                  if (confirm(`Are you sure you want to restore ${restoreModalUser.email} with fresh data? This will delete all their historical data.`)) {
                    handleRestoreUser(restoreModalUser.id, false)
                  }
                }}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 text-left"
              >
                <div className="font-semibold">Restore Fresh</div>
                <div className="text-sm text-blue-100">
                  Reactivate account but delete all data and start fresh.
                </div>
              </button>

              <button
                onClick={() => setRestoreModalUser(null)}
                className="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* User Management Tab */}
      {activeTab === 'users' && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">User Management</h2>
            <button
              onClick={() => setShowCreateUser(!showCreateUser)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
            >
              {showCreateUser ? 'Cancel' : 'Create User'}
            </button>
          </div>

          {usersError && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800">{usersError}</p>
            </div>
          )}

          {/* Create User Form */}
          {showCreateUser && (
            <form onSubmit={handleCreateUser} className="mb-6 p-4 bg-gray-50 rounded-md space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  minLength={8}
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_admin"
                  checked={newUser.is_admin}
                  onChange={(e) => setNewUser({ ...newUser, is_admin: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_admin" className="ml-2 text-sm text-gray-700">
                  Admin user
                </label>
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 text-sm"
              >
                Create User
              </button>
            </form>
          )}

          {/* Users Table */}
          {usersLoading ? (
            <div className="text-center py-8">
              <p className="text-gray-600">Loading users...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {u.is_admin ? (
                          <span className="inline-flex px-2 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                            Admin
                          </span>
                        ) : (
                          <span className="inline-flex px-2 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                            User
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {u.archived_at ? (
                          <span className="inline-flex px-2 text-xs font-semibold rounded-full bg-gray-400 text-white">
                            Archived
                          </span>
                        ) : u.is_active ? (
                          <span className="inline-flex px-2 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex px-2 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {u.archived_at ? (
                          // Archived user - show restore button
                          <button
                            onClick={() => setRestoreModalUser(u)}
                            className="text-green-600 hover:text-green-900"
                          >
                            Restore
                          </button>
                        ) : (
                          // Active/Inactive user - show normal actions
                          <>
                            <button
                              onClick={() => handleToggleUserStatus(u.id, u.is_active)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              {u.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                            <button
                              onClick={() => handleResetPassword(u.id)}
                              className="text-yellow-600 hover:text-yellow-900"
                            >
                              Reset Password
                            </button>
                            {u.id !== user?.id && (
                              <button
                                onClick={() => setDeleteModalUser(u)}
                                className="text-red-600 hover:text-red-900"
                              >
                                Delete
                              </button>
                            )}
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
