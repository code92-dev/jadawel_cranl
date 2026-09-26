<template>
  <div class="dashboard-upcoming-dates-widget">
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
            <Badge v-else-if="overdueCount > 0" color="red" rounded>{{
              $t('upcomingDatesWidget.overdueCount', { count: overdueCount })
            }}</Badge>
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
      <div class="widget__content dashboard-upcoming-dates-widget__body">
        <div v-if="!hasRows" class="dashboard-upcoming-dates-widget__empty">
          {{
            dataSourceMisconfigured
              ? $t('upcomingDatesWidget.misconfigured')
              : $t('upcomingDatesWidget.nothingDue')
          }}
        </div>
        <RecordRows
          v-else
          :rows="rows"
          :fields="fields"
          :trailing-label="dateFieldName"
          :trailing-value="dueLabel"
          :row-is-flagged="isOverdue"
        />
      </div>
    </template>
    <div
      v-else
      class="dashboard-upcoming-dates-widget__loading loading-spinner"
    ></div>
  </div>
</template>

<script>
import moment from '@jadawel/modules/core/moment'
import RecordRows from '@jadawel/modules/arabase/dashboard/components/widget/RecordRows'
import { resolveDisplayedFields } from '@jadawel/modules/arabase/dashboard/recordValues'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'
import WidgetContextMenu from '@jadawel/modules/dashboard/components/widget/WidgetContextMenu'

export default {
  name: 'UpcomingDatesWidget',
  components: { RecordRows, WidgetContextMenu },
  mixins: [dashboardWidget],
  emits: ['delete-widget'],
  computed: {
    rows() {
      return this.dataForDataSource?.results || []
    },
    hasRows() {
      return this.rows.length > 0
    },
    /**
     * The name of the field the window is measured on. Rows are keyed by field
     * name, and the id lives on the service, so the schema maps between them.
     */
    dateFieldName() {
      const fieldId = this.dataSource?.date_field_id
      if (!fieldId) {
        return null
      }
      const property =
        this.dataSource?.schema?.items?.properties?.[`field_${fieldId}`]
      return property?.title || null
    },
    /**
     * The date column is excluded from the field columns: it always shows in the
     * trailing column, and repeating it wastes the widget's width.
     */
    fields() {
      const fieldId = this.dataSource?.date_field_id
      return resolveDisplayedFields(
        this.dataSource,
        this.widget.field_ids,
        2
      ).filter((field) => field.id !== fieldId)
    },
    overdueCount() {
      return this.rows.filter((row) => this.isOverdue(row)).length
    },
  },
  methods: {
    rawDate(row) {
      return this.dateFieldName ? row[this.dateFieldName] : null
    },
    isOverdue(row) {
      const value = this.rawDate(row)
      if (!value) {
        return false
      }
      return moment(value).isBefore(moment().startOf('day'))
    },
    /**
     * Relative wording ("in 3 days", "منذ يومين") rather than a date, because the
     * question an agenda answers is how soon, not when. Moment is already locale
     * aware across the app.
     */
    dueLabel(row) {
      const value = this.rawDate(row)
      if (!value) {
        return ''
      }
      return moment(value).locale(this.$i18n.locale).fromNow()
    },
  },
}
</script>
