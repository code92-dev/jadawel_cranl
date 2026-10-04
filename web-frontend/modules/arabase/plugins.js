import { JadawelPlugin } from '@jadawel/modules/core/plugins'
import ShareDashboardLink from '@jadawel/modules/arabase/dashboard/components/ShareDashboardLink'
import SanadUtilityItem from '@jadawel/modules/arabase/sanad/components/SanadUtilityItem'
import AdminGenerativeAISettings from '@jadawel/modules/arabase/generativeAI/AdminGenerativeAISettings'
import AdminFeatureAccessSettings from '@jadawel/modules/arabase/featureAccess/AdminFeatureAccessSettings'
import { hasFeature } from '@jadawel/modules/arabase/featureAccess/featureAccess'
import SanadPanel from '@jadawel/modules/arabase/sanad/components/SanadPanel'
import AddToMyDashboards from '@jadawel/modules/arabase/savedDashboards/components/AddToMyDashboards'
import MyDashboardsMenuItem from '@jadawel/modules/arabase/savedDashboards/components/MyDashboardsMenuItem'
import MembersSidebarItem from '@jadawel/modules/arabase/components/MembersSidebarItem'

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
    // Any member who can open the dashboard may pin it to their own page; a
    // template preview is no workspace of theirs. The sharing endpoints all
    // require `application.update`; rendering that menu for a viewer would
    // only produce a permission error.
    const isMember = Boolean(
      this.app.$store.getters['workspace/get'](dashboard.workspace.id)
    )
    const canShare = this.app.$hasPermission(
      'application.update',
      dashboard,
      dashboard.workspace.id
    )
    return [
      ...(isMember ? [AddToMyDashboards] : []),
      ...(canShare ? [ShareDashboardLink] : []),
    ]
  }

  /** The members of every workspace, in the workspaces sidebar. */
  getSidebarAllWorkspacesComponents() {
    return [MembersSidebarItem]
  }

  /** "My dashboards" (لوحاتي), directly above "My settings". */
  getUserContextComponentsBeforeSettings() {
    return [MyDashboardsMenuItem]
  }

  /**
   * Sanad (سند), the AI assistant, is for staff and whoever an administrator
   * opens it to (featureAccess); the API enforces the same rule. It opens from
   * the workspace tools window and lives in core's right sidebar, the slot
   * upstream reserved for its assistant.
   */
  getWorkspaceUtilityComponents(workspace) {
    return hasFeature(this.app.$store, 'sanad') ? [SanadUtilityItem] : []
  }

  getRightSidebarWorkspaceComponents(workspace) {
    return hasFeature(this.app.$store, 'sanad') ? [SanadPanel] : []
  }

  /**
   * Who may use automations, applications and Sanad (arabase.feature_access),
   * then AI provider keys (arabase.generative_ai), both managed by
   * administrators on the admin settings page. The page is already staff-only.
   */
  getSettingsPageComponents() {
    return [AdminFeatureAccessSettings, AdminGenerativeAISettings]
  }
}
