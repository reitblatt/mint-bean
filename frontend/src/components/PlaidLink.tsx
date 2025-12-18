import { useCallback, useEffect, useState } from 'react'
import { usePlaidLink } from 'react-plaid-link'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { plaidApi } from '@/api/plaid'

interface PlaidLinkProps {
  onSuccess?: () => void
  onExit?: () => void
}

export default function PlaidLink({ onSuccess, onExit }: PlaidLinkProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  // Fetch link token on mount
  useEffect(() => {
    const getLinkToken = async () => {
      try {
        setError(null)
        const response = await plaidApi.createLinkToken()
        setLinkToken(response.link_token)
      } catch (err) {
        console.error('Error creating link token:', err)
        setError('Failed to initialize Plaid Link. Please check your Plaid credentials.')
      }
    }
    getLinkToken()
  }, [])

  // Exchange public token mutation
  const exchangeTokenMutation = useMutation({
    mutationFn: (publicToken: string) => plaidApi.exchangePublicToken(publicToken),
    onSuccess: async (data) => {
      console.log('Successfully linked account:', data.institution_name)

      // Invalidate relevant queries
      await queryClient.invalidateQueries({ queryKey: ['plaid-items'] })
      await queryClient.invalidateQueries({ queryKey: ['accounts'] })

      onSuccess?.()
    },
    onError: (error) => {
      console.error('Error exchanging public token:', error)
      setError('Failed to link account. Please try again.')
    },
  })

  const handleOnSuccess = useCallback(
    (publicToken: string) => {
      console.log('Plaid Link success, exchanging token...')
      exchangeTokenMutation.mutate(publicToken)
    },
    [exchangeTokenMutation]
  )

  const handleOnExit = useCallback(
    (err: unknown) => {
      if (err) {
        const error = err as { error_message?: string }
        console.error('Plaid Link exit with error:', error)
        setError(`Plaid Link error: ${error.error_message || 'Unknown error'}`)
      }
      onExit?.()
    },
    [onExit]
  )

  const config = {
    token: linkToken,
    onSuccess: handleOnSuccess,
    onExit: handleOnExit,
  }

  const { open, ready } = usePlaidLink(config)

  // Handle errors
  if (error) {
    return (
      <div className="text-center">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={() => window.location.reload()}
          className="btn btn-secondary"
        >
          Retry
        </button>
      </div>
    )
  }

  // Show loading state while fetching token
  if (!linkToken) {
    return (
      <button disabled className="btn btn-primary">
        Initializing...
      </button>
    )
  }

  // Show processing state during token exchange
  if (exchangeTokenMutation.isPending) {
    return (
      <button disabled className="btn btn-primary">
        Connecting account...
      </button>
    )
  }

  // Ready to open Plaid Link
  return (
    <button
      onClick={() => open()}
      disabled={!ready}
      className="btn btn-primary"
    >
      {ready ? 'Connect Bank Account' : 'Loading...'}
    </button>
  )
}
