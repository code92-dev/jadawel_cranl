import { JadawelPlugin } from '@jadawel/modules/core/plugins'
import ShareDashboardLink from '@jadawel/modules/arabase/dashboard/components/ShareDashboardLink'
import SanadUtilityItem from '@jadawel/modules/arabase/sanad/components/SanadUtilityItem'
import AdminGenerativeAISettings from '@jadawel/modules/arabase/generativeAI/AdminGenerativeAISettings'
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
   * introduced; the API enforces the same rule. It opens from the workspace
   * tools window and lives in core's right sidebar, the slot upstream reserved
   * for its assistant.
   */
  getWorkspaceUtilityComponents(workspace) {
    return this.app.$store.getters['auth/isStaff'] ? [SanadUtilityItem] : []
  }

  getRightSidebarWorkspaceComponents(workspace) {
    return this.app.$store.getters['auth/isStaff'] ? [SanadPanel] : []
  }

  /**
   * AI provider keys, managed by administrators on the admin settings page
   * (arabase.generative_ai). The page is already staff-only.
   */
  getSettingsPageComponents() {
    return [AdminGenerativeAISettings]
  }
}
