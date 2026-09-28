<template>
  <WidgetFrame
    :widget="widget"
    :loading="loading"
    :edit-mode="isEditMode"
    :misconfigured="dataSourceMisconfigured"
    :misconfigured-message="$t('recordsListWidget.misconfigured')"
    :empty="!hasRows"
    :empty-message="$t('recordsListWidget.noRecords')"
    empty-icon="task-list"
  >
    <template #badges>
      <span v-if="hasRows" class="widget-count">{{
        counted('recordsListWidget.count', rows.length)
      }}</span>
    </template>
    <template v-if="sourceTableRoute && !isEditMode" #actions>
      <nuxt-link
        :to="sourceTableRoute"
        class="widget-frame__action"
        :title="$t('widgetFrame.openTable')"
        :aria-label="$t('widgetFrame.openTable')"
      >
        <i class="iconoir-open-new-window"></i>
      </nuxt-link>
    </template>
    <RecordRows :rows="rows" :fields="fields" />
  </WidgetFrame>
</template>

<script>
import RecordRows from '@jadawel/modules/arabase/dashboard/components/widget/RecordRows'
import WidgetFrame from '@jadawel/modules/arabase/dashboard/components/widget/WidgetFrame'
import { resolveDisplayedFields } from '@jadawel/modules/arabase/dashboard/recordValues'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'

export default {
  name: 'RecordsListWidget',
  components: { RecordRows, WidgetFrame },
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
