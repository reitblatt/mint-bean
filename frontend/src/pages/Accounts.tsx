import { useQuery } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'
import PlaidAccountsManager from '@/components/PlaidAccountsManager'

export default function Accounts() {
  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list(),
  })

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Accounts</h1>
        <p className="text-gray-600 mt-2">
          Manage your connected bank accounts and sync transactions
        </p>
      </div>

      {/* Plaid Connection Manager */}
      <div className="mb-8">
        <PlaidAccountsManager />
      </div>

      {/* Accounts List */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">All Accounts</h2>

        {isLoading && <div className="text-center py-12 text-gray-600">Loading accounts...</div>}

        {accounts && accounts.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-900 font-medium mb-2">No accounts yet</div>
            <div className="text-gray-600">Connect a bank account above to see your accounts here</div>
          </div>
        )}

        {accounts && accounts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {accounts.map((account) => (
              <div key={account.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-medium text-gray-900">{account.name}</div>
                    {account.official_name && (
                      <div className="text-sm text-gray-600">{account.official_name}</div>
                    )}
                  </div>
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                    {account.type}
                  </span>
                </div>

                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {account.current_balance
                    ? new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: account.currency,
                      }).format(account.current_balance)
                    : 'N/A'}
                </div>

                <div className="text-sm text-gray-600 mb-3">{account.beancount_account}</div>

                {account.institution_name && (
                  <div className="text-xs text-gray-500">{account.institution_name}</div>
                )}

                {account.needs_reconnection && (
                  <div className="mt-3 text-xs text-red-600 font-medium">
                    Needs reconnection
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
