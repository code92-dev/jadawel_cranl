<template>
  <div class="chart">
    <div class="chart__title">{{ title }}</div>

    <div
      v-if="series.length"
      ref="plot"
      class="chart__plot"
      tabindex="0"
      role="img"
      :aria-label="summary"
      @pointermove="onPointerMove"
      @pointerleave="onPointerLeave"
      @focus="focusIndex(series.length - 1)"
      @blur="onPointerLeave"
      @keydown.left.prevent="stepFocus(-1)"
      @keydown.right.prevent="stepFocus(1)"
    >
      <svg
        class="chart__svg"
        :viewBox="`0 0 ${width} ${height}`"
        :width="width"
        :height="height"
        aria-hidden="true"
        focusable="false"
      >
        <line
          v-for="line in gridLines"
          :key="line"
          class="chart__grid"
          x1="0"
          :y1="line"
          :x2="width"
          :y2="line"
        />
        <path class="chart__area" :d="areaPath" />
        <path class="chart__line" :d="linePath" />
        <circle
          v-if="activePoint"
          class="chart__marker"
          :cx="activePoint.x"
          :cy="activePoint.y"
          r="4.5"
        />
        <circle
          v-else-if="lastPoint"
          class="chart__marker"
          :cx="lastPoint.x"
          :cy="lastPoint.y"
          r="4.5"
        />
        <line
          v-if="activePoint"
          class="chart__crosshair"
          :x1="activePoint.x"
          y1="0"
          :x2="activePoint.x"
          :y2="height"
        />
      </svg>

      <div
        v-if="activePoint"
        class="chart__tooltip"
        :style="{ left: activePoint.x + 'px' }"
      >
        <div class="chart__tooltip-value">
          {{ formatValue(activePoint.point.count) }}
        </div>
        <div class="chart__tooltip-label">
          {{ formatDate(activePoint.point.date) }}
        </div>
      </div>
    </div>

    <div v-else class="chart__empty">{{ emptyMessage }}</div>

    <!--
      The time axis reads left to right even in Arabic. Mirroring a time series
      is a well known source of misreading, and Arabic-language dashboards
      overwhelmingly keep time flowing this way; it is the one element on this
      page that deliberately does not follow the page direction.
    -->
    <div v-if="series.length" class="chart__axis">
      <span>{{ formatDate(series[0].date) }}</span>
      <span>{{ formatDate(series[series.length - 1].date) }}</span>
    </div>

    <!--
      The bar chart renders every value as text, so it needs no table. This one
      plots thirty points that exist only as path geometry, so the values are
      given to assistive technology here.
    -->
    <!--
      Hidden by a wrapper because a table ignores the 1px box: hidden on itself,
      its thirty rows still stretched the page below the bottom of the window.
    -->
    <div v-if="series.length" class="chart__sr-only">
      <table>
        <caption>
          {{
            title
          }}
        </caption>
        <thead>
          <tr>
            <th scope="col">{{ $t('dashboardCharts.date') }}</th>
            <th scope="col">{{ $t('dashboardCharts.rowsAdded') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="point in series" :key="point.date">
            <th scope="row">{{ formatDate(point.date) }}</th>
            <td>{{ formatValue(point.count) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
const HEIGHT = 96
// Leaves room for the 4.5px marker and its 2px surface ring at the extremes, so
// a peak or a zero is never clipped by the viewBox edge.
const PADDING = 8

export default {
  name: 'DashboardAreaChart',
  props: {
    title: {
      type: String,
      required: true,
    },
    /**
     * `[{ date, count }]`, dense and oldest first. Density matters: a sparse
     * series would draw a straight line across a quiet week, which reads as
     * steady activity rather than none.
     */
    series: {
      type: Array,
      required: true,
    },
    emptyMessage: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      // Real pixel width, observed rather than assumed. Scaling a fixed viewBox
      // with `preserveAspectRatio="none"` would stretch the marker into an
      // ellipse and make the hover maths lie about where points are.
      width: 300,
      height: HEIGHT,
      activeIndex: null,
      resizeObserver: null,
    }
  },
  computed: {
    points() {
      if (!this.series.length) {
        return []
      }

      const max = Math.max(...this.series.map((point) => point.count), 0)
      const usable = this.height - PADDING * 2
      const step =
        this.series.length > 1
          ? (this.width - PADDING * 2) / (this.series.length - 1)
          : 0

      return this.series.map((point, index) => ({
        point,
        index,
        x: PADDING + step * index,
        // An all-zero window sits on the baseline rather than dividing by zero.
        y: this.height - PADDING - (max > 0 ? (point.count / max) * usable : 0),
      }))
    },
    linePath() {
      return this.points
        .map(
          (p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(2)} ${p.y.toFixed(2)}`
        )
        .join(' ')
    },
    areaPath() {
      if (!this.points.length) {
        return ''
      }
      const base = this.height - PADDING
      const last = this.points[this.points.length - 1]
      const first = this.points[0]
      return `${this.linePath} L${last.x.toFixed(2)} ${base} L${first.x.toFixed(
        2
      )} ${base} Z`
    },
    gridLines() {
      const base = this.height - PADDING
      return [base, PADDING + (base - PADDING) / 2]
    },
    lastPoint() {
      return this.points.length ? this.points[this.points.length - 1] : null
    },
    activePoint() {
      return this.activeIndex === null ? null : this.points[this.activeIndex]
    },
    summary() {
      const total = this.series.reduce((sum, point) => sum + point.count, 0)
      return this.$t('dashboardCharts.activitySummary', {
        total: this.formatValue(total),
        days: this.formatValue(this.series.length),
      })
    },
  },
  mounted() {
    this.measure()
    if (typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => this.measure())
      if (this.$refs.plot) {
        this.resizeObserver.observe(this.$refs.plot)
      }
    }
  },
  beforeUnmount() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
      this.resizeObserver = null
    }
  },
  methods: {
    measure() {
      const element = this.$refs.plot
      if (element && element.clientWidth > 0) {
        this.width = element.clientWidth
      }
    },
    onPointerMove(event) {
      if (!this.points.length) {
        return
      }
      const rect = this.$refs.plot.getBoundingClientRect()
      const x = event.clientX - rect.left
      // Nearest point rather than the one under the cursor: the hit target is
      // the whole column, so there is no dead space between marks.
      let nearest = 0
      let best = Infinity
      this.points.forEach((point) => {
        const distance = Math.abs(point.x - x)
        if (distance < best) {
          best = distance
          nearest = point.index
        }
      })
      this.activeIndex = nearest
    },
    onPointerLeave() {
      this.activeIndex = null
    },
    focusIndex(index) {
      this.activeIndex = index
    },
    stepFocus(delta) {
      if (!this.points.length) {
        return
      }
      const current =
        this.activeIndex === null ? this.points.length - 1 : this.activeIndex
      this.activeIndex = Math.min(
        Math.max(current + delta, 0),
        this.points.length - 1
      )
    },
    formatValue(value) {
      return new Intl.NumberFormat(this.$i18n.locale).format(value)
    },
    formatDate(iso) {
      // Parsed as parts rather than `new Date(iso)`: an ISO date string is UTC
      // midnight, which lands on the previous day for anyone behind UTC.
      const [year, month, day] = iso.split('-').map(Number)
      return new Intl.DateTimeFormat(this.$i18n.locale, {
        day: 'numeric',
        month: 'short',
      }).format(new Date(year, month - 1, day))
    },
  },
}
</script>
