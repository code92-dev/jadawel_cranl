import {
  ChartWidgetType,
  ProgressWidgetType,
  RecordsListWidgetType,
  UpcomingDatesWidgetType,
} from '@jadawel/modules/arabase/dashboard/widgetTypes'
import {
  LocalJadawelGroupedAggregateRowsServiceType,
  LocalJadawelUpcomingRowsServiceType,
} from '@jadawel/modules/arabase/integrations/serviceTypes'
import { BackupAdminType } from '@jadawel/modules/arabase/adminTypes'
import { ArabasePlugin } from '@jadawel/modules/arabase/plugins'
import { ViewerRoleType } from '@jadawel/modules/arabase/roleTypes'
import { ViewerRoleTranslationsPermissionManagerType } from '@jadawel/modules/arabase/permissions'
import { KanbanViewType } from '@jadawel/modules/arabase/kanban/viewType'
import kanbanStore from '@jadawel/modules/arabase/kanban/store'
import publicDashboardApplicationStore from '@jadawel/modules/arabase/dashboard/store/publicDashboardApplication'
import { HtmlPageViewType } from '@jadawel/modules/arabase/views/viewTypes'
import htmlPageViewStore from '@jadawel/modules/arabase/views/store/htmlPageView'
import { McpProtectedEndpointSettingsType } from '@jadawel/modules/arabase/mcp/settingsTypes'
import { BackgroundColorDecoratorType } from '@jadawel/modules/arabase/decorators/backgroundColor'
import { LeftBorderColorDecoratorType } from '@jadawel/modules/arabase/decorators/leftBorderColor'
import { SingleSelectColorValueProviderType } from '@jadawel/modules/arabase/valueProviders/singleSelectColor'
import { ConditionalColorValueProviderType } from '@jadawel/modules/arabase/valueProviders/conditionsColor'

/**
 * Registry registrations for the fork's own types.
 *
 * Separate from ./plugin.js (which only wires up direction/locale) because these
 * depend on namespaces other modules create: `dashboardWidget` is registered by
 * the dashboard plugin, and service types have to exist before a dashboard
 * renders a widget whose data source uses one.
 */
export default defineNuxtPlugin({
  name: 'arabase-registry',
  dependsOn: ['core', 'store', 'dashboard', 'database'],
  setup(nuxtApp) {
    const { $registry, $store } = nuxtApp
    const context = { app: nuxtApp }

    // The page view's row feed, under both prefixes core uses: the plain one
    // for the app, and `page/` for the public share page.
    if (!$store.hasModule('view/html_page')) {
      $store.registerModuleNuxtSafe('view/html_page', htmlPageViewStore)
    }
    if (!$store.hasModule('page/view/html_page')) {
      $store.registerModuleNuxtSafe('page/view/html_page', htmlPageViewStore)
    }

    $registry.register('view', new HtmlPageViewType(context))

    // Read-only twin of `dashboardApplication`, under the `public/` prefix the
    // public dashboard page passes to `DashboardContent` as its store prefix.
    if (!$store.hasModule('public/dashboardApplication')) {
      $store.registerModuleNuxtSafe(
        'public/dashboardApplication',
        publicDashboardApplicationStore
      )
    }

    $registry.register('admin', new BackupAdminType(context))

    $registry.register(
      'service',
      new LocalJadawelGroupedAggregateRowsServiceType(context)
    )
    $registry.register(
      'service',
      new LocalJadawelUpcomingRowsServiceType(context)
    )

    $registry.register('dashboardWidget', new ChartWidgetType(context))
    $registry.register('dashboardWidget', new RecordsListWidgetType(context))
    $registry.register('dashboardWidget', new ProgressWidgetType(context))
    $registry.register('dashboardWidget', new UpcomingDatesWidgetType(context))

    $registry.register('plugin', new ArabasePlugin(context))

    // The OSS kanban board (#35). Its store lives under the same
    // prefixed `view/` namespaces as every other table view type's, so the
    // table page's store-prefix conventions apply unchanged.
    for (const prefix of ['page/', 'template/']) {
      if (!$store.hasModule(`${prefix}view/kanban`)) {
        $store.registerModuleNuxtSafe(`${prefix}view/kanban`, kanbanStore)
      }
    }
    $registry.register('view', new KanbanViewType(context))

    // Workspace VIEWER role (#36): enforced server-side by the additive
    // `viewer_role` permission manager; registered here so the role appears
    // in the invite form and the members table role dropdown. The labels
    // come from the translations manager below: the roles service never
    // calls the role type's getName().
    $registry.register('roles', new ViewerRoleType(context))
    $registry.register(
      'permissionManager',
      new ViewerRoleTranslationsPermissionManagerType(context)
    )

    // Row coloring (#28): decorators fed by single select colors or
    // conditional rules. Core's toolbar menu and row/card rendering pick
    // these up with no core edits.
    $registry.register(
      'viewDecorator',
      new BackgroundColorDecoratorType(context)
    )
    $registry.register(
      'viewDecorator',
      new LeftBorderColorDecoratorType(context)
    )
    $registry.register(
      'decoratorValueProvider',
      new SingleSelectColorValueProviderType(context)
    )
    $registry.register(
      'decoratorValueProvider',
      new ConditionalColorValueProviderType(context)
    )

    // Replace only the settings presentation; the core endpoint card and legacy
    // endpoint APIs remain reusable and upstream-owned.
    $registry.unregister('settings', 'mcp-endpoint')
    $registry.register(
      'settings',
      new McpProtectedEndpointSettingsType(context)
    )

    // Generative AI keys are not configurable per workspace in Jadawel: the
    // provider credentials are an instance-level concern (env vars) or an
    // integration-level one (the AI integration's own `ai_settings`). Dropping
    // the tab here keeps the core component untouched while removing the entry
    // point; the matching API route is removed in the backend (see PATCHES.md).
    $registry.unregister('workspaceSettings', 'generative-ai')
  },
})
