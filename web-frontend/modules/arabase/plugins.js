import { JadawelPlugin } from '@jadawel/modules/core/plugins'
import ShareDashboardLink from '@jadawel/modules/arabase/dashboard/components/ShareDashboardLink'
import SanadSidebarItem from '@jadawel/modules/arabase/sanad/components/SanadSidebarItem'
import SanadPanel from '@jadawel/modules/arabase/sanad/components/SanadPanel'

/**
 * Fork-level UI that core modules render through their plugin hooks. Using the
 * hook keeps the dependency pointing the right way: the dashboard module never
 * imports anything from `arabase`.
 */
export class ArabasePlugin extends JadawelPlugin {
  static getType() {
    return 'arabase'
  }

  getAdditionalDashboardHeaderComponents(dashboard) {
    // The endpoints behind it all require `application.update`; rendering the
    // menu for a viewer would only produce a permission error.
    if (
      !this.app.$hasPermission(
        'application.update',
        dashboard,
        dashboard.workspace.id
      )
    ) {
      return []
    }
    return [ShareDashboardLink]
  }

  /**
   * Sanad (سند), the AI assistant, is limited to instance staff while it is
   * introduced; the API enforces the same rule. It lives in core's right
   * sidebar, the slot upstream reserved for its assistant.
   */
  getSidebarWorkspaceComponents(workspace) {
    return this.app.$store.getters['auth/isStaff'] ? [SanadSidebarItem] : []
  }

  getRightSidebarWorkspaceComponents(workspace) {
    return this.app.$store.getters['auth/isStaff'] ? [SanadPanel] : []
  }
}
