<template>
  <div :class="backgroundClass"><slot /></div>
</template>

<script>
const COLOR_PATTERN = /^[a-z-]+$/

export default {
  name: 'BackgroundColorDecorator',
  props: {
    value: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    backgroundClass() {
      // Reuses core's global `background-color--*` palette so decorated rows
      // match select badges. Anything outside the palette renders plain.
      if (typeof this.value !== 'string' || !COLOR_PATTERN.test(this.value)) {
        return null
      }
      return `background-color--${this.value}`
    },
  },
}
</script>
