<template>
  <!--
    Jadawel: the themed bar across the top of the content column, level with
    the sidebar's own top, so the theme colour reads as one line across the
    app. The app layout renders it for every page that has no header of its
    own; My dashboards is the model it follows. A page that wants its own
    actions on the bar sets `ownHeader` and renders this itself, with the
    actions in the default slot.
  -->
  <header class="layout__col-2-1 header app-header-bar">
    <h1 class="app-header-bar__title">
      <i v-if="icon" :class="icon"></i>
      <span class="app-header-bar__title-text">{{ title }}</span>
    </h1>
    <div v-if="$slots.default" class="app-header-bar__actions">
      <slot></slot>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppHeaderBar',
  props: {
    title: {
      type: String,
      required: false,
      default: '',
    },
    icon: {
      type: String,
      required: false,
      default: null,
    },
  },
}
</script>
