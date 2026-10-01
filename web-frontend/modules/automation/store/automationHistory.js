import { useNuxtApp } from '#app'
import AutomationHistoryService from '@jadawel/modules/automation/services/history'

const state = {
  // Holds the value of which workflow history is currently selected
  workflowHistory: {},
  // The id of the fetch whose data `workflowHistory` reflects, so that an
  // older response landing later can be recognised and dropped.
  workflowHistoryRequestId: 0,
  // Incremented for every fetch of the workflow history, see
  // `fetchWorkflowHistory`.
  fetchRequestId: 0,
}

const mutations = {
  INCREMENT_FETCH_REQUEST_ID(state) {
    state.fetchRequestId += 1
  },
  SET_WORKFLOW_HISTORY(state, { data, requestId }) {
    state.workflowHistory = data
    state.workflowHistoryRequestId = requestId
  },
  UPDATE_WORKFLOW_HISTORY_ITEM(state, { id, values, requestId }) {
    state.workflowHistoryRequestId = requestId
    const results = state.workflowHistory?.results
    if (!Array.isArray(results)) return
    const index = results.findIndex((item) => item.id === id)
    if (index !== -1) {
      results[index] = { ...results[index], ...values }
    }
  },
}

const actions = {
  /**
   * Fetches the history page of the given workflow. Fetches are started by the
   * side panel, by the run lifecycle realtime events and after a cancellation
   * request, so several can be in flight at once and their responses can land
   * out of order. A response only replaces the state when it is newer than
   * what the state already reflects; an older one is dropped because it would
   * undo what a newer fetch, or a cancellation, applied in the meantime. The
   * fetched page is returned either way.
   */
  async fetchWorkflowHistory({ state, commit }, { workflowId }) {
    commit('INCREMENT_FETCH_REQUEST_ID')
    const requestId = state.fetchRequestId

    const { data } = await AutomationHistoryService(
      useNuxtApp().$client
    ).getWorkflowHistory(workflowId)

    if (requestId > state.workflowHistoryRequestId) {
      commit('SET_WORKFLOW_HISTORY', { data, requestId })
    }

    return data
  },
  /**
   * Requests the cancellation of a run. The backend answers with the updated
   * record, which is applied right away so the entry shows as cancelling
   * without waiting for a round trip. The state is then marked as newer than
   * every fetch started so far: those may have read the run before the
   * cancellation was recorded and must not bring it back. The refetch that
   * follows starts after this point, so it always reflects the cancellation.
   * It also runs when the backend refuses because the run resolved in the
   * meantime, so the entry shows its terminal state.
   */
  async cancelWorkflowRun(
    { state, commit, dispatch },
    { workflowId, workflowHistoryId }
  ) {
    try {
      const { data } = await AutomationHistoryService(
        useNuxtApp().$client
      ).cancelWorkflowHistory(workflowHistoryId)
      // The cancel endpoint returns the bare record; the plugin data attached
      // by the list endpoint is not part of it and must keep its value.
      const values = { ...data }
      delete values.plugin_data
      commit('INCREMENT_FETCH_REQUEST_ID')
      commit('UPDATE_WORKFLOW_HISTORY_ITEM', {
        id: data.id,
        values,
        requestId: state.fetchRequestId,
      })
    } finally {
      // The refetch is best effort: what the caller reports is the outcome of
      // the request above, which a failed refresh must not replace. The
      // realtime event for the cancellation request refetches anyway.
      await dispatch('fetchWorkflowHistory', { workflowId }).catch(() => {})
    }
  },
}

const getters = {
  getWorkflowHistory: (state) => () => {
    return state.workflowHistory
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
