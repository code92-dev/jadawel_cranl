import { ViewType } from '@jadawel/modules/database/viewTypes'

import KanbanView from '@jadawel/modules/arabase/kanban/components/KanbanView'

/**
 * The id of the stack a row belongs to: the id of its option in the grouping
 * field, or `null` for the stack of rows without a value.
 */
export function stackIdOfRow(row, groupingFieldId) {
  const value = row[`field_${groupingFieldId}`]
  return value && value.id !== undefined ? value.id : null
}

/**
 * The selected view when it is a kanban view of the given table, otherwise
 * `null`: realtime row events for any other view leave the board alone.
 */
function selectedKanbanView(store, tableId) {
  const view = store.getters['view/getSelected']
  if (
    !view ||
    view.table_id !== tableId ||
    view.type !== KanbanViewType.getType()
  ) {
    return null
  }
  return view
}

/**
 * The kanban board view type (#35): one column per option of a single select
 * field. Rows are fetched per stack from the fork's own API, and cards are
 * rendered by the shared `RowCard`, so row colors (decorations) work on
 * kanban cards exactly like on grid rows and gallery cards.
 */
export class KanbanViewType extends ViewType {
  static getType() {
    return 'kanban'
  }

  getIconClass() {
    return 'iconoir-stack'
  }

  getColorClass() {
    return 'color-warning'
  }

  getName() {
    const { $i18n: i18n } = this.app
    return i18n.t('kanbanViewType.name')
  }

  getDescription() {
    const { $i18n: i18n } = this.app
    return i18n.t('kanbanViewType.description')
  }

  canFilter() {
    return true
  }

  canSort() {
    return true
  }

  canShare() {
    return false
  }

  getComponent() {
    return KanbanView
  }

  getHeaderComponent() {
    return null
  }

  refresh(context, database, view, fields, storePrefix = '') {
    const { store } = context
    return store.dispatch(`${storePrefix}view/kanban/fetch`, { view })
  }

  rowCreated(context, tableId, fields, values, metadata, storePrefix) {
    const { store } = context
    const view = selectedKanbanView(store, tableId)
    if (!view) {
      return
    }
    // The row may belong to any stack and shifts the counts; refetching the
    // board is one cheap request and keeps every count honest.
    store.dispatch(`${storePrefix}view/kanban/fetch`, { view })
  }

  async rowUpdated(
    context,
    tableId,
    fields,
    rowBeforeUpdate,
    row,
    metadata,
    updatedFieldIds,
    storePrefix
  ) {
    const { store } = context
    const view = selectedKanbanView(store, tableId)
    if (!view) {
      return
    }
    const groupingFieldId = view.single_select_field
    if (!groupingFieldId) {
      return
    }

    const before = stackIdOfRow(rowBeforeUpdate, groupingFieldId)
    const after = stackIdOfRow(row, groupingFieldId)

    if (before !== after) {
      // The row moved stacks; refetch both so counts and pages are exact.
      await store.dispatch(`${storePrefix}view/kanban/fetchStack`, {
        view,
        stackId: before,
      })
      await store.dispatch(`${storePrefix}view/kanban/fetchStack`, {
        view,
        stackId: after,
      })
      store.dispatch(`${storePrefix}view/kanban/fetch`, { view })
    } else {
      // The row stayed in its stack; replace it in place if it is loaded.
      const stackId = after
      const data =
        store.getters[`${storePrefix}view/kanban/getStackData`](stackId)
      const index = data.rows.findIndex((r) => r.id === row.id)
      if (index !== -1) {
        store.commit(`${storePrefix}view/kanban/SET_STACK_ROWS`, {
          stackId,
          rows: data.rows.map((r) => (r.id === row.id ? row : r)),
          count: data.count,
          append: false,
        })
      }
    }
  }

  rowDeleted(context, tableId, fields, row, storePrefix) {
    const { store } = context
    const view = selectedKanbanView(store, tableId)
    if (!view) {
      return
    }
    const groupingFieldId = view.single_select_field
    if (!groupingFieldId) {
      return
    }
    const stackId = stackIdOfRow(row, groupingFieldId)
    store.commit(`${storePrefix}view/kanban/REMOVE_ROW`, {
      stackId,
      rowId: row.id,
    })
    store.dispatch(`${storePrefix}view/kanban/fetch`, { view })
  }
}
