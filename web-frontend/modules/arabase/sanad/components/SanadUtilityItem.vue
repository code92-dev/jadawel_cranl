<template>
  <li class="context__menu-item" role="none">
    <a class="context__menu-item-link" role="menuitem" @click="open">
      <i class="context__menu-item-icon iconoir-sparks"></i>
      {{ $t('sanad.name') }}
    </a>
  </li>
</template>

<script>
/**
 * Opens Sanad from the workspace tools window. The chat itself stays in core's
 * right sidebar, beside the page being worked on. Rendered only for users
 * Sanad is available to (see ArabasePlugin).
 */
export default {
  name: 'SanadUtilityItem',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  emits: ['close'],
  methods: {
    open() {
      this.$emit('close')
      this.$bus.$emit('toggle-right-sidebar', true)
    },
  },
}
</script>
