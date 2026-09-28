<template>
  <div class="dashboard-empty">
    <div class="dashboard-empty__preview" aria-hidden="true">
      <span class="dashboard-empty__tile dashboard-empty__tile--kpi"></span>
      <span class="dashboard-empty__tile dashboard-empty__tile--kpi"></span>
      <span class="dashboard-empty__tile dashboard-empty__tile--kpi"></span>
      <span class="dashboard-empty__tile dashboard-empty__tile--chart">
        <i
          v-for="bar in [40, 70, 55, 90, 65]"
          :key="bar"
          :style="{ blockSize: `${bar}%` }"
        ></i>
      </span>
      <span class="dashboard-empty__tile dashboard-empty__tile--ring"></span>
    </div>
    <h2 class="dashboard-empty__title">{{ $t('dashboardEmpty.title') }}</h2>
    <p class="dashboard-empty__text">
      {{
        canCreateWidget
          ? $t('dashboardEmpty.text')
          : $t('dashboardEmpty.readOnly')
      }}
    </p>
    <Button
      v-if="canCreateWidget"
      type="primary"
      size="large"
      icon="iconoir-plus"
      @click="$emit('add-widget')"
      >{{ $t('dashboardEmpty.addWidget') }}</Button
    >
  </div>
</template>

<script>
/**
 * A dashboard with no widgets yet: a sketch of what one looks like and the way
 * to start. Replaces core's `EmptyDashboard`, whose own add-widget modal the
 * fork's gallery supersedes.
 */
export default {
  name: 'DashboardEmptyState',
  props: {
    canCreateWidget: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['add-widget'],
}
</script>
