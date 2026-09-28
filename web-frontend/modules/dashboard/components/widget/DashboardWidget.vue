<template>
  <div
    class="dashboard-widget"
    :class="{
      'dashboard-widget--selected': isSelected,
      'dashboard-widget--selectable': isSelectable,
      'dashboard-widget--editing': isEditMode,
      'dashboard-widget--bare': isBare,
      'dashboard-widget--resizing': previewSize !== null,
    }"
    :style="gridStyle"
    @click="selectWidgetIfAllowed(widget.id)"
  >
    <div v-if="isSelected && isEditMode" class="dashboard-widget__name">
      {{ widgetType.name }}
    </div>
    <component
      :is="widgetComponent(widget.type)"
      :dashboard="dashboard"
      :widget="widget"
      :store-prefix="storePrefix"
      :loading="isLoading"
      :edit-mode="isEditMode"
    />
    <WidgetEditChrome
      v-if="isEditMode && !isTemporary"
      :dashboard="dashboard"
      :widget="widget"
      :store-prefix="storePrefix"
      :can-drag="canArrange"
      :can-resize="canArrange"
      @preview="previewSize = $event"
    />
  </div>
</template>

<script>
import WidgetEditChrome from '@jadawel/modules/arabase/dashboard/components/widget/WidgetEditChrome'
import {
  DEFAULT_MIN_SIZE,
  widgetSize,
} from '@jadawel/modules/arabase/dashboard/layout'

export default {
  name: 'DashboardWidget',
  components: { WidgetEditChrome },
  props: {
    dashboard: {
      type: Object,
      required: true,
    },
    widget: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: false,
      default: '',
    },
    /**
     * Jadawel fork (grid board): false on a narrow, single-column board, where
     * moving and resizing are off.
     */
    canArrange: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      // Jadawel fork (grid board): the size a corner drag has reached, shown
      // until the drag ends.
      previewSize: null,
    }
  },
  computed: {
    isSelected() {
      return this.selectedWidgetId === this.widget.id && this.isEditMode
    },
    isSelectable() {
      return this.selectedWidgetId !== this.widget.id && this.isEditMode
    },
    widgetType() {
      return this.$registry.get('dashboardWidget', this.widget.type)
    },
    selectedWidgetId() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/getSelectedWidgetId`
      ]
    },
    isEditMode() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEditMode`
      ]
    },
    /** A widget still being created carries a temporary, client-side id. */
    isTemporary() {
      return this.widget.dashboard_id === undefined
    },
    isBare() {
      return this.widgetType.isBare
        ? this.widgetType.isBare(this.widget)
        : false
    },
    gridStyle() {
      // Jadawel fork (grid board): the widget's spans on the 12-column board.
      const size =
        this.previewSize ||
        widgetSize(this.widget, this.widgetType.minSize || DEFAULT_MIN_SIZE)
      return {
        gridColumn: `span ${size.width}`,
        gridRow: `span ${size.height}`,
      }
    },
    isLoading() {
      return this.widgetType.isLoading(
        this.widget,
        this.$store.getters[`${this.storePrefix}dashboardApplication/getData`]
      )
    },
  },
  methods: {
    widgetComponent(type) {
      const widgetType = this.$registry.get('dashboardWidget', type)
      return widgetType.component
    },
    selectWidgetIfAllowed(widgetId) {
      if (this.canSelectWidget()) {
        this.$store.dispatch(
          `${this.storePrefix}dashboardApplication/selectWidget`,
          widgetId
        )
      }
    },
    canSelectWidget() {
      return this.$hasPermission(
        'dashboard.widget.update',
        this.widget,
        this.dashboard.workspace.id
      )
    },
  },
}
</script>
