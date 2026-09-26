<template>
  <form @submit.prevent>
    <FormSection
      :title="$t('groupedAggregateRowsDataSourceForm.data')"
      class="margin-bottom-2"
    >
      <FormGroup
        :label="$t('groupedAggregateRowsDataSourceForm.sourceFieldLabel')"
        class="margin-bottom-2"
        small-label
        required
        horizontal
        horizontal-narrow
      >
        <Dropdown
          v-model="computedTableId"
          :show-search="true"
          fixed-items
          :error="fieldHasErrors('table_id')"
        >
          <DropdownSection
            v-for="database in databases"
            :key="database.id"
            :title="`${database.name} (${database.id})`"
          >
            <DropdownItem
              v-for="table in database.tables"
              :key="table.id"
              :name="table.name"
              :value="table.id"
              :indented="true"
            >
              {{ table.name }}
            </DropdownItem>
          </DropdownSection>
        </Dropdown>
      </FormGroup>

      <FormGroup
        v-if="values.table_id && !fieldHasErrors('table_id')"
        :label="$t('groupedAggregateRowsDataSourceForm.viewFieldLabel')"
        class="margin-bottom-2"
        small-label
        horizontal
        horizontal-narrow
      >
        <Dropdown
          v-model="values.view_id"
          :show-search="false"
          fixed-items
          :disabled="fieldsLoading"
        >
          <DropdownItem
            :name="$t('groupedAggregateRowsDataSourceForm.notSelected')"
            :value="null"
            >{{
              $t('groupedAggregateRowsDataSourceForm.notSelected')
            }}</DropdownItem
          >
          <DropdownItem
            v-for="view in tableViews"
            :key="view.id"
            :name="view.name"
            :value="view.id"
          >
            {{ view.name }}
          </DropdownItem>
        </Dropdown>
      </FormGroup>

      <FormGroup
        v-if="values.table_id && !fieldHasErrors('table_id')"
        :label="$t('groupedAggregateRowsDataSourceForm.groupByLabel')"
        :helper-text="$t('groupedAggregateRowsDataSourceForm.groupByHelp')"
        class="margin-bottom-2"
        small-label
        horizontal
        horizontal-narrow
      >
        <Dropdown
          v-model="groupByFieldId"
          :disabled="tableFields.length === 0 || fieldsLoading"
        >
          <DropdownItem
            :name="$t('groupedAggregateRowsDataSourceForm.noGroupBy')"
            :value="null"
            >{{
              $t('groupedAggregateRowsDataSourceForm.noGroupBy')
            }}</DropdownItem
          >
          <DropdownItem
            v-for="field in tableFields"
            :key="field.id"
            :name="field.name"
            :value="field.id"
            :icon="fieldIconClass(field)"
          >
          </DropdownItem>
        </Dropdown>
      </FormGroup>
    </FormSection>

    <FormSection
      v-if="values.table_id && !fieldHasErrors('table_id')"
      :title="$t('groupedAggregateRowsDataSourceForm.series')"
    >
      <div
        v-for="(series, index) in values.aggregation_series"
        :key="`series-${index}`"
        class="grouped-aggregate-series"
      >
        <FormGroup
          class="margin-bottom-1"
          small-label
          :label="$t('groupedAggregateRowsDataSourceForm.seriesFieldLabel')"
          required
          horizontal
          horizontal-narrow
        >
          <Dropdown
            :model-value="series.field_id"
            :disabled="tableFields.length === 0 || fieldsLoading"
            @update:model-value="setSeriesField(index, $event)"
          >
            <DropdownItem
              v-for="field in tableFields"
              :key="field.id"
              :name="field.name"
              :value="field.id"
              :icon="fieldIconClass(field)"
            >
            </DropdownItem>
          </Dropdown>
        </FormGroup>
        <FormGroup
          class="margin-bottom-1"
          small-label
          :label="$t('groupedAggregateRowsDataSourceForm.aggregationTypeLabel')"
          required
          horizontal
          horizontal-narrow
        >
          <Dropdown
            :model-value="series.aggregation_type"
            :disabled="fieldsLoading"
            @update:model-value="setSeriesAggregationType(index, $event)"
          >
            <DropdownItem
              v-for="aggregation in aggregationTypesForField(series.field_id)"
              :key="aggregation.getType()"
              :name="aggregation.getName()"
              :value="aggregation.getType()"
              :disabled="
                unsupportedAggregationTypes.includes(aggregation.getType())
              "
            >
            </DropdownItem>
          </Dropdown>
        </FormGroup>
        <ButtonText
          v-if="values.aggregation_series.length > 1"
          icon="iconoir-bin"
          type="secondary"
          class="margin-bottom-2"
          @click="removeSeries(index)"
          >{{
            $t('groupedAggregateRowsDataSourceForm.removeSeries')
          }}</ButtonText
        >
      </div>

      <ButtonText v-if="canAddSeries" icon="iconoir-plus" @click="addSeries">{{
        $t('groupedAggregateRowsDataSourceForm.addSeries')
      }}</ButtonText>
      <div v-else class="grouped-aggregate-series__limit">
        {{
          $t('groupedAggregateRowsDataSourceForm.seriesLimit', {
            count: maxSeries,
          })
        }}
      </div>
    </FormSection>
  </form>
