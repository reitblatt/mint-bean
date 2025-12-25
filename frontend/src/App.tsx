import { Routes, Route, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'
import Login from '@/pages/Login'
import DashboardCustom from '@/pages/DashboardCustom'
import Transactions from '@/pages/Transactions'
import Accounts from '@/pages/Accounts'
import Categories from '@/pages/Categories'
import Rules from '@/pages/Rules'
import Admin from '@/pages/Admin'
import Onboarding from '@/pages/Onboarding'
import { useAuth } from '@/contexts/AuthContext'
import { onboardingApi } from '@/api/onboarding'

function App() {
  const { isAuthenticated, loading } = useAuth()

  // Check if onboarding is needed
  const { data: onboardingStatus, isLoading: onboardingLoading } = useQuery({
    queryKey: ['onboarding-status'],
    queryFn: () => onboardingApi.checkStatus(),
    retry: false,
  })

  if (loading || onboardingLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  // If onboarding is needed, show onboarding page
  if (onboardingStatus?.needs_onboarding) {
    return (
      <Routes>
        <Route path="*" element={<Onboarding />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardCustom />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="accounts" element={<Accounts />} />
        <Route path="categories" element={<Categories />} />
        <Route path="rules" element={<Rules />} />
        <Route path="admin" element={<Admin />} />
      </Route>
    </Routes>
  )
}

export default App
