<template>
  <div
    class="widget-text"
    :class="[`widget-text--${textStyle}`, `widget-accent--${accentName}`]"
  >
    <span v-if="iconName" class="widget-text__icon" aria-hidden="true">
      <i :class="`iconoir-${iconName}`"></i>
    </span>
    <div class="widget-text__content">
      <component
        :is="textStyle === 'section' ? 'h2' : 'h3'"
        class="widget-text__title widget__header"
      >
        {{ widget.title }}
      </component>
      <p v-if="widget.body" class="widget-text__body">
        {{ widget.body }}
      </p>
      <p v-else-if="isEditMode" class="widget-text__placeholder">
        {{ $t('textWidget.placeholder') }}
      </p>
    </div>
  </div>
</template>

<script>
import { accentOf, iconOf } from '@jadawel/modules/arabase/dashboard/appearance'

const STYLES = ['section', 'note', 'callout']

/**
 * Words on the board: a section heading that splits the dashboard into parts,
 * a note on how to read it, or a callout for what needs attention. The body is
 * plain text with its line breaks kept (`white-space: pre-line`); nothing is
 * parsed as markup.
 *
 * The title carries `widget__header` so a text widget can be dragged by it like
 * any other.
 */
export default {
  name: 'TextWidget',
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
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['delete-widget'],
  computed: {
    textStyle() {
      return STYLES.includes(this.widget.text_style)
        ? this.widget.text_style
        : 'note'
    },
    accentName() {
      return accentOf(
        this.widget,
        this.textStyle === 'callout' ? 'blue' : 'primary'
      )
    },
    iconName() {
      return iconOf(
        this.widget,
        this.textStyle === 'callout' ? 'light-bulb' : null
      )
    },
    isEditMode() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEditMode`
      ]
    },
  },
}
</script>
