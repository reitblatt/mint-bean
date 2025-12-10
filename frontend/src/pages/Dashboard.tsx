export default function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Summary Cards */}
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Total Balance</div>
          <div className="text-2xl font-bold text-gray-900">$0.00</div>
          <div className="text-xs text-gray-500 mt-1">Across all accounts</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">This Month Spending</div>
          <div className="text-2xl font-bold text-red-600">$0.00</div>
          <div className="text-xs text-gray-500 mt-1">vs $0.00 last month</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">This Month Income</div>
          <div className="text-2xl font-bold text-green-600">$0.00</div>
          <div className="text-xs text-gray-500 mt-1">vs $0.00 last month</div>
        </div>

        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Uncategorized</div>
          <div className="text-2xl font-bold text-gray-900">0</div>
          <div className="text-xs text-gray-500 mt-1">transactions</div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Transactions</h2>
        <div className="text-center py-12 text-gray-500">
          No transactions yet. Connect your accounts to get started.
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <button className="card hover:shadow-md transition-shadow text-left">
          <div className="font-medium text-gray-900 mb-1">Sync Transactions</div>
          <div className="text-sm text-gray-600">Pull latest data from Plaid</div>
        </button>

        <button className="card hover:shadow-md transition-shadow text-left">
          <div className="font-medium text-gray-900 mb-1">Review Uncategorized</div>
          <div className="text-sm text-gray-600">Categorize pending transactions</div>
        </button>

        <button className="card hover:shadow-md transition-shadow text-left">
          <div className="font-medium text-gray-900 mb-1">Sync to Beancount</div>
          <div className="text-sm text-gray-600">Write changes to beancount files</div>
        </button>
      </div>
    </div>
  )
}
