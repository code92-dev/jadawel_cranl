<template>
  <li class="tree__item" :class="{ active: rightSidebarOpen }">
    <div class="tree__action sidebar__action">
      <a
        class="tree__link"
        role="button"
        :aria-pressed="rightSidebarOpen ? 'true' : 'false'"
        @click.prevent="toggle"
      >
        <i class="tree__icon iconoir-sparks"></i>
        <span class="tree__link-text">
          <span class="sidebar__item-name">{{ $t('sanad.name') }}</span>
        </span>
      </a>
    </div>
  </li>
</template>

<script>
/**
 * Opens Sanad in core's right sidebar, the slot upstream reserved for its
 * assistant. Rendered only for staff (see ArabasePlugin).
 */
export default {
  name: 'SanadSidebarItem',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    rightSidebarOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  methods: {
    toggle() {
      this.$bus.$emit('toggle-right-sidebar')
    },
  },
}
</script>
