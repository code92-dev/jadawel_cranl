<template>
  <div :class="{ dragging: dragging }" @mousedown.stop="start($event)"></div>
</template>

<script>
import { isRtlElement } from '@jadawel/modules/core/utils/dom'

export default {
  name: 'HorizontalResize',
  props: {
    width: {
      type: Number,
      required: true,
    },
    min: {
      type: Number,
      required: false,
      default: 0,
    },
    max: {
      type: [Number, null],
      required: false,
      default: null,
    },
    stopPropagation: {
      type: Boolean,
      required: false,
      default: false,
    },
    right: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['move', 'update', 'dragging'],
  data() {
    return {
      dragging: false,
      mouseStart: 0,
      startWidth: 0,
      rtl: false,
    }
  },
  methods: {
    start(event) {
      event.preventDefault()
      if (this.stopPropagation) {
        event.stopPropagation()
      }
      this.dragging = true
      // Resolved once per drag because the direction can't change while dragging
      // and reading it on every mousemove would force a style recalculation.
      this.rtl = isRtlElement(this.$el)
      this.mouseStart = event.clientX
      this.startWidth = parseFloat(this.width)

      this.$el.moveEvent = (event) => this.move(event)
      this.$el.upEvent = (event) => this.up(event)

      window.addEventListener('mousemove', this.$el.moveEvent)
      window.addEventListener('mouseup', this.$el.upEvent)
      document.body.classList.add('resizing-horizontal')
      this.$emit('dragging', true)
    },
    /**
     * The pointer movement is converted into a distance along the inline axis, so
     * that dragging away from the element always makes it wider in both LTR and
     * RTL. Without this the handle works in reverse when the direction is RTL.
     */
    calculateWidth(event) {
      const difference = this.rtl
        ? this.mouseStart - event.clientX
        : event.clientX - this.mouseStart
      let newWidth = 0
      if (this.right) {
        newWidth = Math.max(this.startWidth - difference, this.min)
      } else {
        newWidth = Math.max(this.startWidth + difference, this.min)
      }
      if (this.max) {
        newWidth = Math.min(newWidth, this.max)
      }

      return newWidth
    },
    move(event) {
      event.preventDefault()
      this.$emit('move', this.calculateWidth(event))
    },
    up(event) {
      event.preventDefault()
      this.dragging = false
      const newWidth = this.calculateWidth(event)
      window.removeEventListener('mousemove', this.$el.moveEvent)
      window.removeEventListener('mouseup', this.$el.upEvent)
      document.body.classList.remove('resizing-horizontal')
      this.$emit('dragging', false)

      if (newWidth === this.startWidth) {
        return
      }

      this.$emit('update', { width: newWidth, oldWidth: this.startWidth })
    },
  },
}
</script>
