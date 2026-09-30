import core from '@jadawel/modules/dashboard/store/dashboardApplication'
import SavedDashboardsService from '@jadawel/modules/arabase/services/savedDashboards'

/**
 * A dashboard opened from "My dashboards", registered under `saved/`.
 *
 * The same idea as `public/dashboardApplication`: `DashboardContent` and every
 * widget read `${storePrefix}dashboardApplication/...`, so they render as-is,
 * read-only. Only the two loading actions differ: whatever the dashboard's
 * source (a workspace, a link here, another server), the backend answers in the
 * public link's shape under `/arabase/my-dashboards/<id>/`.
 */
export const state = () => ({
  ...core.state(),
  savedDashboardId: null,
})

export const mutations = {
  ...core.mutations,
  SET_SAVED_DASHBOARD_ID(state, savedDashboardId) {
    state.savedDashboardId = savedDashboardId
  },
}

export const actions = {
  ...core.actions,
  async fetchInitial({ commit, dispatch }, { savedDashboardId }) {
    const { $client, $registry } = this
    commit('RESET')
    commit('SET_SAVED_DASHBOARD_ID', savedDashboardId)

    const { data } =
      await SavedDashboardsService($client).fetchContent(savedDashboardId)

    commit('SET_DASHBOARD_ID', data.dashboard.id)
    // A dashboard from another, newer server can hold a widget type this one
    // does not know; it is left out rather than breaking the whole board.
    data.widgets
      .filter((widget) => $registry.exists('dashboardWidget', widget.type))
      .forEach((widget) => commit('ADD_WIDGET', widget))
    data.data_sources.forEach((dataSource) =>
      commit('ADD_DATA_SOURCE', dataSource)
    )
    await dispatch('setLoading', false)

    await Promise.all(
      data.data_sources.map((dataSource) =>
        dispatch('dispatchDataSource', dataSource.id)
      )
    )
    return data.dashboard
  },
  async dispatchDataSource({ commit, state }, dataSourceId) {
    const { $client } = this
    commit('UPDATE_DATA', { dataSourceId, values: null })
    try {
      const { data } = await SavedDashboardsService($client).dispatchDataSource(
        state.savedDashboardId,
        dataSourceId
      )
      commit('UPDATE_DATA', { dataSourceId, values: data })
    } catch (error) {
      commit('UPDATE_DATA', { dataSourceId, values: { _error: true } })
    }
  },
}

export const getters = {
  ...core.getters,
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
