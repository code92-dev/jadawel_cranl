<template>
  <WidgetFrame
    :widget="widget"
    :loading="loading"
    :edit-mode="isEditMode"
    :misconfigured="dataSourceMisconfigured"
    :misconfigured-message="$t('upcomingDatesWidget.misconfigured')"
    :empty="!hasRows"
    :empty-message="$t('upcomingDatesWidget.nothingDue')"
    empty-icon="calendar"
  >
    <template #badges>
      <span v-if="overdueCount > 0" class="widget-status widget-status--danger">
        <i class="iconoir-warning-triangle" aria-hidden="true"></i>
        {{ counted('upcomingDatesWidget.overdue', overdueCount) }}
      </span>
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

    <div class="widget-agenda">
      <section
        v-for="group in groups"
        :key="group.key"
        class="widget-agenda__group"
      >
        <h4 class="widget-agenda__group-title">{{ group.title }}</h4>
        <ul class="widget-agenda__list">
          <li
            v-for="(item, index) in group.items"
            :key="item.row.id ?? index"
            class="widget-agenda__item"
            :class="`widget-agenda__item--${item.when}`"
          >
            <span class="widget-agenda__date" :title="item.fullDate">
              <span class="widget-agenda__day">{{ item.day }}</span>
              <span class="widget-agenda__month">{{ item.month }}</span>
            </span>
            <span class="widget-agenda__text">
              <span class="widget-agenda__title" :title="item.title">{{
                item.title || '—'
              }}</span>
              <span
                v-if="item.details"
                class="widget-agenda__details"
                :title="item.details"
                >{{ item.details }}</span
              >
            </span>
            <span class="widget-agenda__due">{{ item.relative }}</span>
          </li>
        </ul>
      </section>
    </div>
  </WidgetFrame>
</template>

<script>
import moment from '@jadawel/modules/core/moment'
import WidgetFrame from '@jadawel/modules/arabase/dashboard/components/widget/WidgetFrame'
import {
  formatRecordValue,
  resolveDisplayedFields,
} from '@jadawel/modules/arabase/dashboard/recordValues'
import dashboardWidget from '@jadawel/modules/arabase/dashboard/mixins/dashboardWidget'

/** Agenda groups, in reading order. */
const GROUPS = ['overdue', 'today', 'week', 'later']

export default {
  name: 'UpcomingDatesWidget',
  components: { WidgetFrame },
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
     * The fields shown with each date: the first is the item's title, the rest
     * its details. The date itself is the tile at the start of the row, so it is
     * not repeated.
     */
    fields() {
      const fieldId = this.dataSource?.date_field_id
      return resolveDisplayedFields(
        this.dataSource,
        this.widget.field_ids,
        2
      ).filter((field) => field.id !== fieldId)
    },
    items() {
      const today = moment().startOf('day')
      const locale = this.$i18n.locale
      return this.rows.map((row) => {
        const raw = this.dateFieldName ? row[this.dateFieldName] : null
        const date = raw ? moment(raw) : null
        const valid = date && date.isValid()
        const days = valid ? date.clone().startOf('day').diff(today, 'days') : 0
        const [first, ...rest] = this.fields
        return {
          row,
          days,
          when: !valid
            ? 'later'
            : days < 0
              ? 'overdue'
              : days === 0
                ? 'today'
                : days <= 7
                  ? 'week'
                  : 'later',
          day: valid ? date.locale(locale).format('D') : '—',
          month: valid ? date.locale(locale).format('MMM') : '',
          fullDate: valid ? date.locale(locale).format('dddd D MMMM YYYY') : '',
          title: first ? formatRecordValue(row[first.name]) : '',
          details: rest
            .map((field) => formatRecordValue(row[field.name]))
            .filter(Boolean)
            .join(' · '),
          relative: valid ? this.relative(days) : '',
        }
      })
    },
    groups() {
      return GROUPS.map((key) => ({
        key,
        title: this.$t(`upcomingDatesWidget.group.${key}`),
        items: this.items.filter((item) => item.when === key),
      })).filter((group) => group.items.length > 0)
    },
    overdueCount() {
      return this.items.filter((item) => item.when === 'overdue').length
    },
  },
  methods: {
    /**
     * How soon, in whole days — the question an agenda answers. Counted by
     * calendar day rather than moment's `fromNow`, which measures from this
     * minute and calls a date-only deadline tomorrow "in 9 hours".
     */
    relative(days) {
      if (days === 0) {
        return this.$t('upcomingDatesWidget.today')
      }
      if (days === 1) {
        return this.$t('upcomingDatesWidget.tomorrow')
      }
      if (days === -1) {
        return this.$t('upcomingDatesWidget.yesterday')
      }
      return days > 0
        ? this.counted('upcomingDatesWidget.inDays', days)
        : this.counted('upcomingDatesWidget.daysAgo', -days)
    },
  },
}
</script>
