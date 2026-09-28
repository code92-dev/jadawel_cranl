<template>
  <div
    class="widget-board"
    :class="{
      'widget-board--draggable': dragEnabled,
      'widget-board--editing': isEditMode,
    }"
  >
    <DashboardWidget
      v-for="widget in widgets"
      :key="widget.id"
      v-grid-sortable="{
        id: widget.id,
        enabled: canDrag(widget),
        update: onWidgetDrop,
      }"
      :widget="widget"
      :dashboard="dashboard"
      :store-prefix="storePrefix"
      :can-arrange="!isNarrowScreen"
    />
    <button
      v-if="isEditMode && canCreateWidget"
      type="button"
      class="widget-board__add"
      @click="$emit('add-widget')"
    >
      <i class="iconoir-plus" aria-hidden="true"></i>
      <span>{{ $t('dashboardToolbar.addWidget') }}</span>
    </button>
  </div>
</template>

<script>
import DashboardWidget from '@jadawel/modules/dashboard/components/widget/DashboardWidget'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import { computeWidgetOrderUpdate } from '@jadawel/modules/arabase/utils/gridOrder'

// Matches `$dashboard-breakpoint` in the fork's dashboard_canvas.scss: below it
// the grid collapses to one column and moving and resizing are off (the size
// menu still works there).
const GRID_BREAKPOINT = 900

export default {
  name: 'WidgetBoard',
  components: { DashboardWidget },
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
    canCreateWidget: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['add-widget'],
  data() {
    return {
      windowWidth: null,
    }
  },
  computed: {
    isEditMode() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEditMode`
      ]
    },
    widgets() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/getWidgets`
      ]
    },
    isNarrowScreen() {
      return this.windowWidth !== null && this.windowWidth <= GRID_BREAKPOINT
    },
    dragEnabled() {
      return this.isEditMode && !this.isNarrowScreen
    },
  },
  mounted() {
    this.windowWidth = window.innerWidth
    this.windowResizeEvent = () => {
      this.windowWidth = window.innerWidth
    }
    window.addEventListener('resize', this.windowResizeEvent)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.windowResizeEvent)
  },
  methods: {
    canDrag(widget) {
      return (
        this.dragEnabled &&
        this.$hasPermission(
          'dashboard.widget.update',
          widget,
          this.dashboard.workspace.id
        )
      )
    },
    /**
     * Jadawel fork (grid board): a drop only changes the moved widget's
     * position in the order — the fractional `order` between its two new
     * neighbours is computed client-side and PATCHed through the existing
     * debounced update action; the response refreshes the local order value.
     */
    async onWidgetDrop(newOrder, oldOrder, movedId) {
      const widgetsById = new Map(this.widgets.map((w) => [w.id, w]))
      const sortedWidgets = newOrder
        .map((id) => widgetsById.get(id))
        .filter(Boolean)
      const newIndex = sortedWidgets.findIndex((w) => w.id === movedId)
      if (newIndex === -1) {
        return
      }
      const order = computeWidgetOrderUpdate(sortedWidgets, movedId, newIndex)
      try {
        await this.$store.dispatch(
          `${this.storePrefix}dashboardApplication/updateWidget`,
          {
            widgetId: movedId,
            values: { order },
            originalValues: { order: widgetsById.get(movedId)?.order },
          }
        )
      } catch (error) {
        notifyIf(error, 'dashboard')
      }
    },
  },
}
</script>
