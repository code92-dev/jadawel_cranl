<template>
  <div class="widget-chrome" :class="{ 'widget-chrome--resizing': resizing }">
    <div class="widget-chrome__toolbar" @click.stop>
      <span
        v-if="canUpdate && canDrag"
        class="widget-chrome__button widget-chrome__drag"
        :title="$t('widgetChrome.move')"
        :aria-label="$t('widgetChrome.move')"
      >
        <i class="iconoir-drag"></i>
      </span>
      <button
        v-if="canUpdate"
        ref="sizeButton"
        type="button"
        class="widget-chrome__button"
        :title="$t('widgetChrome.size')"
        :aria-label="$t('widgetChrome.size')"
        @click="
          $refs.sizeContext.toggle($refs.sizeButton, 'bottom', 'right', 6)
        "
      >
        <i class="iconoir-scale-frame-enlarge"></i>
      </button>
      <button
        v-if="canDelete"
        type="button"
        class="widget-chrome__button widget-chrome__button--danger"
        :class="{ 'widget-chrome__button--loading': deleting }"
        :title="$t('widgetChrome.delete')"
        :aria-label="$t('widgetChrome.delete')"
        @click="deleteWidget"
      >
        <i class="iconoir-bin"></i>
      </button>
    </div>

    <span
      v-if="canUpdate && canResize"
      class="widget-chrome__resize"
      :title="$t('widgetChrome.resize')"
      @pointerdown.stop.prevent="startResize"
      @click.stop
    ></span>

    <span v-if="resizing && preview" class="widget-chrome__size">
      {{ $t('widgetSize.current', preview) }}
    </span>

    <WidgetSizeContext
      v-if="canUpdate"
      ref="sizeContext"
      :widget="widget"
      :dashboard="dashboard"
      :store-prefix="storePrefix"
    />
  </div>
</template>

<script>
import WidgetSizeContext from '@jadawel/modules/arabase/dashboard/components/widget/WidgetSizeContext'
import {
  DEFAULT_MIN_SIZE,
  sizeFromDrag,
  widgetSize,
} from '@jadawel/modules/arabase/dashboard/layout'
import { notifyIf } from '@jadawel/modules/core/utils/error'

/**
 * What a widget carries while the dashboard is being edited: a small toolbar
 * (move, size, delete) and a corner handle that resizes it by dragging.
 *
 * The drag snaps to the board's cells as the pointer moves, and the widget
 * shows the new size while it does (`preview`); only the final size is saved,
 * in one PATCH, when the pointer is released. Escape puts it back.
 */
export default {
  name: 'WidgetEditChrome',
  components: { WidgetSizeContext },
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
    /** Moving and resizing are off on a narrow, single-column board. */
    canDrag: {
      type: Boolean,
      required: false,
      default: true,
    },
    canResize: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  emits: ['preview'],
  data() {
    return {
      resizing: false,
      preview: null,
      deleting: false,
    }
  },
  computed: {
    canUpdate() {
      return this.$hasPermission(
        'dashboard.widget.update',
        this.widget,
        this.dashboard.workspace.id
      )
    },
    canDelete() {
      return this.$hasPermission(
        'dashboard.widget.delete',
        this.widget,
        this.dashboard.workspace.id
      )
    },
    minSize() {
      const type = this.$registry.get('dashboardWidget', this.widget.type)
      return type?.minSize || DEFAULT_MIN_SIZE
    },
  },
  beforeUnmount() {
    this.stopListening()
  },
  methods: {
    startResize(event) {
      const board = this.$el.closest('.widget-board')
      if (!board || event.button !== 0) {
        return
      }
      this.resizing = true
      this.start = {
        x: event.clientX,
        y: event.clientY,
        size: widgetSize(this.widget, this.minSize),
        boardWidth: board.getBoundingClientRect().width,
        rtl: document.documentElement.dir === 'rtl',
      }
      this.preview = { ...this.start.size }
      this.$emit('preview', this.preview)

      this.onMove = (moveEvent) => this.moveResize(moveEvent)
      this.onUp = () => this.endResize(true)
      this.onKey = (keyEvent) => {
        if (keyEvent.key === 'Escape') {
          this.endResize(false)
        }
      }
      window.addEventListener('pointermove', this.onMove)
      window.addEventListener('pointerup', this.onUp)
      window.addEventListener('keydown', this.onKey)
      document.body.classList.add('widget-board-resizing')
    },
    moveResize(event) {
      const size = sizeFromDrag({
        start: this.start.size,
        dx: event.clientX - this.start.x,
        dy: event.clientY - this.start.y,
        boardWidth: this.start.boardWidth,
        rtl: this.start.rtl,
        minSize: this.minSize,
      })
      if (
        size.width !== this.preview.width ||
        size.height !== this.preview.height
      ) {
        this.preview = size
        this.$emit('preview', size)
      }
    },
    async endResize(save) {
      const size = this.preview
      const original = this.start.size
      this.stopListening()
      this.resizing = false
      this.preview = null
      if (
        !save ||
        !size ||
        (size.width === original.width && size.height === original.height)
      ) {
        this.$emit('preview', null)
        return
      }
      // The store applies the size right away and debounces the request, so
      // the preview can be dropped without the widget jumping back.
      const request = this.$store.dispatch(
        `${this.storePrefix}dashboardApplication/updateWidget`,
        { widgetId: this.widget.id, values: size, originalValues: original }
      )
      this.$emit('preview', null)
      try {
        await request
      } catch (error) {
        notifyIf(error, 'dashboard')
      }
    },
    stopListening() {
      window.removeEventListener('pointermove', this.onMove)
      window.removeEventListener('pointerup', this.onUp)
      window.removeEventListener('keydown', this.onKey)
      document.body.classList.remove('widget-board-resizing')
    },
    async deleteWidget() {
      this.deleting = true
      try {
        await this.$store.dispatch(
          `${this.storePrefix}dashboardApplication/deleteWidget`,
          this.widget.id
        )
      } catch (error) {
        notifyIf(error, 'dashboard')
      } finally {
        this.deleting = false
      }
    },
  },
}
</script>
