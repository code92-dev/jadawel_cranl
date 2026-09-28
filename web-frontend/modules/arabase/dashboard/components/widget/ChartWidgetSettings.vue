<template>
  <div>
    <GroupedAggregateRowsDataSourceForm
      v-if="dataSource"
      ref="dataSourceForm"
      :dashboard="dashboard"
      :widget="widget"
      :data-source="dataSource"
      :default-values="dataSource"
      :store-prefix="storePrefix"
      @values-changed="onDataSourceValuesChanged"
    />

    <WidgetAppearanceForm
      :widget="widget"
      :store-prefix="storePrefix"
      :features="appearanceFeatures"
      default-color="blue"
    >
      <FormGroup
        :label="$t('chartWidgetSettings.chartType')"
        class="margin-bottom-2"
        small-label
        required
      >
        <div class="widget-chart-types" role="radiogroup">
          <button
            v-for="type in chartTypes"
            :key="type.value"
            type="button"
            role="radio"
            class="widget-chart-types__option"
            :class="{
              'widget-chart-types__option--active': type.value === chartType,
            }"
            :aria-checked="type.value === chartType ? 'true' : 'false'"
            :title="type.name"
            @click="chartType = type.value"
          >
            <i :class="type.icon" aria-hidden="true"></i>
            <span>{{ type.name }}</span>
          </button>
        </div>
      </FormGroup>
      <FormGroup small-label class="margin-bottom-2">
        <Checkbox v-model="showLegend">{{
          $t('chartWidgetSettings.showLegend')
        }}</Checkbox>
      </FormGroup>
    </WidgetAppearanceForm>
  </div>
</template>

<script>
import GroupedAggregateRowsDataSourceForm from '@jadawel/modules/arabase/dashboard/components/data_source/GroupedAggregateRowsDataSourceForm'
import WidgetAppearanceForm from '@jadawel/modules/arabase/dashboard/components/widget/WidgetAppearanceForm'
import dashboardWidgetSettings from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidgetSettings'
import { CHART_TYPES } from '@jadawel/modules/arabase/dashboard/widgetTypes'

export default {
  name: 'ChartWidgetSettings',
  components: { GroupedAggregateRowsDataSourceForm, WidgetAppearanceForm },
  mixins: [dashboardWidgetSettings],
  computed: {
    chartTypes() {
      return CHART_TYPES.map((type) => ({
        value: type.value,
        icon: type.icon,
        name: this.$t(type.nameKey),
      }))
    },
    chartType: {
      get() {
        return this.widget.chart_type
      },
      set(value) {
        if (value !== this.widget.chart_type) {
          this.updateWidget({ chart_type: value })
        }
      },
    },
    showLegend: {
      get() {
        return this.widget.show_legend
      },
      set(value) {
        this.updateWidget({ show_legend: value })
      },
    },
    appearanceFeatures() {
      const sliced = ['pie', 'doughnut'].includes(this.widget.chart_type)
      return sliced ? ['color', 'number'] : ['color', 'number', 'stacked']
    },
  },
}
</script>
