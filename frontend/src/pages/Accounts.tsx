import { useQuery } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'

export default function Accounts() {
  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list(),
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Accounts</h1>
        <button className="btn btn-primary">Add Account</button>
      </div>

      {isLoading && <div className="text-center py-12 text-gray-600">Loading accounts...</div>}

      {accounts && accounts.length === 0 && (
        <div className="card text-center py-12">
          <div className="text-gray-900 font-medium mb-2">No accounts connected</div>
          <div className="text-gray-600 mb-4">Connect your financial accounts to get started</div>
          <button className="btn btn-primary">Connect with Plaid</button>
        </div>
      )}

      {accounts && accounts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <div key={account.id} className="card">
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
  )
}
