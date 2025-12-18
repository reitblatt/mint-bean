import { useQuery } from '@tanstack/react-query'
import type { TransactionFilters } from '@/api/types'
import { categoriesApi } from '@/api/categories'
import { accountsApi } from '@/api/accounts'

interface TransactionFiltersProps {
  filters: TransactionFilters
  onFiltersChange: (filters: TransactionFilters) => void
  isOpen: boolean
  onToggle: () => void
}

export default function TransactionFiltersPanel({
  filters,
  onFiltersChange,
  isOpen,
  onToggle,
}: TransactionFiltersProps) {
  // Fetch categories and accounts
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.list(),
  })

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list(),
  })

  const updateFilter = (key: keyof TransactionFilters, value: string | number | undefined) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
      page: 1, // Reset to page 1 when filter changes
    })
  }

  const handleClear = () => {
    onFiltersChange({
      page: 1,
      page_size: filters.page_size || 50,
    })
  }

  // Quick date range presets
  const setDateRange = (range: 'today' | 'week' | 'month' | 'quarter' | 'year' | 'all') => {
    const today = new Date()
    let startDate: Date | null = null

    switch (range) {
      case 'today':
        startDate = new Date(today.setHours(0, 0, 0, 0))
        break
      case 'week':
        startDate = new Date(today.setDate(today.getDate() - 7))
        break
      case 'month':
        startDate = new Date(today.setMonth(today.getMonth() - 1))
        break
      case 'quarter':
        startDate = new Date(today.setMonth(today.getMonth() - 3))
        break
      case 'year':
        startDate = new Date(today.setFullYear(today.getFullYear() - 1))
        break
      case 'all':
        onFiltersChange({
          ...filters,
          start_date: undefined,
          end_date: undefined,
          page: 1,
        })
        return
    }

    if (startDate) {
      onFiltersChange({
        ...filters,
        start_date: startDate.toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        page: 1,
      })
    }
  }

  const activeFilterCount = Object.keys(filters).filter(
    (key) =>
      key !== 'page' &&
      key !== 'page_size' &&
      filters[key as keyof TransactionFilters] !== undefined
  ).length

  return (
    <div className="mb-6">
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-700">
            {isOpen ? '▼' : '▶'} Filters
          </span>
          {activeFilterCount > 0 && (
            <span className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold text-white bg-blue-600 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </div>
        {activeFilterCount > 0 && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleClear()
            }}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear all
          </button>
        )}
      </button>

      {/* Collapsible Filter Panel */}
      {isOpen && (
        <div className="mt-4 p-6 bg-white border border-gray-200 rounded-lg shadow-sm space-y-6">
          {/* Date Range Presets */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quick Date Ranges
            </label>
            <div className="flex flex-wrap gap-2">
              {[
                { label: 'Today', value: 'today' as const },
                { label: 'Last 7 Days', value: 'week' as const },
                { label: 'Last Month', value: 'month' as const },
                { label: 'Last 3 Months', value: 'quarter' as const },
                { label: 'Last Year', value: 'year' as const },
                { label: 'All Time', value: 'all' as const },
              ].map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => setDateRange(preset.value)}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Grid Layout for Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => updateFilter('start_date', e.target.value)}
                className="input w-full"
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
              <input
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => updateFilter('end_date', e.target.value)}
                className="input w-full"
              />
            </div>

            {/* Account Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Account</label>
              <select
                value={filters.account_id || ''}
                onChange={(e) =>
                  updateFilter('account_id', e.target.value ? parseInt(e.target.value) : undefined)
                }
                className="input w-full"
              >
                <option value="">All Accounts</option>
                {accounts?.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={filters.category_id || ''}
                onChange={(e) =>
                  updateFilter('category_id', e.target.value ? parseInt(e.target.value) : undefined)
                }
                className="input w-full"
              >
                <option value="">All Categories</option>
                <optgroup label="Expense Categories">
                  {categories
                    ?.filter((cat) => cat.category_type === 'expense')
                    .map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.display_name}
                      </option>
                    ))}
                </optgroup>
                <optgroup label="Income Categories">
                  {categories
                    ?.filter((cat) => cat.category_type === 'income')
                    .map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.display_name}
                      </option>
                    ))}
                </optgroup>
              </select>
            </div>
          </div>

          {/* Active Filters Summary */}
          {activeFilterCount > 0 && (
            <div className="pt-4 border-t border-gray-200">
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-sm font-medium text-gray-700">Active:</span>
                {filters.start_date && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                    From: {filters.start_date}
                    <button
                      onClick={() => updateFilter('start_date', undefined)}
                      className="hover:text-blue-900 font-bold"
                    >
                      ×
                    </button>
                  </span>
                )}
                {filters.end_date && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                    To: {filters.end_date}
                    <button
                      onClick={() => updateFilter('end_date', undefined)}
                      className="hover:text-blue-900 font-bold"
                    >
                      ×
                    </button>
                  </span>
                )}
                {filters.account_id && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                    Account: {accounts?.find((a) => a.id === filters.account_id)?.name}
                    <button
                      onClick={() => updateFilter('account_id', undefined)}
                      className="hover:text-blue-900 font-bold"
                    >
                      ×
                    </button>
                  </span>
                )}
                {filters.category_id && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                    Category:{' '}
                    {categories?.find((c) => c.id === filters.category_id)?.display_name}
                    <button
                      onClick={() => updateFilter('category_id', undefined)}
                      className="hover:text-blue-900 font-bold"
                    >
                      ×
                    </button>
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
