<template>
  <div>
    <AggregateRowsDataSourceForm
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
      :features="['icon', 'color', 'number']"
    />
  </div>
</template>

<script>
import AggregateRowsDataSourceForm from '@jadawel/modules/dashboard/components/data_source/AggregateRowsDataSourceForm'
import WidgetAppearanceForm from '@jadawel/modules/arabase/dashboard/components/widget/WidgetAppearanceForm'
import dashboardWidgetSettings from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidgetSettings'

/**
 * Settings of the key-number (`summary`) widget: upstream's aggregation form,
 * then how the number looks.
 */
export default {
  name: 'KpiWidgetSettings',
  components: { AggregateRowsDataSourceForm, WidgetAppearanceForm },
  mixins: [dashboardWidgetSettings],
}
</script>
