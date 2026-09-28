<template>
  <div>
    <div v-if="!isLoading">
      <div class="layout__col-2-2 dashboard-app__layout">
        <div
          class="dashboard-app__layout-scrollable"
          :style="{ width: `calc(100% - ${sidebarWidth}px)` }"
        >
          <div
            class="dashboard-app__content dashboard-canvas"
            :class="{
              'dashboard-app__content--small': isInTemplate,
              'dashboard-canvas--editing': isEditMode,
            }"
          >
            <div class="dashboard-canvas__top">
              <DashboardContentHeader
                :dashboard="dashboard"
                :store-prefix="storePrefix"
              />
              <DashboardCanvasToolbar
                :dashboard="dashboard"
                :store-prefix="storePrefix"
                :can-create-widget="canCreateWidget"
                @add-widget="openGallery"
              />
            </div>
            <DashboardEmptyState
              v-if="isEmpty"
              :can-create-widget="canCreateWidget"
              @add-widget="openGallery"
            />
            <WidgetBoard
              v-else
              :dashboard="dashboard"
              :store-prefix="storePrefix"
              :can-create-widget="canCreateWidget"
              @add-widget="openGallery"
            />
            <WidgetGalleryModal
              v-if="canCreateWidget"
              ref="gallery"
              :dashboard="dashboard"
              @select="createWidget($event)"
            />
          </div>
        </div>
        <DashboardSidebar
          v-if="isEditMode"
          :dashboard="dashboard"
          :store-prefix="storePrefix"
          :style="{ width: `${sidebarWidth}px` }"
        />
      </div>
    </div>
  </div>
</template>

<script>
import DashboardSidebar from '@jadawel/modules/dashboard/components/DashboardSidebar'
import DashboardContentHeader from '@jadawel/modules/dashboard/components/DashboardContentHeader'
import WidgetBoard from '@jadawel/modules/dashboard/components/WidgetBoard'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import DashboardCanvasToolbar from '@jadawel/modules/arabase/dashboard/components/DashboardCanvasToolbar'
import DashboardEmptyState from '@jadawel/modules/arabase/dashboard/components/DashboardEmptyState'
import WidgetGalleryModal from '@jadawel/modules/arabase/dashboard/components/WidgetGalleryModal'

export default {
  name: 'DashboardContent',
  components: {
    WidgetBoard,
    DashboardContentHeader,
    DashboardSidebar,
    DashboardCanvasToolbar,
    DashboardEmptyState,
    WidgetGalleryModal,
  },
  props: {
    dashboard: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: false,
      default: '',
    },
  },
  data() {
    return {
      contentHeight: 0,
    }
  },
  computed: {
    sidebarWidth() {
      if (this.isEditMode) {
        return 352
      }
      return 0
    },
    isEditMode() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEditMode`
      ]
    },
    isEmpty() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEmpty`
      ]
    },
    isLoading() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isLoading`
      ]
    },
    isInTemplate() {
      return this.storePrefix === 'template/'
    },
    /**
     * Jadawel fork: a computed rather than core's method, which the template
     * tested for truthiness — always true, so read-only members saw the add
     * button. The public and template dashboards never create widgets.
     */
    canCreateWidget() {
      if (this.storePrefix !== '' || !this.dashboard.workspace?.id) {
        return false
      }
      return this.$hasPermission(
        'dashboard.create_widget',
        this.dashboard,
        this.dashboard.workspace.id
      )
    },
  },
  methods: {
    toggleEditMode() {
      return this.$store.dispatch(
        `${this.storePrefix}dashboardApplication/toggleEditMode`
      )
    },
    enterEditMode() {
      return this.$store.dispatch(
        `${this.storePrefix}dashboardApplication/enterEditMode`
      )
    },
    openGallery() {
      this.$refs.gallery?.show()
    },
    async createWidget(widgetVariation) {
      const widgetType = widgetVariation.type.getType()
      const typeFromRegistry = this.$registry.get('dashboardWidget', widgetType)
      // Jadawel fork: created at the variation's size, so a key number lands
      // as a quarter-width card and a list as a wide one.
      const size = widgetVariation.size || typeFromRegistry.defaultSize || {}
      try {
        await this.$store.dispatch('dashboardApplication/createWidget', {
          dashboard: this.dashboard,
          widget: {
            title: widgetVariation.name || typeFromRegistry.name,
            type: widgetType,
            ...size,
            ...widgetVariation.params,
          },
        })
        this.enterEditMode()
      } catch (error) {
        notifyIf(error, 'dashboard')
      }
    },
  },
}
</script>
