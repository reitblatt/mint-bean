import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, startOfMonth, endOfMonth, subMonths } from 'date-fns'
import { dashboardsApi } from '@/api/dashboards'
import WidgetRenderer from '@/components/widgets/WidgetRenderer'

type TimeRange = 'current-month' | 'last-month' | 'last-3-months'

export default function DashboardCustom() {
  const [selectedTabId, setSelectedTabId] = useState<number | null>(null)
  const [timeRange, setTimeRange] = useState<TimeRange>('current-month')

  // Fetch all tabs
  const { data: tabs, isLoading: tabsLoading } = useQuery({
    queryKey: ['dashboard-tabs'],
    queryFn: () => dashboardsApi.listTabs(),
  })

  // Set default tab once tabs are loaded
  const activeTabId = selectedTabId || tabs?.find((tab) => tab.is_default)?.id || tabs?.[0]?.id

  // Fetch active tab with widgets
  const { data: activeTab, isLoading: tabLoading } = useQuery({
    queryKey: ['dashboard-tab', activeTabId],
    queryFn: () => dashboardsApi.getTab(activeTabId!),
    enabled: !!activeTabId,
  })

  // Calculate date range based on selection
  const getDateRange = () => {
    const today = new Date()
    let start: Date
    let end: Date

    switch (timeRange) {
      case 'current-month':
        start = startOfMonth(today)
        end = endOfMonth(today)
        break
      case 'last-month':
        const lastMonth = subMonths(today, 1)
        start = startOfMonth(lastMonth)
        end = endOfMonth(lastMonth)
        break
      case 'last-3-months':
        start = startOfMonth(subMonths(today, 2))
        end = endOfMonth(today)
        break
    }

    return {
      start_date: format(start, 'yyyy-MM-dd'),
      end_date: format(end, 'yyyy-MM-dd'),
    }
  }

  const { start_date, end_date } = getDateRange()

  if (tabsLoading) {
    return (
      <div className="p-6">
        <div className="h-10 bg-gray-200 rounded w-64 mb-6 animate-pulse" />
        <div className="h-96 bg-gray-200 rounded animate-pulse" />
      </div>
    )
  }

  if (!tabs || tabs.length === 0) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h2 className="text-lg font-medium text-yellow-900 mb-2">No Dashboard Found</h2>
          <p className="text-yellow-700">
            You don't have any dashboard tabs yet. Please contact support.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header with tabs and time range selector */}
      <div className="mb-6 flex items-center justify-between">
        {/* Tab navigation */}
        <div className="flex gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTabId(tab.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                tab.id === activeTabId
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              {tab.icon && <span className="mr-2">{tab.icon}</span>}
              {tab.name}
            </button>
          ))}
        </div>

        {/* Time range selector */}
        <div className="flex gap-2">
          <button
            onClick={() => setTimeRange('current-month')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              timeRange === 'current-month'
                ? 'bg-indigo-100 text-indigo-700'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
            }`}
          >
            Current Month
          </button>
          <button
            onClick={() => setTimeRange('last-month')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              timeRange === 'last-month'
                ? 'bg-indigo-100 text-indigo-700'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
            }`}
          >
            Last Month
          </button>
          <button
            onClick={() => setTimeRange('last-3-months')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              timeRange === 'last-3-months'
                ? 'bg-indigo-100 text-indigo-700'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
            }`}
          >
            Last 3 Months
          </button>
        </div>
      </div>

      {/* Dashboard grid */}
      {tabLoading ? (
        <div className="h-96 bg-gray-200 rounded animate-pulse" />
      ) : activeTab && activeTab.widgets.length > 0 ? (
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: 'repeat(4, 1fr)',
            gridAutoRows: 'minmax(200px, auto)',
          }}
        >
          {activeTab.widgets.map((widget) => (
            <div
              key={widget.id}
              style={{
                gridColumn: `${widget.grid_col} / span ${widget.grid_width}`,
                gridRow: `${widget.grid_row} / span ${widget.grid_height}`,
              }}
            >
              <WidgetRenderer widget={widget} startDate={start_date} endDate={end_date} />
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Widgets</h3>
          <p className="text-gray-600">This dashboard doesn't have any widgets yet.</p>
        </div>
      )}
    </div>
  )
}
