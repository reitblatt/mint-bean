import type { DashboardWidget, WidgetConfig } from '@/api/types'
import BarChartWidget from './BarChartWidget'
import LineChartWidget from './LineChartWidget'
import PieChartWidget from './PieChartWidget'
import SummaryCardWidget from './SummaryCardWidget'
import TransactionTableWidget from './TransactionTableWidget'

interface WidgetRendererProps {
  widget: DashboardWidget
  startDate?: string
  endDate?: string
}

export default function WidgetRenderer({ widget, startDate, endDate }: WidgetRendererProps) {
  // Parse widget config
  let config: WidgetConfig = {}
  if (widget.config) {
    try {
      config = JSON.parse(widget.config)
    } catch (error) {
      console.error('Failed to parse widget config:', error)
    }
  }

  // Render appropriate widget based on type
  switch (widget.widget_type) {
    case 'summary_card':
      return (
        <SummaryCardWidget
          title={widget.title}
          config={config}
          startDate={startDate}
          endDate={endDate}
        />
      )

    case 'line_chart':
      return (
        <LineChartWidget
          title={widget.title}
          config={config}
          startDate={startDate}
          endDate={endDate}
        />
      )

    case 'bar_chart':
      return (
        <BarChartWidget
          title={widget.title}
          config={config}
          startDate={startDate}
          endDate={endDate}
        />
      )

    case 'pie_chart':
      return (
        <PieChartWidget
          title={widget.title}
          config={config}
          startDate={startDate}
          endDate={endDate}
        />
      )

    case 'table':
      return (
        <TransactionTableWidget
          title={widget.title}
          config={config}
          startDate={startDate}
          endDate={endDate}
        />
      )

    default:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-900 mb-2">{widget.title}</h3>
          <p className="text-sm text-gray-500">Unknown widget type: {widget.widget_type}</p>
        </div>
      )
  }
}
