import { ViewType } from '@jadawel/modules/database/viewTypes'

import HtmlPageView from '@jadawel/modules/arabase/views/components/HtmlPageView'
import HtmlPageViewHeader from '@jadawel/modules/arabase/views/components/HtmlPageViewHeader'

/**
 * A view whose body is an HTML document, authored by an AI over MCP.
 *
 * Shares through the same machinery as a form: `canShare()` is all it takes,
 * because the slug, the public flag and the password hash live on the base
 * `View` model and `ShareViewLink` is written against the view type's
 * capabilities rather than against a list of known types.
 */
export class HtmlPageViewType extends ViewType {
  static getType() {
    return 'html_page'
  }

  getIconClass() {
    return 'iconoir-page'
  }

  getColorClass() {
    return 'color-success'
  }

  // Namespaced under the fork's own key rather than added to core's `viewType`
  // object: extending a core module's namespace from here would depend on how
  // i18n merges module messages, and would conflict on every upstream merge.
  getName() {
    const { $i18n: i18n } = this.app
    return i18n.t('htmlPageViewType.name')
  }

  getSharingLinkName() {
    const { $i18n: i18n } = this.app
    return i18n.t('htmlPageViewType.sharingLinkName')
  }

  canFilter() {
    return true
  }

  canSort() {
    return true
  }

  canShare() {
    return true
  }

  canSetDefaultValues() {
    return false
  }

  getComponent() {
    return HtmlPageView
  }

  getHeaderComponent() {
    return HtmlPageViewHeader
  }

  getPublicRoute() {
    return 'arabase-public-page-view'
  }

  async fetch({ store }, database, view, fields, storePrefix = '') {
    await store.dispatch(storePrefix + 'view/html_page/fetch', { view })
  }

  async refresh(context, database, view, fields, storePrefix = '') {
    await this.fetch(context, database, view, fields, storePrefix)
  }

  async afterFieldDeleted(context, field, fieldType, storePrefix = '') {
    // The deleted field's column disappears from the feed, so the page has to
    // be handed a fresh payload rather than keeping rows with a stale key.
    await this._refetchSelected(context, storePrefix)
  }

  async afterFieldUpdated(
    context,
    field,
    oldField,
    fieldType,
    storePrefix = ''
  ) {
    await this._refetchSelected(context, storePrefix)
  }

  /**
   * Called from the `field` store's `forceUpdate`/`forceDelete` actions, which
   * pass the Vuex action context — not a `{ store }` object like the realtime
   * hooks do. Read the root getter/dispatch the same way the grid view type
   * does, otherwise `store` is undefined and `store.getters` throws.
   */
  async _refetchSelected({ dispatch, rootGetters }, storePrefix) {
    const view = rootGetters['view/getSelected']
    if (view?.type === HtmlPageViewType.getType()) {
      await dispatch(
        storePrefix + 'view/html_page/fetch',
        { view },
        { root: true }
      )
    }
  }

  async rowCreated(
    context,
    tableId,
    fields,
    values,
    metadata,
    storePrefix = ''
  ) {
    await this._refetchIfCurrent(context, tableId, storePrefix)
  }

  async rowUpdated(
    context,
    tableId,
    fields,
    row,
    values,
    metadata,
    updatedFieldIds,
    storePrefix = ''
  ) {
    await this._refetchIfCurrent(context, tableId, storePrefix)
  }

  async rowDeleted(context, tableId, fields, row, storePrefix = '') {
    await this._refetchIfCurrent(context, tableId, storePrefix)
  }

  /**
   * Rows arrive as one bounded feed rather than a windowed buffer, so there is
   * no per-row patching to do: refetch and re-post. Only for the view that is
   * actually on screen — a page nobody is looking at costs nothing to leave
   * stale, and it reloads when it is opened.
   */
  async _refetchIfCurrent({ store }, tableId, storePrefix) {
    if (!this.isCurrentView(store, tableId)) {
      return
    }
    const view = store.getters['view/getSelected']
    await store.dispatch(storePrefix + 'view/html_page/fetch', { view })
  }
}
