import { pluralKeys } from '@jadawel/modules/core/utils/plural'

/**
 * What every arabase dashboard widget renders from: its data source and that
 * source's dispatched data, read through `storePrefix` so the same component
 * works on the public dashboard, plus the edit-mode flag and the error marker
 * the header badge shows. Components add their own display logic on top.
 *
 * Each component still declares `emits: ['delete-widget']` itself: its template
 * does the emitting, and vue/require-explicit-emits does not look into mixins.
 */
export default {
  props: {
    dashboard: {
      type: Object,
      required: true,
    },
    widget: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: false,
      default: '',
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    dataSource() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/getDataSourceById`
      ](this.widget.data_source_id)
    },
    dataForDataSource() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/getDataForDataSource`
      ](this.dataSource?.id)
    },
    isEditMode() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEditMode`
      ]
    },
    dataSourceMisconfigured() {
      return !!this.dataForDataSource?._error
    },
    /**
     * Where the rows behind the widget live, for an "open the table" link.
     * Only a signed-in member has the database in their sidebar; the public
     * dashboard and templates have no route to offer.
     */
    sourceTableRoute() {
      const tableId = this.dataSource?.table_id
      if (!tableId || this.storePrefix !== '') {
        return null
      }
      const applications = this.$store.getters['application/getAll'] || []
      const database = applications.find(
        (application) =>
          application.type === 'database' &&
          (application.tables || []).some((table) => table.id === tableId)
      )
      if (!database) {
        return null
      }
      return {
        name: 'database-table',
        params: {
          databaseId: database.id,
          tableId,
          viewId: this.dataSource.view_id || undefined,
        },
      }
    },
  },
  methods: {
    /**
     * A counted message in the reader's plural form ("3 records", "3 سجلات").
     * vue-i18n applies the English rule to Arabic, so the CLDR category is
     * resolved first and names a plain key (see core/utils/plural.js).
     */
    counted(base, count) {
      const keys = pluralKeys(base, this.$i18n.locale, count)
      const key =
        keys.find((candidate) => this.$te(candidate)) || keys[keys.length - 1]
      return this.$t(key, { count })
    },
  },
}
