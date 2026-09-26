import KanbanService from '@jadawel/modules/arabase/kanban/service'
import { stackIdOfRow } from '@jadawel/modules/arabase/kanban/viewType'

/**
 * The kanban board's state: the stacks (one per select option of the view's
 * grouping field, plus the stack of rows without a value) and the rows
 * fetched per stack. Rows are paged per stack with a `hasNextPage` flag, so
 * a board with many rows only loads what is visible.
 *
 * The store exists — rather than the component fetching for itself — for the
 * same reason as every other view type: `ViewType.refresh()` is called by
 * the table header (filter changed, sort changed) with no handle on the
 * component.
 */

const PAGE_SIZE = 40

export const state = () => ({
  loading: false,
  stacks: [],
  // `fieldId -> { hidden, order }`, populated from the board response.
  fieldOptions: {},
  // `stackId -> { rows, count, hasNextPage, nextOffset, loading }`
  stacksData: {},
})

export const mutations = {
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_FIELD_OPTIONS(state, fieldOptions) {
    state.fieldOptions = fieldOptions || {}
  },
  SET_STACKS(state, stacks) {
    state.stacks = stacks
    const stacksData = {}
    for (const stack of stacks) {
      stacksData[stack.id] = state.stacksData[stack.id] || {
        rows: [],
        count: stack.count,
        hasNextPage: false,
        nextOffset: 0,
        loading: false,
      }
      stacksData[stack.id].count = stack.count
    }
    state.stacksData = stacksData
  },
  SET_STACK_ROWS(state, { stackId, rows, count, append }) {
    const data = state.stacksData[stackId] || {
      rows: [],
      count,
      hasNextPage: false,
      nextOffset: 0,
      loading: false,
    }
    data.rows = append ? data.rows.concat(rows) : rows
    data.count = count
    data.nextOffset = data.rows.length
    data.hasNextPage = data.rows.length < count
    state.stacksData = { ...state.stacksData, [stackId]: data }
  },
  SET_STACK_LOADING(state, { stackId, value }) {
    const data = state.stacksData[stackId]
    if (data) {
      state.stacksData = {
        ...state.stacksData,
        [stackId]: { ...data, loading: value },
      }
    }
  },
  MOVE_ROW(state, { fromStackId, toStackId, row, beforeId }) {
    const fromData = state.stacksData[fromStackId]
    const toData = state.stacksData[toStackId]
    if (fromData) {
      const rows = fromData.rows.filter((r) => r.id !== row.id)
      state.stacksData = {
        ...state.stacksData,
        [fromStackId]: {
          ...fromData,
          rows,
          nextOffset: Math.max(0, fromData.nextOffset - 1),
          count: Math.max(0, fromData.count - 1),
        },
      }
    }
    if (toData && !toData.rows.some((r) => r.id === row.id)) {
      const rows = [...toData.rows]
      const index = beforeId
        ? rows.findIndex((r) => r.id === beforeId)
        : rows.length
      rows.splice(index === -1 ? rows.length : index, 0, row)
      state.stacksData = {
        ...state.stacksData,
        [toStackId]: {
          ...toData,
          rows,
          nextOffset: toData.nextOffset + 1,
          count: toData.count + 1,
        },
      }
    }
  },
  REMOVE_ROW(state, { stackId, rowId }) {
    const data = state.stacksData[stackId]
    if (data) {
      state.stacksData = {
        ...state.stacksData,
        [stackId]: {
          ...data,
          rows: data.rows.filter((r) => r.id !== rowId),
          count: Math.max(0, data.count - 1),
        },
      }
    }
  },
}

export const getters = {
  getStacks(state) {
    return state.stacks
  },
  getStackData: (state) => (stackId) =>
    state.stacksData[stackId] || {
      rows: [],
      count: 0,
      hasNextPage: false,
      nextOffset: 0,
      loading: false,
    },
  getAllFieldOptions(state) {
    return state.fieldOptions
  },
}

export const actions = {
  /**
   * Fetches the board (stacks with counts) and the first page of every
   * stack, in parallel.
   */
  async fetch({ commit, dispatch }, { view, search = '' }) {
    commit('SET_LOADING', true)
    try {
      const { data } = await KanbanService(this.$client).fetchBoard({
        viewId: view.id,
        search,
      })
      commit('SET_FIELD_OPTIONS', data.field_options)
      commit('SET_STACKS', data.stacks)
      await Promise.all(
        data.stacks.map((stack) =>
          dispatch('fetchStack', { view, stackId: stack.id, search })
        )
      )
    } finally {
      commit('SET_LOADING', false)
    }
  },
  async fetchStack(
    { commit, getters },
    { view, stackId, search = '', append = false }
  ) {
    const stackIdKey = stackId === null ? 'null' : stackId
    // `getters` here are the module-local ones, regardless of the prefix the
    // module is registered under.
    const current = getters.getStackData(stackId)
    commit('SET_STACK_LOADING', { stackId, value: true })
    try {
      const { data } = await KanbanService(this.$client).fetchStackRows({
        viewId: view.id,
        stackId: stackIdKey,
        offset: append ? current.nextOffset : 0,
        limit: PAGE_SIZE,
        search,
      })
      commit('SET_STACK_ROWS', {
        stackId,
        rows: data.results,
        count: data.count,
        append,
      })
    } finally {
      commit('SET_STACK_LOADING', { stackId, value: false })
    }
  },
  /**
   * Moves a row to another stack by updating the grouping field's value
   * through the standard row update endpoint. The board state is updated
   * optimistically and reverts if the request fails.
   */
  async moveRow({ commit }, { table, view, fields, row, toStackId, toStack }) {
    const groupingFieldId = view.single_select_field
    const groupingField = fields.find((field) => field.id === groupingFieldId)
    if (!groupingField) {
      return
    }

    const fromStackId = stackIdOfRow(row, groupingFieldId)

    // Build the full option object for the optimistic update so badges and
    // colors render correctly before the refetch lands; the component passes
    // the target stack, which carries the option's title and color.
    const updatedRow = {
      ...row,
      [`field_${groupingFieldId}`]:
        toStackId === null
          ? null
          : {
              id: toStackId,
              value: toStack ? toStack.title : undefined,
              color: toStack ? toStack.color : undefined,
            },
    }

    commit('MOVE_ROW', { fromStackId, toStackId, row: updatedRow })

    try {
      await this.$client.patch(`/database/rows/table/${table.id}/${row.id}/`, {
        [`field_${groupingFieldId}`]: toStackId,
      })
    } catch (error) {
      // Revert the optimistic move.
      commit('MOVE_ROW', {
        fromStackId: toStackId,
        toStackId: fromStackId,
        row: { ...row },
      })
      throw error
    }
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
