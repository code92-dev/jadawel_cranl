<template>
  <section class="dashboard__section">
    <h2 class="dashboard__section-title">
      {{ $t('dashboardCharts.title') }}
    </h2>

    <div class="dashboard__charts">
      <DashboardBarChart
        :title="$t('dashboardCharts.rowsPerDatabase')"
        :items="rowsPerDatabase"
        :empty-message="$t('dashboardCharts.noDatabases')"
      />
      <DashboardAreaChart
        :title="$t('dashboardCharts.rowsAddedOverTime', { days: activityDays })"
        :series="activitySeries"
        :empty-message="$t('dashboardCharts.noActivity')"
      />
    </div>
  </section>
</template>

<script>
import DashboardBarChart from '@jadawel/modules/core/components/dashboard/DashboardBarChart'
import DashboardAreaChart from '@jadawel/modules/core/components/dashboard/DashboardAreaChart'
import { rowCountsAreExact } from '@jadawel/modules/core/utils/workspaceStats'

// Beyond this the chart is a wall of near-identical bars that answers nothing.
// The remainder is folded into one row rather than dropped, so the totals in the
// overview still reconcile with what the chart shows.
const MAX_BARS = 6

/**
 * The workspace's charts: rows per database and rows added per day.
 */
export default {
  name: 'DashboardCharts',
  components: { DashboardBarChart, DashboardAreaChart },
  props: {
    applications: {
      type: Array,
      required: true,
    },
    /**
     * `{ [databaseId]: { table_count, field_count, row_count, rows_exact } }`,
     * or `{}` while the request is in flight or after it failed.
     */
    stats: {
      type: Object,
      required: true,
    },
    /**
     * `{ days, complete, total, series }`, or null until it resolves.
     */
    activity: {
      type: Object,
      required: false,
      default: null,
    },
  },
  computed: {
    rowsPerDatabase() {
      if (!rowCountsAreExact(this.stats)) {
        return []
      }

      const named = Object.entries(this.stats)
        .map(([id, stat]) => ({
          key: id,
          label:
            this.applications.find((a) => String(a.id) === String(id))?.name ||
            this.$t('dashboardCharts.untitledDatabase'),
          value: stat.row_count || 0,
        }))
        .sort((a, b) => b.value - a.value)

      if (named.length <= MAX_BARS) {
        return named
      }

      const shown = named.slice(0, MAX_BARS - 1)
      const rest = named.slice(MAX_BARS - 1)
      return [
        ...shown,
        {
          key: 'other',
          label: this.$t('dashboardCharts.otherDatabases', {
            count: rest.length,
          }),
          value: rest.reduce((sum, item) => sum + item.value, 0),
        },
      ]
    },
    activitySeries() {
      return this.activity?.complete ? this.activity.series : []
    },
    activityDays() {
      return this.activity?.days || 30
    },
  },
}
</script>
