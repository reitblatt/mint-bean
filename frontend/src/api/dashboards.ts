import { apiClient } from './client'
import type {
  DashboardTab,
  DashboardTabCreate,
  DashboardTabUpdate,
  DashboardTabWithWidgets,
  DashboardWidget,
  DashboardWidgetCreate,
  DashboardWidgetUpdate,
} from './types'

export const dashboardsApi = {
  // Tab endpoints
  listTabs: async (): Promise<DashboardTab[]> => {
    const response = await apiClient.get<DashboardTab[]>('/dashboards')
    return response.data
  },

  getTab: async (tabId: number): Promise<DashboardTabWithWidgets> => {
    const response = await apiClient.get<DashboardTabWithWidgets>(`/dashboards/${tabId}`)
    return response.data
  },

  createTab: async (data: DashboardTabCreate): Promise<DashboardTab> => {
    const response = await apiClient.post<DashboardTab>('/dashboards', data)
    return response.data
  },

  updateTab: async (tabId: number, data: DashboardTabUpdate): Promise<DashboardTab> => {
    const response = await apiClient.patch<DashboardTab>(`/dashboards/${tabId}`, data)
    return response.data
  },

  deleteTab: async (tabId: number): Promise<void> => {
    await apiClient.delete(`/dashboards/${tabId}`)
  },

  // Widget endpoints
  createWidget: async (tabId: number, data: DashboardWidgetCreate): Promise<DashboardWidget> => {
    const response = await apiClient.post<DashboardWidget>(`/dashboards/${tabId}/widgets`, data)
    return response.data
  },

  updateWidget: async (
    tabId: number,
    widgetId: number,
    data: DashboardWidgetUpdate,
  ): Promise<DashboardWidget> => {
    const response = await apiClient.patch<DashboardWidget>(
      `/dashboards/${tabId}/widgets/${widgetId}`,
      data,
    )
    return response.data
  },

  deleteWidget: async (tabId: number, widgetId: number): Promise<void> => {
    await apiClient.delete(`/dashboards/${tabId}/widgets/${widgetId}`)
  },
}
