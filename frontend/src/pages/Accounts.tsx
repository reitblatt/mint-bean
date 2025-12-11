import { useQuery } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'
import PlaidAccountsManager from '@/components/PlaidAccountsManager'
import AccountsHierarchy from '@/components/AccountsHierarchy'

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

      {/* Accounts Hierarchy */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">All Accounts</h2>

        {isLoading && <div className="text-center py-12 text-gray-600">Loading accounts...</div>}

        {accounts && <AccountsHierarchy accounts={accounts} />}
      </div>
    </div>
  )
}
