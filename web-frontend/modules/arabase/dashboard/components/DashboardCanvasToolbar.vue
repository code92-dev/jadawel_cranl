<template>
  <div class="dashboard-toolbar">
    <template v-if="isEditMode">
      <span class="dashboard-toolbar__hint">
        <i class="iconoir-drag" aria-hidden="true"></i>
        {{ $t('dashboardToolbar.editHint') }}
      </span>
      <Button
        v-if="canCreateWidget"
        type="primary"
        size="regular"
        icon="iconoir-plus"
        @click="$emit('add-widget')"
        >{{ $t('dashboardToolbar.addWidget') }}</Button
      >
    </template>
    <template v-else-if="!isEmpty">
      <span v-if="refreshedAt" class="dashboard-toolbar__updated">
        {{ $t('dashboardToolbar.updated', { time: refreshedLabel }) }}
      </span>
      <ButtonIcon
        type="secondary"
        icon="iconoir-refresh-double"
        :loading="refreshing"
        :disabled="refreshing"
        :title="$t('dashboardToolbar.refresh')"
        :aria-label="$t('dashboardToolbar.refresh')"
        @click="refresh"
      ></ButtonIcon>
    </template>
  </div>
</template>

<script>
import moment from '@jadawel/modules/core/moment'

/**
 * The actions beside the dashboard's title. Reading it: when the numbers were
 * fetched and a button to fetch them again, since a dashboard left open on a
 * wall screen otherwise shows the morning's figures all day. Editing it: how
 * the board is arranged and the button that adds a widget.
 */
export default {
  name: 'DashboardCanvasToolbar',
  props: {
    dashboard: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: false,
      default: '',
    },
    canCreateWidget: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['add-widget'],
  data() {
    return {
      refreshing: false,
      refreshedAt: null,
    }
  },
  computed: {
    isEditMode() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEditMode`
      ]
    },
    isEmpty() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/isEmpty`
      ]
    },
    widgets() {
      return this.$store.getters[
        `${this.storePrefix}dashboardApplication/getWidgets`
      ]
    },
    refreshedLabel() {
      return moment(this.refreshedAt).locale(this.$i18n.locale).format('LT')
    },
  },
  mounted() {
    this.refreshedAt = new Date()
  },
  methods: {
    async refresh() {
      const ids = [
        ...new Set(
          this.widgets.map((widget) => widget.data_source_id).filter(Boolean)
        ),
      ]
      this.refreshing = true
      try {
        await Promise.all(
          ids.map((id) =>
            this.$store.dispatch(
              `${this.storePrefix}dashboardApplication/dispatchDataSource`,
              id
            )
          )
        )
        this.refreshedAt = new Date()
      } finally {
        this.refreshing = false
      }
    },
  },
}
</script>
