<template>
  <Context ref="context">
    <div class="widget-size-context">
      <div class="widget-size-context__label">
        {{ $t('widgetSize.width') }}
      </div>
      <div class="widget-size-context__options">
        <button
          v-for="width in widths"
          :key="`w${width}`"
          type="button"
          class="widget-size-context__option"
          :class="{
            'widget-size-context__option--active': width === current.width,
          }"
          :disabled="width < minSize.width"
          :title="widthLabel(width)"
          @click="select({ width })"
        >
          <span class="widget-size-context__bar">
            <span
              class="widget-size-context__bar-fill"
              :style="{ inlineSize: `${(width / columns) * 100}%` }"
            ></span>
          </span>
          <span class="widget-size-context__option-label">{{
            widthLabel(width)
          }}</span>
        </button>
      </div>
      <div class="widget-size-context__label">
        {{ $t('widgetSize.height') }}
      </div>
      <div class="widget-size-context__heights">
        <button
          v-for="height in heights"
          :key="`h${height}`"
          type="button"
          class="widget-size-context__height"
          :class="{
            'widget-size-context__height--active': height === current.height,
          }"
          :disabled="height < minSize.height"
          :title="$t('widgetSize.rows', { count: height })"
          @click="select({ height })"
        >
          {{ height }}
        </button>
      </div>
      <p class="widget-size-context__hint">
        {{ $t('widgetSize.current', current) }} ·
        {{ $t('widgetSize.dragHint') }}
      </p>
    </div>
  </Context>
</template>

<script>
import context from '@jadawel/modules/core/mixins/context'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import {
  DEFAULT_MIN_SIZE,
  GRID_COLUMNS,
  HEIGHT_PRESETS,
  WIDTH_PRESETS,
  widgetSize,
} from '@jadawel/modules/arabase/dashboard/layout'

/**
 * The widget's "Size" menu: a width as a share of the row (quarter, third,
 * half, two thirds, full) and a height in rows. The corner handle on the board
 * resizes to any cell; this menu is the precise, keyboard-reachable way to the
 * common sizes. Changes go through the store's debounced `updateWidget`.
 */
export default {
  name: 'WidgetSizeContext',
  mixins: [context],
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
  },
  emits: ['selected'],
  computed: {
    columns() {
      return GRID_COLUMNS
    },
    widths() {
      return WIDTH_PRESETS
    },
    heights() {
      return HEIGHT_PRESETS
    },
    minSize() {
      const type = this.$registry.get('dashboardWidget', this.widget.type)
      return type?.minSize || DEFAULT_MIN_SIZE
    },
    current() {
      return widgetSize(this.widget, this.minSize)
    },
  },
  methods: {
    widthLabel(width) {
      return this.$t(`widgetSize.widths.${width}`)
    },
    async select(change) {
      const size = { ...this.current, ...change }
      if (
        size.width === this.current.width &&
        size.height === this.current.height
      ) {
        return
      }
      // Closed before the request: the store debounces the PATCH by a second,
      // and rolls the widget back itself if it fails.
      this.hide()
      this.$emit('selected')
      try {
        await this.$store.dispatch(
          `${this.storePrefix}dashboardApplication/updateWidget`,
          {
            widgetId: this.widget.id,
            values: size,
            originalValues: { ...this.current },
          }
        )
      } catch (error) {
        notifyIf(error, 'dashboard')
      }
    },
  },
}
</script>
