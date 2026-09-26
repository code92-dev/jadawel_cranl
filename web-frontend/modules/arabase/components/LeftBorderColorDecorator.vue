<template>
  <div v-if="barClass" :class="barClass"></div>
</template>

<script>
import { COLOR_PATTERN } from '@jadawel/modules/arabase/utils/rowColor'

export default {
  name: 'LeftBorderColorDecorator',
  props: {
    value: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    barClass() {
      // Reuses core's palette so the bar matches select badges. Anything
      // outside the palette renders nothing.
      if (typeof this.value !== 'string' || !COLOR_PATTERN.test(this.value)) {
        return null
      }
      return `row-coloring__border-bar background-color--${this.value}`
    },
  },
}
</script>
