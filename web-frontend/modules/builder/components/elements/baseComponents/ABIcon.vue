<template>
  <button
    v-if="isButton"
    type="button"
    class="ab-icon"
    :class="{
      'loading-spinner': loading,
      'ab-icon--button': isButton,
      [icon]: true,
    }"
    :title="title"
    :aria-label="ariaLabel || title || null"
    @click="$emit('click', $event)"
  />
  <i
    v-else
    class="ab-icon"
    :class="{
      'loading-spinner': loading,
      [icon]: true,
    }"
    :title="title"
    @click="$emit('click', $event)"
  />
</template>

<script>
/**
 * Shared icon control.
 *
 * When `isButton` is set the icon renders as a semantic `<button type>`
 * with an accessible name (from `ariaLabel` or `title`), so it is
 * focusable and keyboard-activatable (Enter/Space) without further
 * changes at the call site. Non-button icons keep the plain `<i>` tag.
 */
export default {
  name: 'ABIcon',
  props: {
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
    isButton: {
      type: Boolean,
      default: false,
    },
    icon: {
      type: String,
      required: true,
    },
    title: {
      type: String,
      default: '',
    },
    ariaLabel: {
      type: String,
      default: '',
    },
  },
  emits: ['click'],
}
</script>
