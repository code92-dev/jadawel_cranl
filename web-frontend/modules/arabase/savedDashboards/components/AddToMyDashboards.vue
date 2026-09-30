<template>
  <a
    class="header__filter-link"
    :class="{ 'header__filter-link--disabled': adding }"
    @click="add"
  >
    <i class="header__filter-icon iconoir-pin"></i>
    <span class="header__filter-name">{{ $t('myDashboards.addToMine') }}</span>
  </a>
</template>

<script>
import SavedDashboardsService from '@jadawel/modules/arabase/services/savedDashboards'
import { notifyIf } from '@jadawel/modules/core/utils/error'

/**
 * Sends the open dashboard to the user's "My dashboards" page. Shown to anyone
 * who can open the dashboard; adding it twice keeps the one card.
 */
export default {
  name: 'AddToMyDashboards',
  props: {
    dashboard: {
      type: Object,
      required: true,
    },
  },
  data() {
    return { adding: false }
  },
  methods: {
    async add() {
      if (this.adding) {
        return
      }
      this.adding = true
      try {
        await SavedDashboardsService(this.$client).addFromWorkspace(
          this.dashboard.id
        )
        this.$store.dispatch('toast/success', {
          title: this.$t('myDashboards.addedTitle'),
          message: this.$t('myDashboards.addedMessage', {
            name: this.dashboard.name,
          }),
        })
      } catch (error) {
        notifyIf(error, 'dashboard')
      } finally {
        this.adding = false
      }
    },
  },
}
</script>
