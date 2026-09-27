import HtmlPageViewService from '@jadawel/modules/arabase/views/services/htmlPageView'
import ViewService from '@jadawel/modules/database/services/view'

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
  // Keyed by field ID, as every other view type's store holds them. Core reads
  // them through `getAllFieldOptions` (the share popup's field warnings, for
  // one), so a missing getter crashes that popup.
  fieldOptions: {},
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
  SET_FIELD_OPTIONS(state, fieldOptions) {
    state.fieldOptions = fieldOptions
  },
  RESET(current) {
    Object.assign(current, state())
  },
}

export const actions = {
  /**
   * `fieldOptions` also loads the view's field options. The view type asks for
   * them when the page is opened or refreshed, not on every realtime row event.
   * A public visitor never needs them: the public info already leaves out the
   * hidden fields.
   */
  async fetch({ commit, rootGetters }, { view, fieldOptions = false }) {
    const isPublic = rootGetters['page/view/public/getIsPublic']
    commit('SET_LOADING', true)

    try {
      const [{ data }, options] = await Promise.all([
        HtmlPageViewService(this.$client).fetchRows({
          viewId: view.id,
          publicUrl: isPublic,
          publicAuthToken: isPublic
            ? rootGetters['page/view/public/getAuthToken']
            : null,
        }),
        fieldOptions && !isPublic
          ? ViewService(this.$client).fetchFieldOptions(view.id)
          : null,
      ])

      if (options) {
        commit('SET_FIELD_OPTIONS', options.data.field_options)
      }

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
  getAllFieldOptions(state) {
    return state.fieldOptions
  },
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters,
}
