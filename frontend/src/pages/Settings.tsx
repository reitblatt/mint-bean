import { useAuth } from '@/contexts/AuthContext'

export default function Settings() {
  const { user } = useAuth()

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

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>
      <p className="text-sm text-gray-600 mb-8">
        Configure application-wide settings (Admin only)
      </p>

      <div className="max-w-4xl space-y-6">
        {/* Beancount Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Beancount Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beancount File Path
              </label>
              <input
                type="text"
                className="input"
                placeholder="/path/to/main.beancount"
                disabled
              />
              <p className="text-xs text-gray-500 mt-1">
                Path to your main Beancount ledger file
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Repository Path
              </label>
              <input
                type="text"
                className="input"
                placeholder="/path/to/beancount/repo"
                disabled
              />
              <p className="text-xs text-gray-500 mt-1">
                Git repository path for version control
              </p>
            </div>
          </div>
        </div>

        {/* Plaid Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Plaid Configuration</h2>
          <p className="text-sm text-gray-600 mb-4">
            Plaid API settings are managed in the Admin panel. This section displays the current
            environment only.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
              <select className="input" disabled>
                <option value="sandbox">Sandbox</option>
                <option value="development">Development</option>
                <option value="production">Production</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Configure Plaid settings in the Admin panel
              </p>
            </div>
          </div>
        </div>

        {/* Note about other settings */}
        <div className="card bg-blue-50 border border-blue-200">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-blue-600 mt-0.5 mr-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <h3 className="text-sm font-semibold text-blue-900 mb-1">
                Other Configuration Options
              </h3>
              <p className="text-sm text-blue-800">
                Plaid Category Mappings have been moved to the Categorization page under the "Plaid
                Category Mappings" tab. User management and Plaid API credentials are available in
                the Admin panel.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
