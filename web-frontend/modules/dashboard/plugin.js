import { DashboardSearchType } from '@jadawel/modules/dashboard/searchTypes'
import { searchTypeRegistry } from '@jadawel/modules/core/search/types/registry'
import dashboardApplicationStore from '@jadawel/modules/dashboard/store/dashboardApplication'
import { DashboardApplicationType } from '@jadawel/modules/dashboard/applicationTypes'
import { DashboardLastViewedItemType } from '@jadawel/modules/dashboard/lastViewedItemTypes'
import { SummaryWidgetType } from '@jadawel/modules/dashboard/widgetTypes'

export default defineNuxtPlugin({
  name: 'dashboard',
  dependsOn: ['core', 'store'],
  async setup(nuxtApp) {
    const { $store, $registry } = nuxtApp
    const context = { app: nuxtApp }

    if (!$store.hasModule('dashboardApplication')) {
      $store.registerModuleNuxtSafe(
        'dashboardApplication',
        dashboardApplicationStore
      )
      $store.registerModuleNuxtSafe(
        'template/dashboardApplication',
        dashboardApplicationStore
      )
    }

    $registry.registerNamespace('dashboardWidget')
    $registry.register('application', new DashboardApplicationType(context))
    $registry.register(
      'lastViewedItem',
      new DashboardLastViewedItemType(context)
    )
    $registry.register('dashboardWidget', new SummaryWidgetType(context))

    searchTypeRegistry.register(new DashboardSearchType(context))
  },
})
