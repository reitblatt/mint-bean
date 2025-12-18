import { useState } from 'react'
import { formatLastSync, getAccountTypeInfo } from '@/utils/accountTypes'
import type { Account } from '@/api/accounts'

interface AccountsHierarchyProps {
  accounts: Account[]
}

interface GroupedAccounts {
  [institution: string]: Account[]
}

export default function AccountsHierarchy({ accounts }: AccountsHierarchyProps) {
  const [expandedInstitutions, setExpandedInstitutions] = useState<Set<string>>(new Set())

  // Group accounts by institution
  const groupedAccounts: GroupedAccounts = accounts.reduce((acc, account) => {
    const institution = account.institution_name || 'Other Accounts'
    if (!acc[institution]) {
      acc[institution] = []
    }
    acc[institution].push(account)
    return acc
  }, {} as GroupedAccounts)

  // Sort institutions
  const sortedInstitutions = Object.keys(groupedAccounts).sort((a, b) => {
    // Put "Other Accounts" at the end
    if (a === 'Other Accounts') return 1
    if (b === 'Other Accounts') return -1
    return a.localeCompare(b)
  })

  const toggleInstitution = (institution: string) => {
    const newExpanded = new Set(expandedInstitutions)
    if (newExpanded.has(institution)) {
      newExpanded.delete(institution)
    } else {
      newExpanded.add(institution)
    }
    setExpandedInstitutions(newExpanded)
  }

  // Calculate total balance per institution
  const getInstitutionTotal = (accounts: Account[]): number => {
    return accounts.reduce((sum, acc) => {
      const balance = acc.current_balance ?? 0
      // Subtract credit card balances (they're liabilities)
      const typeInfo = getAccountTypeInfo(acc.type, acc.subtype)
      return typeInfo.category === 'credit' || typeInfo.category === 'loan'
        ? sum - Math.abs(balance)
        : sum + balance
    }, 0)
  }

  if (accounts.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-900 font-medium mb-2">No accounts yet</div>
        <div className="text-gray-600">Connect a bank account to see your accounts here</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sortedInstitutions.map((institution) => {
        const institutionAccounts = groupedAccounts[institution]
        const isExpanded = expandedInstitutions.has(institution)
        const totalBalance = getInstitutionTotal(institutionAccounts)

        return (
          <div key={institution} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* Institution Header */}
            <button
              onClick={() => toggleInstitution(institution)}
              className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏦</span>
                <div className="text-left">
                  <div className="font-semibold text-gray-900">{institution}</div>
                  <div className="text-sm text-gray-600">
                    {institutionAccounts.length} account{institutionAccounts.length === 1 ? '' : 's'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-xl font-bold text-gray-900">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(totalBalance)}
                  </div>
                  <div className="text-xs text-gray-500">Total</div>
                </div>
                <svg
                  className={`w-5 h-5 text-gray-500 transition-transform ${
                    isExpanded ? 'transform rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            {/* Accounts List */}
            {isExpanded && (
              <div className="divide-y divide-gray-200">
                {institutionAccounts.map((account) => {
                  const typeInfo = getAccountTypeInfo(account.type, account.subtype)
                  const lastSync = formatLastSync(account.last_synced_at ?? null)

                  return (
                    <div key={account.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        {/* Account Info */}
                        <div className="flex items-center gap-3 flex-1">
                          <span className="text-2xl">{typeInfo.icon}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <div className="font-medium text-gray-900 truncate">{account.name}</div>
                              <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs whitespace-nowrap">
                                {typeInfo.displayName}
                              </span>
                            </div>
                            {account.official_name && account.official_name !== account.name && (
                              <div className="text-sm text-gray-600 truncate">{account.official_name}</div>
                            )}
                            <div className="text-xs text-gray-500 mt-1">
                              {account.beancount_account}
                            </div>
                          </div>
                        </div>

                        {/* Balance and Status */}
                        <div className="flex items-center gap-6 ml-4">
                          {/* Available Balance (if different from current) */}
                          {account.available_balance !== null &&
                            account.available_balance !== account.current_balance && (
                              <div className="text-right">
                                <div className="text-sm font-medium text-gray-700">
                                  {new Intl.NumberFormat('en-US', {
                                    style: 'currency',
                                    currency: account.currency,
                                  }).format(account.available_balance ?? 0)}
                                </div>
                                <div className="text-xs text-gray-500">Available</div>
                              </div>
                            )}

                          {/* Current Balance */}
                          <div className="text-right">
                            <div className="text-xl font-bold text-gray-900">
                              {account.current_balance != null
                                ? new Intl.NumberFormat('en-US', {
                                    style: 'currency',
                                    currency: account.currency ?? 'USD',
                                  }).format(account.current_balance)
                                : 'N/A'}
                            </div>
                            <div className="text-xs text-gray-500">Current</div>
                          </div>

                          {/* Last Sync */}
                          <div className="text-right min-w-[120px]">
                            <div
                              className={`text-xs ${
                                account.last_synced_at ? 'text-gray-500' : 'text-yellow-600'
                              }`}
                            >
                              {lastSync}
                            </div>
                            {account.needs_reconnection && (
                              <div className="text-xs text-red-600 font-medium mt-1">
                                Needs reconnection
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
