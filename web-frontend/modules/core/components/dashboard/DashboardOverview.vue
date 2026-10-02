<template>
  <section class="dashboard__section">
    <h2 class="dashboard__section-title">
      {{ $t('dashboardOverview.title') }}
    </h2>

    <div class="dashboard__stat-tiles">
      <div v-for="tile in tiles" :key="tile.key" class="dashboard__stat-tile">
        <span class="dashboard__stat-tile-icon">
          <i :class="tile.icon"></i>
        </span>
        <div class="dashboard__stat-tile-body">
          <div class="dashboard__stat-tile-label">{{ tile.label }}</div>
          <SkeletonBlock
            v-if="tile.loading"
            class="dashboard__stat-tile-skeleton"
            width="48px"
            height="24px"
          ></SkeletonBlock>
          <div v-else class="dashboard__stat-tile-value">{{ tile.value }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { rowCountsAreExact } from '@jadawel/modules/core/utils/workspaceStats'

/**
 * The workspace's headline numbers. Databases and members are known from the
 * store straight away; tables and rows come from the stats request.
 */
export default {
  name: 'DashboardOverview',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
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
    statsLoading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    tiles() {
      const stats = Object.values(this.stats)
      const tables = stats.reduce((sum, stat) => sum + stat.table_count, 0)
      const rows = stats.reduce((sum, stat) => sum + (stat.row_count || 0), 0)
      const databases = this.applications.filter(
        (application) => application.type === 'database'
      ).length

      return [
        {
          key: 'databases',
          icon: 'iconoir-db',
          label: this.$t('dashboardOverview.databases'),
          value: this.format(databases),
          loading: false,
        },
        {
          key: 'tables',
          icon: 'iconoir-table',
          label: this.$t('dashboardOverview.tables'),
          value: this.format(tables),
          loading: this.statsLoading,
        },
        {
          key: 'rows',
          icon: 'iconoir-table-rows',
          label: this.$t('dashboardOverview.rows'),
          value: rowCountsAreExact(this.stats) ? this.format(rows) : '—',
          loading: this.statsLoading,
        },
        {
          key: 'members',
          icon: 'iconoir-group',
          label: this.$t('dashboardOverview.members'),
          value: this.format(this.workspace.users?.length || 0),
          loading: false,
        },
      ]
    },
  },
  methods: {
    format(value) {
      return new Intl.NumberFormat(this.$i18n.locale).format(value)
    },
  },
}
</script>
