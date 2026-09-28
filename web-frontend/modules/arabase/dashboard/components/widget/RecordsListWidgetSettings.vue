<template>
  <div>
    <form v-if="dataSource" class="margin-bottom-2" @submit.prevent>
      <FormSection :title="$t('recordsListWidgetSettings.display')">
        <DisplayedFieldsFormGroup
          :model-value="widget.field_ids"
          :fields="tableFields"
          @update:model-value="updateWidget({ field_ids: $event })"
        />
      </FormSection>
    </form>

    <ListRowsDataSourceForm
      v-if="dataSource"
      ref="dataSourceForm"
      :dashboard="dashboard"
      :widget="widget"
      :data-source="dataSource"
      :default-values="dataSource"
      :store-prefix="storePrefix"
      @values-changed="onDataSourceValuesChanged"
    />

    <WidgetAppearanceForm :widget="widget" :store-prefix="storePrefix" />
  </div>
</template>

<script>
import DisplayedFieldsFormGroup from '@jadawel/modules/arabase/dashboard/components/data_source/DisplayedFieldsFormGroup'
import ListRowsDataSourceForm from '@jadawel/modules/arabase/dashboard/components/data_source/ListRowsDataSourceForm'
import WidgetAppearanceForm from '@jadawel/modules/arabase/dashboard/components/widget/WidgetAppearanceForm'
import dashboardWidgetSettings from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidgetSettings'
import tableFields from '@jadawel/modules/database/mixins/tableFields'

export default {
  name: 'RecordsListWidgetSettings',
  components: {
    DisplayedFieldsFormGroup,
    ListRowsDataSourceForm,
    WidgetAppearanceForm,
  },
  mixins: [dashboardWidgetSettings, tableFields],
  methods: {
    /**
     * Overrides the method in the tableFields mixin.
     *
     * The field picker needs each field's type for its icon, which the data
     * source schema does not carry — so the real fields are loaded rather than
     * derived from the schema.
     */
    getTableId() {
      return this.dataSource?.table_id || null
    },
  },
}
</script>
