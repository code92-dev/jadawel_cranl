import HtmlPageViewService from '@jadawel/modules/arabase/views/services/htmlPageView'

/**
 * The page view's row feed.
 *
 * Small on purpose: the page renders itself inside a sandboxed iframe, so the
 * store holds the data and nothing about presentation. It exists at all —
 * rather than the component fetching for itself — because `ViewType.refresh()`
 * is called by the table header (filter changed, sort changed, search) with no
 * handle on the component, and a store action is how the rest of the view types
 * bridge that gap.
 */
export const state = () => ({
  loading: false,
  loaded: false,
  rows: [],
  count: 0,
  rowLimit: 0,
  truncated: false,
})

export const mutations = {
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_FEED(state, { rows, count, rowLimit, truncated }) {
    state.rows = rows
    state.count = count
    state.rowLimit = rowLimit
    state.truncated = truncated
    state.loaded = true
  },
  RESET(current) {
    Object.assign(current, state())
  },
}

export const actions = {
  async fetch({ commit, rootGetters }, { view }) {
    const isPublic = rootGetters['page/view/public/getIsPublic']
    commit('SET_LOADING', true)

    try {
      const { data } = await HtmlPageViewService(this.$client).fetchRows({
        viewId: view.id,
        publicUrl: isPublic,
        publicAuthToken: isPublic
          ? rootGetters['page/view/public/getAuthToken']
          : null,
      })

      commit('SET_FEED', {
        rows: data.results,
        count: data.count,
        rowLimit: data.row_limit,
        truncated: data.truncated,
      })
    } finally {
      commit('SET_LOADING', false)
    }
  },
  reset({ commit }) {
    commit('RESET')
  },
}

export const getters = {
  getLoading(state) {
    return state.loading
  },
  getLoaded(state) {
    return state.loaded
  },
  getRows(state) {
    return state.rows
  },
  getCount(state) {
    return state.count
  },
  getRowLimit(state) {
    return state.rowLimit
  },
  getTruncated(state) {
    return state.truncated
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters,
}
