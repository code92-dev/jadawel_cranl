<template>
  <div class="quick-styles">
    <div class="quick-styles__label">{{ $t('quickStyles.title') }}</div>
    <div class="quick-styles__options">
      <button
        v-for="key in styles"
        :key="key"
        type="button"
        class="quick-style"
        :class="{ 'quick-style--active': key === current }"
        :aria-pressed="key === current"
        :disabled="disabled"
        :title="$t(`quickStyles.styles.${key}.description`)"
        @click="$emit('apply', values(key))"
      >
        <span
          class="quick-style__swatch"
          :class="`quick-style__swatch--${key}`"
          :style="swatchStyle(key)"
          aria-hidden="true"
        >
          <i></i><i></i>
        </span>
        <span class="quick-style__name">{{
          $t(`quickStyles.styles.${key}.name`)
        }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import {
  QUICK_STYLES,
  matchingQuickStyle,
  quickStyle,
} from '@jadawel/modules/arabase/builder/elementQuickStyles'

/**
 * The top of a container element's Style panel: plain, card, tinted or
 * outlined in one click. Emits the `style_*` values to save; the fields below
 * keep every one of them editable.
 */
export default {
  name: 'ElementQuickStyles',
  props: {
    element: {
      type: Object,
      required: true,
    },
    theme: {
      type: Object,
      required: false,
      default: () => ({}),
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['apply'],
  computed: {
    styles() {
      return QUICK_STYLES
    },
    current() {
      return matchingQuickStyle(this.element, this.theme)
    },
  },
  methods: {
    values(key) {
      return quickStyle(key, this.theme)
    },
    swatchStyle(key) {
      const style = quickStyle(key, this.theme)
      return {
        '--swatch-background':
          style.style_background === 'color'
            ? style.style_background_color.slice(0, 7)
            : 'transparent',
        '--swatch-accent': (this.theme.primary_color || '#278053').slice(0, 7),
      }
    },
  },
}
</script>
