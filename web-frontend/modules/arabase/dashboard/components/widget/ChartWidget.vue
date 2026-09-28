<template>
  <WidgetFrame
    :widget="widget"
    :loading="loading"
    :edit-mode="isEditMode"
    :misconfigured="dataSourceMisconfigured"
    :misconfigured-message="$t('chartWidget.misconfigured')"
    :empty="!hasData"
    :empty-message="$t('chartWidget.noData')"
    empty-icon="stats-report"
  >
    <template #badges>
      <Badge v-if="truncated" color="yellow" size="small" indicator rounded>{{
        $t('chartWidget.truncated', { count: groups.length })
      }}</Badge>
    </template>

    <div v-if="isSliced" class="widget-chart widget-chart--sliced">
      <div class="widget-chart__pie">
        <div class="widget-chart__canvas">
          <component
            :is="chartComponent"
            :key="chartKey"
            :data="chartData"
            :options="chartOptions"
          />
        </div>
        <div
          v-if="widget.chart_type === 'doughnut'"
          class="widget-chart__center"
        >
          <span class="widget-chart__center-value">{{
            formatValue(sliceTotal, true)
          }}</span>
          <span class="widget-chart__center-label">{{
            $t('chartWidget.total')
          }}</span>
        </div>
      </div>
      <ul v-if="widget.show_legend" class="widget-chart__legend">
        <li
          v-for="slice in slices"
          :key="slice.index"
          class="widget-chart__legend-item"
        >
          <span
            class="widget-chart__swatch"
            :style="{ backgroundColor: slice.color }"
          ></span>
          <span class="widget-chart__legend-label" :title="slice.label">{{
            slice.label
          }}</span>
          <span class="widget-chart__legend-value">{{
            formatValue(slice.value)
          }}</span>
          <span class="widget-chart__legend-share">{{ slice.share }}</span>
        </li>
      </ul>
    </div>

    <div v-else class="widget-chart">
      <component
        :is="chartComponent"
        :key="chartKey"
        :data="chartData"
        :options="chartOptions"
      />
    </div>
  </WidgetFrame>
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
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import colorStyles from '@jadawel/modules/core/assets/scss/colors.module.scss'
import WidgetFrame from '@jadawel/modules/arabase/dashboard/components/widget/WidgetFrame'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'
import {
  accentOf,
  numberFormatOf,
  seriesPalette,
  withAlpha,
} from '@jadawel/modules/arabase/dashboard/appearance'
import {
  formatNumber,
  riyalText,
  toNumber,
} from '@jadawel/modules/arabase/dashboard/format'
import { chartTheme } from '@jadawel/modules/arabase/dashboard/chartTheme'

Chart.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip
)

const SLICED = ['pie', 'doughnut']
const COMPONENTS = {
  bar: BarChart,
  horizontal_bar: BarChart,
  line: LineChart,
  area: LineChart,
  pie: PieChart,
  doughnut: DoughnutChart,
}

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
export const resolveColor = (value) => {
  if (typeof value !== 'string' || value === '') {
    return null
  }
  if (value.startsWith('#')) {
    return value
  }
  const named = colorStyles[value]
  return typeof named === 'string' && named.startsWith('#') ? named : null
}

/**
 * A select option's colour as a chart paints it. Option colours are pale tints
 * made to sit behind cell text; as a slice or a bar they wash out. The same hue
 * at its strongest step keeps "Won is green" while reading as a data colour.
 */
export const resolveOptionColor = (value) => {
  if (typeof value !== 'string' || value.startsWith('#')) {
    return resolveColor(value)
  }
  const hue = value.replace(/^(light|dark|darker)-/, '')
  return resolveColor(`darker-${hue}`) || resolveColor(value)
}

/** The widest a category label runs on one line before it wraps. */
const TICK_LINE = 14

/**
 * A category label as up to two lines, split on spaces, the second cut with
 * an ellipsis. Chart.js draws an array as stacked lines, so a project name
 * wraps under its bar instead of being clipped.
 */
export const wrapLabel = (label) => {
  const text = String(label)
  if (text.length <= TICK_LINE) {
    return text
  }
  const lines = ['']
  for (const word of text.split(/\s+/)) {
    const line = lines[lines.length - 1]
    if (line && `${line} ${word}`.length > TICK_LINE) {
      lines.push(word)
    } else {
      lines[lines.length - 1] = line ? `${line} ${word}` : word
    }
  }
  const [first, ...rest] = lines
  if (rest.length === 0) {
    return first.length > TICK_LINE
      ? `${first.slice(0, TICK_LINE - 1)}…`
      : first
  }
  const second = rest.join(' ')
  return [
    first.length > TICK_LINE ? `${first.slice(0, TICK_LINE - 1)}…` : first,
    second.length > TICK_LINE ? `${second.slice(0, TICK_LINE - 1)}…` : second,
  ]
}

