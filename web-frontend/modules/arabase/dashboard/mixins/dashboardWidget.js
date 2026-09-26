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
  },
}
