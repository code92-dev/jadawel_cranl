<template>
  <section
    class="widget-frame"
    :class="[
      `widget-accent--${accentName}`,
      { 'widget-frame--bare': bare, 'widget-frame--loading': loading },
    ]"
    :aria-busy="loading ? 'true' : 'false'"
  >
    <header v-if="!hideHeader" class="widget-frame__header widget__header">
      <span v-if="iconName" class="widget-frame__icon" aria-hidden="true">
        <i :class="`iconoir-${iconName}`"></i>
      </span>
      <div class="widget-frame__heading">
        <div class="widget-frame__title-row">
          <h3 class="widget-frame__title" :title="title">
            {{ title }}
          </h3>
          <Badge
            v-if="misconfigured && !loading"
            color="red"
            size="small"
            indicator
            rounded
            >{{ $t('widget.fixConfiguration') }}</Badge
          >
          <slot v-else-if="!loading" name="badges"></slot>
        </div>
        <p
          v-if="description"
          class="widget-frame__description"
          :title="description"
        >
          {{ description }}
        </p>
      </div>
      <div v-if="$slots.actions && !loading" class="widget-frame__actions">
        <slot name="actions"></slot>
      </div>
    </header>

    <div class="widget-frame__body">
      <div v-if="loading" class="widget-frame__skeleton" aria-hidden="true">
        <span class="widget-frame__skeleton-line"></span>
        <span class="widget-frame__skeleton-line"></span>
        <span class="widget-frame__skeleton-line"></span>
      </div>
      <div v-else-if="misconfigured" class="widget-frame__state">
        <i
          class="iconoir-settings widget-frame__state-icon"
          aria-hidden="true"
        ></i>
        <p class="widget-frame__state-text">
          {{ misconfiguredMessage || $t('widgetFrame.misconfigured') }}
        </p>
        <p v-if="editMode" class="widget-frame__state-hint">
          {{ $t('widgetFrame.openSettings') }}
        </p>
      </div>
      <div v-else-if="empty" class="widget-frame__state">
        <i
          :class="`iconoir-${emptyIcon}`"
          class="widget-frame__state-icon"
          aria-hidden="true"
        ></i>
        <p class="widget-frame__state-text">
          {{ emptyMessage || $t('widgetFrame.empty') }}
        </p>
      </div>
      <slot v-else></slot>
    </div>

    <footer
      v-if="$slots.footer && !loading && !misconfigured && !empty"
      class="widget-frame__footer"
    >
      <slot name="footer"></slot>
    </footer>
  </section>
</template>

<script>
import { accentOf, iconOf } from '@jadawel/modules/arabase/dashboard/appearance'
import { riyalText } from '@jadawel/modules/arabase/dashboard/format'

/**
 * The card every dashboard widget renders in: an optional icon chip, the title
 * and description, badges beside the title, and the body — or, instead of the
 * body, a skeleton while the data loads, a note when the widget is not set up,
 * or an empty state. One frame keeps the widgets consistent and lets a widget
 * component be about its content only.
 *
 * The header keeps core's `widget__header` class: it is the drag handle the
 * board's sortable directive looks for.
 */
export default {
  name: 'WidgetFrame',
  props: {
    widget: {
      type: Object,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    editMode: {
      type: Boolean,
      default: false,
    },
    misconfigured: {
      type: Boolean,
      default: false,
    },
    misconfiguredMessage: {
      type: String,
      default: null,
    },
    empty: {
      type: Boolean,
      default: false,
    },
    emptyMessage: {
      type: String,
      default: null,
    },
    emptyIcon: {
      type: String,
      default: 'database-script',
    },
    /** An icon to show when the widget has none of its own. */
    defaultIcon: {
      type: String,
      default: null,
    },
    /** No card chrome: a section heading sits on the canvas itself. */
    bare: {
      type: Boolean,
      default: false,
    },
    hideHeader: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    accentName() {
      return accentOf(this.widget)
    },
    iconName() {
      return iconOf(this.widget, this.defaultIcon)
    },
    /** "Budget (SAR)" reads "Budget (⃁)": the riyal is written as its sign. */
    title() {
      return riyalText(this.widget.title)
    },
    description() {
      return riyalText(this.widget.description)
    },
  },
}
</script>
