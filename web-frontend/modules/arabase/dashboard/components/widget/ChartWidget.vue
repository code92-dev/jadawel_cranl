<template>
  <div class="dashboard-chart-widget">
    <template v-if="!loading">
      <div class="widget__header widget__header--no-border">
        <div class="widget__header-main">
          <div class="widget__header-title-wrapper">
            <div class="widget__header-title">{{ widget.title }}</div>

            <Badge
              v-if="dataSourceMisconfigured"
              color="red"
              indicator
              rounded
              >{{ $t('widget.fixConfiguration') }}</Badge
            >
            <Badge v-else-if="truncated" color="yellow" indicator rounded>{{
              $t('chartWidget.truncated', { count: maxBuckets })
            }}</Badge>
          </div>
          <div v-if="widget.description" class="widget__header-description">
            {{ widget.description }}
          </div>
        </div>
        <WidgetContextMenu
          v-if="isEditMode"
          :widget="widget"
          :dashboard="dashboard"
          @delete-widget="$emit('delete-widget', $event)"
        ></WidgetContextMenu>
      </div>
      <div class="widget__content dashboard-chart-widget__chart">
        <div
          v-if="dataSourceMisconfigured || !hasData"
          class="dashboard-chart-widget__empty"
        >
          {{
            dataSourceMisconfigured
              ? $t('chartWidget.misconfigured')
              : $t('chartWidget.noData')
          }}
        </div>
        <component
          :is="chartComponent"
          v-else
          :key="widget.chart_type"
          :data="chartData"
          :options="chartOptions"
        />
      </div>
    </template>
    <div v-else class="dashboard-chart-widget__loading loading-spinner"></div>
  </div>
</template>

<script>
import {
  Bar as BarChart,
  Line as LineChart,
  Pie as PieChart,
  Doughnut as DoughnutChart,
} from 'vue-chartjs'
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import colorStyles from '@jadawel/modules/core/assets/scss/colors.module.scss'
import { getBaseColors } from '@jadawel/modules/core/utils/colors'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'
import WidgetContextMenu from '@jadawel/modules/dashboard/components/widget/WidgetContextMenu'

Chart.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip
)

// A pie slice per bucket needs one colour per bucket, so the palette has to be
// able to repeat. Bar and line charts use one colour per series instead.
const FALLBACK_PALETTE = getBaseColors()

/**
 * Resolves a stored colour to something chart.js can paint with: either a
 * literal hex, or one of Jadawel's colour names (what a single select option
 * stores) looked up in the shared palette.
 *
 * The name lookup is deliberately strict about what comes back. `colorStyles` is
 * a CSS modules object, and asking one for a key it does not export can return a
 * generated class name rather than `undefined` — so a value is only accepted if
 * it actually looks like a colour.
 */
const resolveColor = (value) => {
  if (typeof value !== 'string' || value === '') {
    return null
  }
  if (value.startsWith('#')) {
    return value
  }
  const named = colorStyles[value]
  return typeof named === 'string' && named.startsWith('#') ? named : null
}

export default {
  name: 'ChartWidget',
  components: {
    WidgetContextMenu,
    BarChart,
    LineChart,
    PieChart,
    DoughnutChart,
  },
  mixins: [dashboardWidget],
  emits: ['delete-widget'],
  computed: {
    result() {
      return this.dataForDataSource?.result || null
    },
    series() {
      return this.result?.series || []
    },
    groups() {
      return this.result?.groups || []
    },
    truncated() {
      return !!this.result?.truncated
    },
    maxBuckets() {
      return this.groups.length
    },
    hasData() {
      return this.series.some((s) => (s.data || []).length > 0)
    },
    isSliced() {
      return ['pie', 'doughnut'].includes(this.widget.chart_type)
    },
    chartComponent() {
      return {
        bar: BarChart,
        line: LineChart,
        pie: PieChart,
        doughnut: DoughnutChart,
      }[this.widget.chart_type]
    },
    /**
     * Bucket labels. An unset group by returns a single unlabelled bucket, and
     * a row whose grouped value is empty gets an explicit label rather than a
     * blank tick.
     */
    labels() {
      if (this.groups.length === 0) {
        return this.series.map((s) => this.seriesLabel(s))
      }
      // `||` treated every falsy bucket value as empty, so grouping by a number
      // field labelled each `0` bucket "Empty" and grouping by a boolean did the
      // same to `false`. Only null, undefined and the empty string are absent.
      return this.groups.map((group) => {
        const value = group?.value
        if (value === null || value === undefined || value === '') {
          return this.$t('chartWidget.emptyGroup')
        }
        return String(value)
      })
    },
    /**
     * Colours the buckets take when the chart draws one slice per bucket. A
     * single select group by carries its own option colours, which users expect
     * to see again in the chart.
     */
    bucketColors() {
      return this.groups.map(
        (group, index) =>
          resolveColor(group?.color) ||
          FALLBACK_PALETTE[index % FALLBACK_PALETTE.length]
      )
    },
    chartData() {
      if (this.groups.length === 0) {
        // No group by: each series contributes one value, so the series
        // themselves become the categories.
        return {
          labels: this.labels,
          datasets: [
            {
              label: this.widget.title,
              data: this.series.map((s) => (s.data || [])[0] ?? null),
              backgroundColor: this.series.map(
                (s, index) =>
                  this.seriesColor(s) ||
                  FALLBACK_PALETTE[index % FALLBACK_PALETTE.length]
              ),
            },
          ],
        }
      }

      return {
        labels: this.labels,
        datasets: this.series.map((s, index) => {
          const color =
            this.seriesColor(s) ||
            FALLBACK_PALETTE[index % FALLBACK_PALETTE.length]
          return {
            label: this.seriesLabel(s),
            data: s.data || [],
            backgroundColor: this.isSliced ? this.bucketColors : color,
            borderColor: color,
            tension: 0.4,
          }
        }),
      }
    },
    /**
     * Chart.js draws into a canvas, so it never inherits `dir` from the page:
     * without being told, an Arabic dashboard renders its legend, tooltips and
     * category axis left to right inside an RTL layout.
     *
     * `<html dir>` is the source of truth (the arabase plugin sets it from the
     * locale, and core's Context.vue reads it the same way). `$i18n.locale` is
     * referenced only so this recomputes when the user switches language.
     */
    rtl() {
      const locale = this.$i18n.locale
      return (
        Boolean(locale) &&
        typeof document !== 'undefined' &&
        document.documentElement.dir === 'rtl'
      )
    },
    chartOptions() {
      const rtl = this.rtl

      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: this.widget.show_legend && this.series.length > 0,
            align: 'start',
            position: 'bottom',
            rtl,
            textDirection: rtl ? 'rtl' : 'ltr',
          },
          tooltip: {
            rtl,
            textDirection: rtl ? 'rtl' : 'ltr',
          },
        },
        scales: this.isSliced
          ? {}
          : {
              x: { reverse: rtl },
              y: { beginAtZero: true, position: rtl ? 'right' : 'left' },
            },
      }
    },
  },
  methods: {
    seriesConfig(series) {
      return (this.widget.series_config || {})[series.key] || {}
    },
    seriesLabel(series) {
      const configured = this.seriesConfig(series).label
      if (configured) {
        return configured
      }
      const aggregationType = this.$registry.get(
        'viewAggregation',
        series.aggregation_type
      )
      return `${series.label} (${aggregationType.getName()})`
    },
    seriesColor(series) {
      return resolveColor(this.seriesConfig(series).color)
    },
  },
}
</script>
