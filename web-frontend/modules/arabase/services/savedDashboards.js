/**
 * The "My dashboards" page (لوحاتي): `/arabase/my-dashboards/`.
 * docs/MY_DASHBOARDS.md.
 */
export default (client) => {
  return {
    list() {
      return client.get('/arabase/my-dashboards/')
    },
    listAvailable() {
      return client.get('/arabase/my-dashboards/available/')
    },
    addFromWorkspace(dashboardId) {
      return client.post('/arabase/my-dashboards/workspace/', {
        dashboard_id: dashboardId,
      })
    },
    addLink(url, password = '') {
      return client.post('/arabase/my-dashboards/link/', { url, password })
    },
    enterPassword(savedDashboardId, password) {
      return client.post(
        `/arabase/my-dashboards/${savedDashboardId}/password/`,
        { password }
      )
    },
    remove(savedDashboardId) {
      return client.delete(`/arabase/my-dashboards/${savedDashboardId}/`)
    },
    order(savedDashboardIds) {
      return client.post('/arabase/my-dashboards/order/', {
        saved_dashboard_ids: savedDashboardIds,
      })
    },
    fetchContent(savedDashboardId) {
      return client.get(`/arabase/my-dashboards/${savedDashboardId}/content/`)
    },
    dispatchDataSource(savedDashboardId, dataSourceId) {
      return client.post(
        `/arabase/my-dashboards/${savedDashboardId}/dispatch/${dataSourceId}/`
      )
    },
  }
}