export default {
  name: 'ChartWidget',
  components: {
    WidgetFrame,
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
    hasData() {
      return this.series.some((s) => (s.data || []).length > 0)
    },
    chartType() {
      return COMPONENTS[this.widget.chart_type] ? this.widget.chart_type : 'bar'
    },
    isSliced() {
      return SLICED.includes(this.chartType)
    },
    isHorizontal() {
      return this.chartType === 'horizontal_bar'
    },
    isStacked() {
      return (
        this.widget.appearance?.stacked === true &&
        ['bar', 'horizontal_bar', 'area'].includes(this.chartType) &&
        this.series.length > 1
      )
    },
    /** Area charts fill down to the axis, or to the series below when stacked. */
    lineFill() {
      if (this.chartType !== 'area') {
        return false
      }
      return this.isStacked ? 'stack' : 'origin'
    },
    chartComponent() {
      return COMPONENTS[this.chartType]
    },
    chartKey() {
      return `${this.chartType}-${this.isStacked}-${this.rtl}`
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
      // Only null, undefined and the empty string are absent: a `0` bucket of a
      // number field or a `false` one of a boolean are real values.
      return this.groups.map((group) => {
        const value = group?.value
        if (value === null || value === undefined || value === '') {
          return this.$t('chartWidget.emptyGroup')
        }
        return String(value)
      })
    },
    /**
     * Charts start from blue rather than the workspace colour: the identity
     * gives blue to the highlighted series, and a theme's accent is chosen for
     * buttons, not data — on a grey theme every chart came out grey.
     */
    palette() {
      return seriesPalette(accentOf(this.widget, 'blue'), 8)
    },
    /**
     * Colours the buckets take when the chart draws one slice per bucket. A
     * single select group by carries its own option colours, which users expect
     * to see again in the chart.
     */
    bucketColors() {
      return this.labels.map(
        (label, index) =>
          resolveOptionColor(this.groups[index]?.color) ||
          this.palette[index % this.palette.length]
      )
    },
    datasets() {
      if (this.groups.length === 0) {
        // No group by: each series contributes one value, so the series
        // themselves become the categories.
        const colors = this.series.map(
          (s, index) =>
            this.seriesColor(s) || this.palette[index % this.palette.length]
        )
        return [
          {
            label: this.widget.title,
            data: this.series.map((s) => toNumber((s.data || [])[0])),
            colors,
          },
        ]
      }
      return this.series.map((s, index) => ({
        label: this.seriesLabel(s),
        data: (s.data || []).map(toNumber),
        colors:
          this.seriesColor(s) || this.palette[index % this.palette.length],
      }))
    },
    chartData() {
      const { lineColor } = chartTheme()
      return {
        labels: this.labels,
        datasets: this.datasets.map((dataset) => {
          const color = dataset.colors
          const base = { label: dataset.label, data: dataset.data }
          if (this.isSliced) {
            return {
              ...base,
              backgroundColor: Array.isArray(color) ? color : this.bucketColors,
              borderColor: '#ffffff',
              borderWidth: 2,
              hoverOffset: 6,
            }
          }
          if (this.chartType === 'line' || this.chartType === 'area') {
            const solid = Array.isArray(color) ? color[0] : color
            const points = this.labels.length <= 16
            return {
              ...base,
              borderColor: solid,
              backgroundColor: withAlpha(solid, this.isStacked ? 0.35 : 0.14),
              pointBackgroundColor: '#ffffff',
              pointBorderColor: solid,
              pointBorderWidth: 2,
              pointRadius: points ? 3 : 0,
              pointHoverRadius: 5,
              borderWidth: 2.5,
              tension: 0.35,
              fill: this.lineFill,
            }
          }
          return {
            ...base,
            backgroundColor: color,
            hoverBackgroundColor: Array.isArray(color)
              ? color.map((c) => withAlpha(c, 0.85))
              : withAlpha(color, 0.85),
            borderRadius: this.isStacked ? 0 : 6,
            borderSkipped: 'start',
            maxBarThickness: 44,
            categoryPercentage: 0.72,
            barPercentage: this.series.length > 1 ? 0.92 : 1,
            borderColor: lineColor,
            borderWidth: 0,
          }
        }),
      }
    },
    /** The first series, one entry per bucket: what a pie or doughnut draws. */
    slices() {
      const data = this.datasets[0]?.data || []
      const total = this.sliceTotal
      const colors = Array.isArray(this.datasets[0]?.colors)
        ? this.datasets[0].colors
        : this.bucketColors
      return this.labels.map((label, index) => ({
        index,
        label,
        value: data[index],
        color: colors[index],
        share:
          total > 0 && data[index] !== null
            ? `${formatNumber((data[index] / total) * 100, {
                locale: this.$i18n.locale,
                decimals: 0,
              })}%`
            : '',
      }))
    },
    sliceTotal() {
      return (this.datasets[0]?.data || []).reduce(
        (sum, value) => sum + (value ?? 0),
        0
      )
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
      const theme = chartTheme()
      const rtl = this.rtl
      const tooltip = {
        rtl,
        textDirection: rtl ? 'rtl' : 'ltr',
        backgroundColor: theme.tooltipBackground,
        titleColor: '#ffffff',
        bodyColor: theme.tooltipText,
        titleFont: { family: theme.fontFamily, size: 12, weight: '600' },
        bodyFont: { family: theme.fontFamily, size: 12 },
        padding: 10,
        cornerRadius: 8,
        boxPadding: 4,
        usePointStyle: true,
        callbacks: {
          label: (context) => {
            const value = this.isSliced
              ? context.parsed
              : this.isHorizontal
                ? context.parsed.x
                : context.parsed.y
            // The tooltip's title already names the category, so one series
            // needs only its value. With several, each part is isolated
            // (U+2068…U+2069) so an English label and an Arabic amount keep
            // their own order instead of running into each other.
            const amount = this.formatValue(value)
            if (!this.isSliced && this.datasets.length === 1) {
              return ` \u2068${amount}\u2069`
            }
            const label = this.isSliced ? context.label : context.dataset.label
            return ` \u2068${label}\u2069: \u2068${amount}\u2069`
          },
        },
      }

      if (this.isSliced) {
        return {
          responsive: true,
          maintainAspectRatio: false,
          cutout: this.chartType === 'doughnut' ? '72%' : 0,
          layout: { padding: 4 },
          plugins: { legend: { display: false }, tooltip },
        }
      }

      const valueAxis = {
        beginAtZero: true,
        stacked: this.isStacked,
        grid: { color: theme.gridColor, drawTicks: false, drawBorder: false },
        ticks: {
          color: theme.tickColor,
          font: { family: theme.fontFamily, size: 11 },
          padding: 8,
          maxTicksLimit: 6,
          // No unit on every tick: the title, legend and tooltip carry it.
          callback: (value) => this.formatValue(value, true, false),
        },
      }
      const categoryAxis = {
        stacked: this.isStacked,
        grid: { display: false, drawBorder: false },
        ticks: {
          color: theme.tickColor,
          font: { family: theme.fontFamily, size: 11 },
          padding: 6,
          maxRotation: 0,
          autoSkipPadding: 12,
          callback(value) {
            return wrapLabel(this.getLabelForValue(value))
          },
        },
      }

      return {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: this.isHorizontal ? 'y' : 'x',
        interaction: { mode: 'index', intersect: false },
        layout: { padding: { top: 4 } },
        plugins: {
          legend: {
            display: this.widget.show_legend && this.datasets.length > 1,
            align: 'end',
            position: 'top',
            rtl,
            textDirection: rtl ? 'rtl' : 'ltr',
            labels: {
              usePointStyle: true,
              pointStyle: 'circle',
              boxWidth: 8,
              boxHeight: 8,
              padding: 14,
              color: theme.labelColor,
              font: { family: theme.fontFamily, size: 12 },
            },
          },
          tooltip,
        },
        scales: this.isHorizontal
          ? {
              x: { ...valueAxis, reverse: rtl },
              y: { ...categoryAxis, position: rtl ? 'right' : 'left' },
            }
          : {
              x: { ...categoryAxis, reverse: rtl },
              y: { ...valueAxis, position: rtl ? 'right' : 'left' },
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
        return riyalText(configured)
      }
      if (!this.$registry.exists('viewAggregation', series.aggregation_type)) {
        return riyalText(series.label)
      }
      const aggregationType = this.$registry.get(
        'viewAggregation',
        series.aggregation_type
      )
      return `${riyalText(series.label)} (${aggregationType.getName()})`
    },
    seriesColor(series) {
      return resolveColor(this.seriesConfig(series).color)
    },
    /**
     * A value as the widget's number options say, compact on axes and in the
     * doughnut's centre where space is short, and without the unit on axes.
     */
    formatValue(value, compactHint = false, withUnit = true) {
      const options = numberFormatOf(this.widget)
      if (!withUnit) {
        options.prefix = ''
        options.suffix = ''
      }
      return (
        formatNumber(value, {
          ...options,
          compact: options.compact || compactHint,
          decimals: compactHint && !options.compact ? null : options.decimals,
          locale: this.$i18n.locale,
        }) ?? '—'
      )
    },
  },
}
</script>