</template>

<script>
import { useVuelidate } from '@vuelidate/core'
import { required } from '@vuelidate/validators'
import dashboardTableSourceForm from '@jadawel/modules/arabase/dashboard/mixins/dashboardTableSourceForm'

// The backend accepts more; three is what fits the settings panel and stays
// readable in one chart.
const MAX_SERIES = 3

const includes = (array) => (value) => array.includes(value)

export default {
  name: 'GroupedAggregateRowsDataSourceForm',
  mixins: [dashboardTableSourceForm],
  setup() {
    return { v$: useVuelidate({ $lazy: true }) }
  },
  data() {
    return {
      allowedValues: [
        'table_id',
        'view_id',
        'aggregation_series',
        'aggregation_group_bys',
      ],
      values: {
        table_id: null,
        view_id: null,
        aggregation_series: [],
        aggregation_group_bys: [],
      },
      skipFirstValuesEmit: true,
      tableIdHasChanged: false,
    }
  },
  computed: {
    maxSeries() {
      return MAX_SERIES
    },
    canAddSeries() {
      return this.values.aggregation_series.length < MAX_SERIES
    },
    /**
     * The API models group bys as a list so a second level can be added later;
     * the form exposes the one v1 supports as a plain field id.
     */
    groupByFieldId: {
      get() {
        return this.values.aggregation_group_bys[0]?.field_id ?? null
      },
      set(fieldId) {
        this.values.aggregation_group_bys =
          fieldId === null ? [] : [{ field_id: fieldId }]
      },
    },
    unsupportedAggregationTypes() {
      return this.$registry.get(
        'service',
        'local_jadawel_grouped_aggregate_rows'
      ).unsupportedAggregationTypes
    },
  },
  watch: {
    fieldsLoading(loading) {
      if (this.tableIdHasChanged && !loading) {
        // A chart with no series renders nothing, so picking a table seeds one
        // rather than leaving an empty widget behind.
        if (this.tableFields.length > 0) {
          this.values.aggregation_series = [
            this.newSeries(this.tableFields[0].id),
          ]
        }
        this.tableIdHasChanged = false
      }
    },
  },
  validations() {
    return {
      values: {
        table_id: {
          required,
          isValidTableId: (value) => includes(this.tableIds)(value),
        },
      },
    }
  },
  methods: {
    onTableChanged() {
      this.tableIdHasChanged = true
      // Views, series and group bys all reference fields on the table that
      // was just replaced.
      this.values.view_id = null
      this.values.aggregation_series = []
      this.values.aggregation_group_bys = []
    },
    fieldIconClass(field) {
      return this.$registry.get('field', field.type).iconClass
    },
    aggregationTypesForField(fieldId) {
      const field = this.tableFields.find(({ id }) => id === fieldId)
      if (!field) {
        return []
      }
      return this.$registry
        .getOrderedList('viewAggregation')
        .filter((aggregation) => aggregation.fieldIsCompatible(field))
    },
    newSeries(fieldId) {
      const compatible = this.aggregationTypesForField(fieldId).filter(
        (aggregation) =>
          !this.unsupportedAggregationTypes.includes(aggregation.getType())
      )
      return {
        field_id: fieldId,
        aggregation_type: compatible[0]?.getType() || '',
      }
    },
    addSeries() {
      if (!this.canAddSeries || this.tableFields.length === 0) {
        return
      }
      this.values.aggregation_series = [
        ...this.values.aggregation_series,
        this.newSeries(this.tableFields[0].id),
      ]
    },
    removeSeries(index) {
      this.values.aggregation_series = this.values.aggregation_series.filter(
        (_, i) => i !== index
      )
    },
    setSeriesField(index, fieldId) {
      this.values.aggregation_series = this.values.aggregation_series.map(
        (series, i) => {
          if (i !== index) {
            return series
          }
          // The previous aggregation type may not apply to the new field, so it
          // falls back to the first compatible one.
          const stillCompatible = this.aggregationTypesForField(fieldId).some(
            (aggregation) => aggregation.getType() === series.aggregation_type
          )
          return stillCompatible
            ? { ...series, field_id: fieldId }
            : this.newSeries(fieldId)
        }
      )
    },
    setSeriesAggregationType(index, aggregationType) {
      this.values.aggregation_series = this.values.aggregation_series.map(
        (series, i) =>
          i === index
            ? { ...series, aggregation_type: aggregationType }
            : series
      )
    },
  },
}
</script>
