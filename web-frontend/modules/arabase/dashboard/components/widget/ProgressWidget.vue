<template>
  <div class="dashboard-progress-widget">
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

      <div class="widget__content dashboard-progress-widget__body">
        <div
          v-if="dataSourceMisconfigured"
          class="dashboard-progress-widget__empty"
        >
          {{ $t('progressWidget.misconfigured') }}
        </div>

        <!-- Ring -->
        <div v-else-if="isRing" class="dashboard-progress-widget__ring-wrapper">
          <svg class="dashboard-progress-widget__ring" viewBox="0 0 42 42">
            <circle
              class="dashboard-progress-widget__ring-track"
              cx="21"
              cy="21"
              r="15.9"
              fill="none"
              stroke-width="4"
            />
            <circle
              class="dashboard-progress-widget__ring-value"
              :class="stateClass"
              cx="21"
              cy="21"
              r="15.9"
              fill="none"
              stroke-width="4"
              stroke-linecap="round"
              :stroke-dasharray="`${dashLength} ${circumference}`"
              transform="rotate(-90 21 21)"
            />
          </svg>
          <div class="dashboard-progress-widget__ring-label">
            <div
              class="dashboard-progress-widget__percentage"
              :class="stateClass"
            >
              {{ percentageLabel }}
            </div>
          </div>
        </div>

        <!-- Bar -->
        <template v-else>
          <div
            class="dashboard-progress-widget__percentage"
            :class="stateClass"
          >
            {{ percentageLabel }}
          </div>
          <div class="dashboard-progress-widget__track">
            <div
              class="dashboard-progress-widget__fill"
              :class="stateClass"
              :style="{ width: `${cappedPercentage}%` }"
            ></div>
          </div>
        </template>

        <div class="dashboard-progress-widget__values">
          {{
            $t('progressWidget.ofTarget', {
              value: resultLabel,
              target: targetLabel,
            })
          }}
        </div>
      </div>
    </template>
    <div
      v-else
      class="dashboard-progress-widget__loading loading-spinner"
    ></div>
  </div>
</template>

<script>
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'
import WidgetContextMenu from '@jadawel/modules/dashboard/components/widget/WidgetContextMenu'

// r=15.9 in a 42-unit viewBox, so the ring's stroke fits inside without clipping.
const RING_CIRCUMFERENCE = 2 * Math.PI * 15.9

export default {
  name: 'ProgressWidget',
  components: { WidgetContextMenu },
  mixins: [dashboardWidget],
  emits: ['delete-widget'],
  computed: {
    isRing() {
      return this.widget.display_style === 'ring'
    },
    circumference() {
      return RING_CIRCUMFERENCE
    },
    /**
     * The aggregation arrives serialized by its field type, so a number field
     * gives back a string. Parsing it here rather than trusting the type keeps a
     * non-numeric aggregation (an empty table, say) from rendering as NaN%.
     */
    result() {
      const raw = this.dataForDataSource?.result
      const parsed = Number.parseFloat(raw)
      return Number.isFinite(parsed) ? parsed : null
    },
    target() {
      const parsed = Number.parseFloat(this.widget.target_value)
      // The API rejects a target of zero, but a widget imported from elsewhere or
      // edited through the API could still carry one, and dividing by it would
      // render Infinity%.
      return Number.isFinite(parsed) && parsed > 0 ? parsed : null
    },
    percentage() {
      if (this.result === null || this.target === null) {
        return 0
      }
      return (this.result / this.target) * 100
    },
    cappedPercentage() {
      // Overshooting the target is worth stating in the number but cannot be
      // drawn: a bar wider than its track escapes the widget.
      return Math.max(0, Math.min(100, this.percentage))
    },
    percentageLabel() {
      if (this.result === null || this.target === null) {
        return '—'
      }
      return `${Math.round(this.percentage)}%`
    },
    dashLength() {
      return (this.cappedPercentage / 100) * RING_CIRCUMFERENCE
    },
    stateClass() {
      if (this.result === null || this.target === null) {
        return 'dashboard-progress-widget--neutral'
      }
      if (this.percentage >= this.widget.success_threshold) {
        return 'dashboard-progress-widget--success'
      }
      if (this.percentage >= this.widget.warning_threshold) {
        return 'dashboard-progress-widget--warning'
      }
      return 'dashboard-progress-widget--danger'
    },
    /**
     * The formatted aggregation, so a currency or duration field reads the way it
     * does everywhere else. The service type owns that formatting.
     */
    resultLabel() {
      const data = this.dataForDataSource
      if (this.dataSource && data && data.result !== undefined) {
        const serviceType = this.$registry.get('service', this.dataSource.type)
        return serviceType.getResult(this.dataSource, data)
      }
      return '—'
    },
    targetLabel() {
      if (this.target === null) {
        return '—'
      }
      // `toLocaleString` rather than vue-i18n's `$n`, which needs number formats
      // declared per locale; this only has to group thousands.
      return this.target.toLocaleString(this.$i18n.locale)
    },
  },
}
</script>
