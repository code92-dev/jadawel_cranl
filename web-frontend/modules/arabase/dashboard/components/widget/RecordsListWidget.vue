<template>
  <div class="dashboard-records-list-widget">
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
      <div class="widget__content dashboard-records-list-widget__body">
        <div v-if="!hasRows" class="dashboard-records-list-widget__empty">
          {{
            dataSourceMisconfigured
              ? $t('recordsListWidget.misconfigured')
              : $t('recordsListWidget.noRecords')
          }}
        </div>
        <RecordRows v-else :rows="rows" :fields="fields" />
      </div>
    </template>
    <div
      v-else
      class="dashboard-records-list-widget__loading loading-spinner"
    ></div>
  </div>
</template>

<script>
import RecordRows from '@jadawel/modules/arabase/dashboard/components/widget/RecordRows'
import { resolveDisplayedFields } from '@jadawel/modules/arabase/dashboard/recordValues'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'
import WidgetContextMenu from '@jadawel/modules/dashboard/components/widget/WidgetContextMenu'

export default {
  name: 'RecordsListWidget',
  components: { RecordRows, WidgetContextMenu },
  mixins: [dashboardWidget],
  emits: ['delete-widget'],
  computed: {
    rows() {
      return this.dataForDataSource?.results || []
    },
    hasRows() {
      return this.rows.length > 0 && this.fields.length > 0
    },
    fields() {
      return resolveDisplayedFields(this.dataSource, this.widget.field_ids)
    },
  },
}
</script>
