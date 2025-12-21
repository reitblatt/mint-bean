import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { onboardingApi, type OnboardingRequest } from '@/api/onboarding'

export default function Onboarding() {
  const queryClient = useQueryClient()
  const [step, setStep] = useState<'admin' | 'database' | 'plaid'>('admin')

  // Admin user fields
  const [adminEmail, setAdminEmail] = useState('')
  const [adminPassword, setAdminPassword] = useState('')
  const [adminConfirmPassword, setAdminConfirmPassword] = useState('')

  // Database fields
  const [databaseType, setDatabaseType] = useState<'sqlite' | 'mysql'>('sqlite')
  const [databaseHost, setDatabaseHost] = useState('localhost')
  const [databasePort, setDatabasePort] = useState('3306')
  const [databaseName, setDatabaseName] = useState('mintbean')
  const [databaseUser, setDatabaseUser] = useState('')
  const [databasePassword, setDatabasePassword] = useState('')
  const [sqlitePath, setSqlitePath] = useState('./data/mintbean.db')

  // Plaid fields
  const [plaidClientId, setPlaidClientId] = useState('')
  const [plaidSecret, setPlaidSecret] = useState('')
  const [plaidEnvironment, setPlaidEnvironment] = useState<'sandbox' | 'development' | 'production'>('sandbox')

  const [error, setError] = useState<string | null>(null)

  const onboardingMutation = useMutation({
    mutationFn: (data: OnboardingRequest) => onboardingApi.complete(data),
    onSuccess: () => {
      // Invalidate onboarding status and force reload to login page
      queryClient.invalidateQueries({ queryKey: ['onboarding-status'] })
      // Use window.location to force a full page reload
      window.location.href = '/login'
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to complete onboarding')
    },
  })

  const handleAdminNext = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!adminEmail || !adminPassword) {
      setError('All fields are required')
      return
    }

    if (adminPassword.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    if (adminPassword !== adminConfirmPassword) {
      setError('Passwords do not match')
      return
    }

    setStep('database')
  }

  const handleDatabaseNext = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation for MySQL
    if (databaseType === 'mysql') {
      if (!databaseHost || !databaseName || !databaseUser || !databasePassword) {
        setError('All MySQL fields are required')
        return
      }
    }

    setStep('plaid')
  }

  const handlePlaidSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!plaidClientId || !plaidSecret) {
      setError('Plaid Client ID and Secret are required')
      return
    }

    // Submit onboarding
    onboardingMutation.mutate({
      admin_email: adminEmail,
      admin_password: adminPassword,
      database_type: databaseType,
      database_host: databaseType === 'mysql' ? databaseHost : undefined,
      database_port: databaseType === 'mysql' ? parseInt(databasePort) : 3306,
      database_name: databaseType === 'mysql' ? databaseName : undefined,
      database_user: databaseType === 'mysql' ? databaseUser : undefined,
      database_password: databaseType === 'mysql' ? databasePassword : undefined,
      sqlite_path: databaseType === 'sqlite' ? sqlitePath : './data/mintbean.db',
      plaid_client_id: plaidClientId,
      plaid_secret: plaidSecret,
      plaid_environment: plaidEnvironment,
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h1 className="text-center text-3xl font-bold text-gray-900">
          Welcome to MintBean
        </h1>
        <p className="mt-2 text-center text-sm text-gray-600">
          Let's set up your account
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {/* Progress indicator */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className={`text-xs font-medium ${step === 'admin' ? 'text-indigo-600' : 'text-gray-500'}`}>
                1. Admin
              </span>
              <span className={`text-xs font-medium ${step === 'database' ? 'text-indigo-600' : 'text-gray-500'}`}>
                2. Database
              </span>
              <span className={`text-xs font-medium ${step === 'plaid' ? 'text-indigo-600' : 'text-gray-500'}`}>
                3. Plaid
              </span>
            </div>
            <div className="flex gap-2">
              <div className={`h-2 flex-1 rounded ${step === 'admin' ? 'bg-indigo-600' : 'bg-gray-200'}`} />
              <div className={`h-2 flex-1 rounded ${step === 'database' ? 'bg-indigo-600' : 'bg-gray-200'}`} />
              <div className={`h-2 flex-1 rounded ${step === 'plaid' ? 'bg-indigo-600' : 'bg-gray-200'}`} />
            </div>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {step === 'admin' ? (
            <form onSubmit={handleAdminNext}>
              <h2 className="text-lg font-medium text-gray-900 mb-4">Create Admin Account</h2>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  className="input"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  placeholder="admin@example.com"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  className="input"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  placeholder="Min. 8 characters"
                  required
                  minLength={8}
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confirm Password
                </label>
                <input
                  type="password"
                  className="input"
                  value={adminConfirmPassword}
                  onChange={(e) => setAdminConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary w-full">
                Next: Configure Database
              </button>
            </form>
          ) : step === 'database' ? (
            <form onSubmit={handleDatabaseNext}>
              <h2 className="text-lg font-medium text-gray-900 mb-4">Database Configuration</h2>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Database Type
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="database_type"
                      value="sqlite"
                      checked={databaseType === 'sqlite'}
                      onChange={() => setDatabaseType('sqlite')}
                      className="mr-2"
                    />
                    <span className="text-sm">SQLite (Recommended)</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="database_type"
                      value="mysql"
                      checked={databaseType === 'mysql'}
                      onChange={() => setDatabaseType('mysql')}
                      className="mr-2"
                    />
                    <span className="text-sm">MySQL</span>
                  </label>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  SQLite is perfect for single-user setups. Choose MySQL for multi-user deployments.
                </p>
              </div>

              {databaseType === 'sqlite' ? (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Database File Path
                  </label>
                  <input
                    type="text"
                    className="input"
                    value={sqlitePath}
                    onChange={(e) => setSqlitePath(e.target.value)}
                    placeholder="./data/mintbean.db"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Path where the SQLite database file will be stored
                  </p>
                </div>
              ) : (
                <>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      MySQL Host
                    </label>
                    <input
                      type="text"
                      className="input"
                      value={databaseHost}
                      onChange={(e) => setDatabaseHost(e.target.value)}
                      placeholder="localhost"
                      required
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      MySQL Port
                    </label>
                    <input
                      type="number"
                      className="input"
                      value={databasePort}
                      onChange={(e) => setDatabasePort(e.target.value)}
                      placeholder="3306"
                      required
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Database Name
                    </label>
                    <input
                      type="text"
                      className="input"
                      value={databaseName}
                      onChange={(e) => setDatabaseName(e.target.value)}
                      placeholder="mintbean"
                      required
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      MySQL Username
                    </label>
                    <input
                      type="text"
                      className="input"
                      value={databaseUser}
                      onChange={(e) => setDatabaseUser(e.target.value)}
                      placeholder="mintbean_user"
                      required
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      MySQL Password
                    </label>
                    <input
                      type="password"
                      className="input"
                      value={databasePassword}
                      onChange={(e) => setDatabasePassword(e.target.value)}
                      placeholder="Your MySQL password"
                      required
                    />
                  </div>
                </>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep('admin')}
                  className="btn btn-secondary flex-1"
                >
                  Back
                </button>
                <button type="submit" className="btn btn-primary flex-1">
                  Next: Configure Plaid
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handlePlaidSubmit}>
              <h2 className="text-lg font-medium text-gray-900 mb-4">Configure Plaid</h2>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Plaid Client ID
                </label>
                <input
                  type="text"
                  className="input"
                  value={plaidClientId}
                  onChange={(e) => setPlaidClientId(e.target.value)}
                  placeholder="Your Plaid Client ID"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  Get your credentials from the{' '}
                  <a
                    href="https://dashboard.plaid.com/developers/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:text-indigo-500"
                  >
                    Plaid Dashboard
                  </a>
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Plaid Secret
                </label>
                <input
                  type="password"
                  className="input"
                  value={plaidSecret}
                  onChange={(e) => setPlaidSecret(e.target.value)}
                  placeholder="Your Plaid Secret"
                  required
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Environment
                </label>
                <select
                  className="input"
                  value={plaidEnvironment}
                  onChange={(e) => setPlaidEnvironment(e.target.value as 'sandbox' | 'development' | 'production')}
                >
                  <option value="sandbox">Sandbox (Testing)</option>
                  <option value="development">Development</option>
                  <option value="production">Production</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  Use Sandbox for testing, Production for real bank accounts
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep('database')}
                  className="btn btn-secondary flex-1"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="btn btn-primary flex-1"
                  disabled={onboardingMutation.isPending}
                >
                  {onboardingMutation.isPending ? 'Setting up...' : 'Complete Setup'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
