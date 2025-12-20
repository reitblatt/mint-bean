import { apiClient } from './client'

export interface OnboardingStatus {
  needs_onboarding: boolean
}

export interface OnboardingRequest {
  admin_email: string
  admin_password: string
  plaid_client_id: string
  plaid_secret: string
  plaid_environment: 'sandbox' | 'development' | 'production'
}

export interface OnboardingResponse {
  status: string
  message: string
  admin_user_id: number
  admin_email: string
}

export const onboardingApi = {
  checkStatus: async (): Promise<OnboardingStatus> => {
    const response = await apiClient.get<OnboardingStatus>('/onboarding/status')
    return response.data
  },

  complete: async (data: OnboardingRequest): Promise<OnboardingResponse> => {
    const response = await apiClient.post<OnboardingResponse>('/onboarding/complete', data)
    return response.data
  },
}
