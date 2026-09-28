<template>
  <WidgetFrame
    :widget="widget"
    :loading="loading"
    :edit-mode="isEditMode"
    :misconfigured="dataSourceMisconfigured"
    :misconfigured-message="$t('kpiWidget.misconfigured')"
  >
    <div class="widget-kpi">
      <div
        class="widget-kpi__value"
        :class="{ 'widget-kpi__value--empty': display === null }"
        :style="{ '--kpi-characters': characters }"
        :title="display ?? ''"
      >
        {{ display ?? '—' }}
      </div>
      <div v-if="caption" class="widget-kpi__caption">{{ caption }}</div>
    </div>
  </WidgetFrame>
</template>

<script>
import WidgetFrame from '@jadawel/modules/arabase/dashboard/components/widget/WidgetFrame'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'
import { numberFormatOf } from '@jadawel/modules/arabase/dashboard/appearance'
import {
  formatAggregate,
  riyalText,
} from '@jadawel/modules/arabase/dashboard/format'

/**
 * The key-number widget: upstream's `summary` type, drawn by the fork.
 *
 * The aggregation's own formatter still decides how a currency, a duration or a
 * date reads; a plain number is formatted here with thousands separators and the
 * widget's decimals, compact notation and unit. The size of the number follows
 * the widget's size (container query units in `dashboard_widgets.scss`), so a
 * quarter-width card and a half-width one both read well.
 */
export default {
  name: 'KpiWidget',
  components: { WidgetFrame },
  mixins: [dashboardWidget],
  emits: ['delete-widget'],
  computed: {
    display() {
      const data = this.dataForDataSource
      if (!this.dataSource || !data || data.result === undefined) {
        return null
      }
      const serviceType = this.$registry.get('service', this.dataSource.type)
      const formatted = serviceType.getResult(this.dataSource, data)
      return formatAggregate(data.result, formatted, {
        ...numberFormatOf(this.widget),
        locale: this.$i18n.locale,
      })
    },
    /**
     * How many characters the number takes, so its size can shrink for a long
     * one ("1.6 مليون ر.س") rather than being cut off. Short numbers are capped
     * by the card's height instead.
     */
    characters() {
      return Math.max(4, (this.display ?? '—').length)
    },
    /**
     * "Sum of Budget" under the number, when the widget has no description to
     * say what it counts. The public dashboard carries no field names, so it
     * stays blank there.
     */
    caption() {
      if (this.widget.description) {
        return null
      }
      const field = this.dataSource?.context_data?.field
      const aggregation = this.dataSource?.aggregation_type
      if (!field?.name || !aggregation) {
        return null
      }
      const type = this.$registry.exists('viewAggregation', aggregation)
        ? this.$registry.get('viewAggregation', aggregation)
        : null
      return type
        ? this.$t('kpiWidget.caption', {
            aggregation: type.getName(),
            field: riyalText(field.name),
          })
        : null
    },
  },
}
</script>
