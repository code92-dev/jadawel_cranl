import core from '@jadawel/modules/dashboard/store/dashboardApplication'
import DashboardShareService from '@jadawel/modules/arabase/services/dashboardShare'

/**
 * The dashboard store as an anonymous visitor sees it.
 *
 * Registered under the `public/` prefix so `DashboardContent` and every widget
 * component can be reused verbatim — they read
 * `${storePrefix}dashboardApplication/...`. Only the two actions that talk to
 * an authenticated endpoint are replaced: everything reachable without a login
 * goes through `/arabase/public/dashboard/<slug>/`.
 *
 * The editing actions inherited from core stay in place but are unreachable:
 * `editMode` can never become true here, and the components that would trigger
 * them are gated behind `dashboard.widget.update`, which an anonymous visitor
 * never has.
 */
export const state = () => ({
  ...core.state(),
  slug: null,
  authToken: null,
})

export const mutations = {
  ...core.mutations,
  SET_PUBLIC_SOURCE(state, { slug, authToken }) {
    state.slug = slug
    state.authToken = authToken
  },
}

export const actions = {
  ...core.actions,
  /**
   * One request returns the dashboard, its widgets and its data sources, then
   * every data source is dispatched. The authenticated store needs three calls
   * (widgets, data sources, integrations); a visitor has no integrations to
   * read and no reason to pay for the extra round trips.
   */
  async fetchInitial({ commit, dispatch }, { slug, authToken = null }) {
    const { $client } = this
    commit('RESET')
    commit('SET_PUBLIC_SOURCE', { slug, authToken })

    const { data } = await DashboardShareService($client).fetchPublicInfo(
      slug,
      authToken
    )

    commit('SET_DASHBOARD_ID', data.dashboard.id)
    data.widgets.forEach((widget) => commit('ADD_WIDGET', widget))
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
      const { data } = await DashboardShareService(
        $client
      ).dispatchPublicDataSource(state.slug, dataSourceId, state.authToken)
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
