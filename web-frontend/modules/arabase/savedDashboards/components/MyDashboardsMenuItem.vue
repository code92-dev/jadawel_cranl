<template>
  <li class="context__menu-item">
    <nuxt-link
      :to="{ name: 'arabase-my-dashboards' }"
      class="context__menu-item-link"
      @click="$emit('hide')"
    >
      <i class="context__menu-item-icon jadawel-icon-dashboard"></i>
      {{ $t('myDashboards.title') }}
    </nuxt-link>
  </li>
</template>

<script>
/** The user menu's way to "My dashboards", directly above "My settings". */
export default {
  name: 'MyDashboardsMenuItem',
  emits: ['hide'],
}
</script>
