import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { plaidApi } from '@/api/plaid'
import PlaidLink from './PlaidLink'
import { DisconnectAccountModal } from './DisconnectAccountModal'

export default function PlaidAccountsManager() {
  const queryClient = useQueryClient()
  const [syncingItemId, setSyncingItemId] = useState<number | null>(null)
  const [showLinkButton, setShowLinkButton] = useState(false)
  const [disconnectModal, setDisconnectModal] = useState<{
    itemId: number
    institutionName: string
  } | null>(null)

  // Fetch connected Plaid items
  const { data: items, isLoading } = useQuery({
    queryKey: ['plaid-items'],
    queryFn: () => plaidApi.listItems(),
  })

  // Sync transactions mutation
  const syncMutation = useMutation({
    mutationFn: (itemId: number) => plaidApi.syncTransactions(itemId),
    onSuccess: (data, itemId) => {
      console.log(`Synced ${data.added} new transactions`)
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      setSyncingItemId(null)
    },
    onError: (error) => {
      console.error('Sync error:', error)
      setSyncingItemId(null)
    },
  })

  // Delete item mutation
  const deleteMutation = useMutation({
    mutationFn: (itemId: number) => plaidApi.deleteItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plaid-items'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  const handleSync = (itemId: number) => {
    setSyncingItemId(itemId)
    syncMutation.mutate(itemId)
  }

  const handleDelete = (itemId: number, institutionName: string | null) => {
    setDisconnectModal({
      itemId,
      institutionName: institutionName || 'this account',
    })
  }

  const handleConfirmDisconnect = () => {
    if (disconnectModal) {
      deleteMutation.mutate(disconnectModal.itemId)
      setDisconnectModal(null)
    }
  }

  const handleLinkSuccess = () => {
    setShowLinkButton(false)
    // Items will be refetched automatically via query invalidation
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Connected Accounts</h2>
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900">Connected Accounts</h2>
        {!showLinkButton && (
          <button
            onClick={() => setShowLinkButton(true)}
            className="btn btn-primary"
          >
            + Add Account
          </button>
        )}
      </div>

      {showLinkButton && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-700 mb-3">
            Connect your bank account securely through Plaid
          </p>
          <div className="flex gap-3">
            <PlaidLink
              onSuccess={handleLinkSuccess}
              onExit={() => setShowLinkButton(false)}
            />
            <button
              onClick={() => setShowLinkButton(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {!items || items.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-4">No bank accounts connected yet</div>
          {!showLinkButton && (
            <p className="text-sm text-gray-600">
              Click "Add Account" to connect your first bank account
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {item.institution_name || 'Unknown Bank'}
                    </h3>
                    {item.is_active ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                    {item.needs_update && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Needs Update
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Last synced: {item.last_synced_at
                      ? new Date(item.last_synced_at).toLocaleString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: 'numeric',
                          minute: '2-digit',
                          hour12: true,
                          timeZoneName: 'short'
                        })
                      : 'Never'}
                  </p>
                  {item.error_code && (
                    <p className="text-sm text-red-600 mt-1">
                      Error: {item.error_code}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleSync(item.id)}
                    disabled={syncingItemId === item.id || syncMutation.isPending}
                    className="btn btn-secondary text-sm"
                  >
                    {syncingItemId === item.id ? 'Syncing...' : 'Sync Now'}
                  </button>
                  <button
                    onClick={() => handleDelete(item.id, item.institution_name)}
                    disabled={deleteMutation.isPending}
                    className="btn btn-secondary text-sm text-red-600 hover:bg-red-50"
                  >
                    Disconnect
                  </button>
                </div>
              </div>

              {syncMutation.isSuccess && syncingItemId === item.id && (
                <div className="mt-3 p-3 bg-green-50 rounded text-sm text-green-800">
                  Successfully synced! Added {syncMutation.data?.added || 0} new transactions
                </div>
              )}

              {syncMutation.isError && syncingItemId === item.id && (
                <div className="mt-3 p-3 bg-red-50 rounded text-sm text-red-800">
                  Failed to sync transactions. Please try again.
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Disconnect confirmation modal */}
      {disconnectModal && (
        <DisconnectAccountModal
          isOpen={true}
          plaidItemId={disconnectModal.itemId}
          institutionName={disconnectModal.institutionName}
          onConfirm={handleConfirmDisconnect}
          onCancel={() => setDisconnectModal(null)}
        />
      )}
    </div>
  )
}
