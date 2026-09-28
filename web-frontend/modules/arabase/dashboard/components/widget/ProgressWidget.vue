<template>
  <WidgetFrame
    :widget="widget"
    :loading="loading"
    :edit-mode="isEditMode"
    :misconfigured="dataSourceMisconfigured"
    :misconfigured-message="$t('progressWidget.misconfigured')"
  >
    <template #badges>
      <span
        v-if="status"
        class="widget-status"
        :class="`widget-status--${status.tone}`"
      >
        <i :class="status.icon" aria-hidden="true"></i>
        {{ status.label }}
      </span>
    </template>

    <div
      class="widget-progress"
      :class="[`widget-progress--${displayStyle}`, `widget-tone--${tone}`]"
    >
      <!-- Ring: a full circle around the percentage. -->
      <template v-if="displayStyle === 'ring'">
        <div class="widget-progress__dial">
          <svg class="widget-progress__svg" viewBox="0 0 42 42" role="img">
            <title>{{ percentageLabel }}</title>
            <circle
              class="widget-progress__track"
              cx="21"
              cy="21"
              r="16"
              pathLength="100"
            />
            <circle
              class="widget-progress__arc"
              cx="21"
              cy="21"
              r="16"
              pathLength="100"
              :stroke-dasharray="`${cappedPercentage} 100`"
              transform="rotate(-90 21 21)"
            />
          </svg>
          <div class="widget-progress__dial-label">{{ percentageLabel }}</div>
        </div>
        <div class="widget-progress__values">
          <div class="widget-progress__value">{{ valueLabel }}</div>
          <div class="widget-progress__target">
            {{ $t('progressWidget.target', { target: targetLabel }) }}
          </div>
        </div>
      </template>

      <!-- Gauge: a half dial, the needle's end on the arc. -->
      <template v-else-if="displayStyle === 'gauge'">
        <div class="widget-progress__dial">
          <svg class="widget-progress__svg" viewBox="0 0 48 27" role="img">
            <title>{{ percentageLabel }}</title>
            <path
              class="widget-progress__track"
              d="M 4 24 A 20 20 0 0 1 44 24"
              pathLength="100"
            />
            <path
              class="widget-progress__arc"
              d="M 4 24 A 20 20 0 0 1 44 24"
              pathLength="100"
              :stroke-dasharray="`${cappedPercentage} 100`"
            />
          </svg>
          <div class="widget-progress__dial-label">{{ percentageLabel }}</div>
        </div>
        <div class="widget-progress__values">
          <div class="widget-progress__value">{{ valueLabel }}</div>
          <div class="widget-progress__target">
            {{ $t('progressWidget.target', { target: targetLabel }) }}
          </div>
        </div>
      </template>

      <!-- Bar -->
      <template v-else>
        <div class="widget-progress__headline">
          <span class="widget-progress__percentage">{{ percentageLabel }}</span>
          <span class="widget-progress__of">{{
            $t('progressWidget.ofTarget', {
              value: valueLabel,
              target: targetLabel,
            })
          }}</span>
        </div>
        <div
          class="widget-progress__bar"
          role="progressbar"
          :aria-valuenow="Math.round(cappedPercentage)"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div
            class="widget-progress__fill"
            :style="{ inlineSize: `${cappedPercentage}%` }"
          ></div>
          <span
            v-for="mark in marks"
            :key="mark.value"
            class="widget-progress__mark"
            :style="{ insetInlineStart: `${mark.value}%` }"
            :title="mark.label"
          ></span>
        </div>
      </template>
    </div>
  </WidgetFrame>
</template>

<script>
import WidgetFrame from '@jadawel/modules/arabase/dashboard/components/widget/WidgetFrame'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'
import { numberFormatOf } from '@jadawel/modules/arabase/dashboard/appearance'
import {
  formatAggregate,
  formatNumber,
  toNumber,
} from '@jadawel/modules/arabase/dashboard/format'

const STATUS = {
  success: { icon: 'iconoir-check-circle', key: 'met' },
  warning: { icon: 'iconoir-clock', key: 'onTrack' },
  danger: { icon: 'iconoir-warning-triangle', key: 'atRisk' },
}

export default {
  name: 'ProgressWidget',
  components: { WidgetFrame },
  mixins: [dashboardWidget],
  emits: ['delete-widget'],
  computed: {
    displayStyle() {
      return ['ring', 'gauge'].includes(this.widget.display_style)
        ? this.widget.display_style
        : 'bar'
    },
    /**
     * The aggregation arrives serialized by its field type, so a number field
     * gives back a string. Parsing it rather than trusting the type keeps a
     * non-numeric aggregation (an empty table, say) from rendering as NaN%.
     */
    result() {
      return toNumber(this.dataForDataSource?.result)
    },
    target() {
      const parsed = toNumber(this.widget.target_value)
      // The API rejects a target of zero, but a widget imported from elsewhere
      // could still carry one, and dividing by it would render Infinity%.
      return parsed !== null && parsed > 0 ? parsed : null
    },
    hasValue() {
      return this.result !== null && this.target !== null
    },
    percentage() {
      return this.hasValue ? (this.result / this.target) * 100 : 0
    },
    cappedPercentage() {
      // Overshooting the target is worth stating in the number but cannot be
      // drawn: a fill wider than its track escapes the widget.
      return Math.max(0, Math.min(100, this.percentage))
    },
    percentageLabel() {
      if (!this.hasValue) {
        return '—'
      }
      return `${formatNumber(Math.round(this.percentage), {
        locale: this.$i18n.locale,
      })}%`
    },
    tone() {
      if (!this.hasValue) {
        return 'neutral'
      }
      if (this.percentage >= this.widget.success_threshold) {
        return 'success'
      }
      if (this.percentage >= this.widget.warning_threshold) {
        return 'warning'
      }
      return 'danger'
    },
    /**
     * The state in words and an icon as well as a colour, so it reads without
     * colour vision and in a screenshot printed in grey.
     */
    status() {
      const status = STATUS[this.tone]
      if (!status) {
        return null
      }
      return {
        tone: this.tone,
        icon: status.icon,
        label: this.$t(`progressWidget.status.${status.key}`),
      }
    },
    numberOptions() {
      return { ...numberFormatOf(this.widget), locale: this.$i18n.locale }
    },
    /**
     * The aggregation as the rest of Jadawel prints it — a currency or duration
     * keeps its own formatting — with the widget's number options on a plain
     * number.
     */
    valueLabel() {
      const data = this.dataForDataSource
      if (!this.dataSource || !data || data.result === undefined) {
        return '—'
      }
      const serviceType = this.$registry.get('service', this.dataSource.type)
      const formatted = serviceType.getResult(this.dataSource, data)
      return formatAggregate(data.result, formatted, this.numberOptions) ?? '—'
    },
    targetLabel() {
      return this.target === null
        ? '—'
        : formatNumber(this.target, this.numberOptions)
    },
    /** Where "at risk" ends on the bar, so the thresholds can be seen. */
    marks() {
      const warning = Number(this.widget.warning_threshold)
      if (!Number.isFinite(warning) || warning <= 0 || warning >= 100) {
        return []
      }
      return [
        {
          value: warning,
          label: this.$t('progressWidget.warningMark', { value: warning }),
        },
      ]
    },
  },
}
</script>
