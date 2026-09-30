<template>
  <Modal ref="modal" @show="load" @hidden="reset">
    <h2 class="box__title">{{ $t('myDashboards.addTitle') }}</h2>

    <SegmentControl
      v-model:active-index="tab"
      :segments="segments"
      class="margin-bottom-2"
    />

    <Error :error="error"></Error>

    <div v-if="tab === 0" class="add-saved-dashboard">
      <div v-if="loadingAvailable" class="loading margin-auto"></div>
      <p v-else-if="!workspaces.length" class="add-saved-dashboard__empty">
        {{ $t('myDashboards.noWorkspaceDashboards') }}
      </p>
      <div
        v-for="workspace in workspaces"
        v-else
        :key="workspace.id"
        class="add-saved-dashboard__workspace"
      >
        <div class="add-saved-dashboard__workspace-name">
          {{ workspace.name }}
        </div>
        <ul class="add-saved-dashboard__list">
          <li
            v-for="dashboard in workspace.dashboards"
            :key="dashboard.id"
            class="add-saved-dashboard__item"
          >
            <i class="jadawel-icon-dashboard"></i>
            <span class="add-saved-dashboard__item-name">{{
              dashboard.name
            }}</span>
            <span v-if="dashboard.saved" class="add-saved-dashboard__added">
              <i class="iconoir-check"></i>
              {{ $t('myDashboards.added') }}
            </span>
            <Button
              v-else
              type="secondary"
              size="small"
              icon="iconoir-plus"
              :loading="addingId === dashboard.id"
              :disabled="addingId !== null"
              @click="addFromWorkspace(dashboard)"
            >
              {{ $t('myDashboards.add') }}
            </Button>
          </li>
        </ul>
      </div>
    </div>

    <form v-else class="add-saved-dashboard" @submit.prevent="addLink">
      <p class="box__description">{{ $t('myDashboards.linkDescription') }}</p>
      <FormGroup :label="$t('myDashboards.linkLabel')" required>
        <FormInput
          ref="url"
          v-model="url"
          :placeholder="$t('myDashboards.linkPlaceholder')"
          :disabled="submitting"
          dir="ltr"
          @update:model-value="needsPassword = false"
        />
      </FormGroup>
      <FormGroup
        v-if="needsPassword"
        :label="$t('myDashboards.passwordLabel')"
        :helper-text="$t('myDashboards.passwordNeeded')"
        required
        class="margin-top-2"
      >
        <FormInput
          ref="password"
          v-model="password"
          type="password"
          autocomplete="off"
          :disabled="submitting"
        />
      </FormGroup>
      <div class="actions">
        <ul class="action__links">
          <li>
            <a :disabled="submitting" @click.prevent="hide()">{{
              $t('action.cancel')
            }}</a>
          </li>
        </ul>
        <Button
          type="primary"
          :loading="submitting"
          :disabled="submitting || !url.trim() || (needsPassword && !password)"
        >
          {{ $t('myDashboards.add') }}
        </Button>
      </div>
    </form>
  </Modal>
</template>

<script>
import modal from '@jadawel/modules/core/mixins/modal'
import error from '@jadawel/modules/core/mixins/error'
import SavedDashboardsService from '@jadawel/modules/arabase/services/savedDashboards'
import {
  errorCode,
  showSavedDashboardError,
} from '@jadawel/modules/arabase/savedDashboards/errors'

/**
 * Adds a dashboard to "My dashboards": one of the user's own, picked from
 * their workspaces, or anyone's by its public link — here or on another
 * Jadawel server. A protected link asks for its password before it is added.
 */
export default {
  name: 'AddSavedDashboardModal',
  mixins: [modal, error],
  emits: ['added'],
  data() {
    return {
      tab: 0,
      workspaces: [],
      loadingAvailable: false,
      addingId: null,
      url: '',
      password: '',
      needsPassword: false,
      submitting: false,
    }
  },
  computed: {
    segments() {
      return [
        {
          label: this.$t('myDashboards.fromWorkspaces'),
          icon: 'iconoir-view-grid',
        },
        { label: this.$t('myDashboards.byLink'), icon: 'iconoir-link' },
      ]
    },
  },
  watch: {
    tab() {
      this.hideError()
    },
  },
  methods: {
    service() {
      return SavedDashboardsService(this.$client)
    },
    async load() {
      this.loadingAvailable = true
      try {
        const { data } = await this.service().listAvailable()
        this.workspaces = data
      } catch (error) {
        this.handleError(error, 'dashboard')
      } finally {
        this.loadingAvailable = false
      }
    },
    reset() {
      this.tab = 0
      this.url = ''
      this.password = ''
      this.needsPassword = false
      this.hideError()
    },
    async addFromWorkspace(dashboard) {
      this.addingId = dashboard.id
      this.hideError()
      try {
        const { data } = await this.service().addFromWorkspace(dashboard.id)
        dashboard.saved = true
        this.$emit('added', data)
      } catch (error) {
        showSavedDashboardError(this, error)
      } finally {
        this.addingId = null
      }
    },
    async addLink() {
      if (this.submitting || !this.url.trim()) {
        return
      }
      this.submitting = true
      this.hideError()
      try {
        const { data } = await this.service().addLink(
          this.url.trim(),
          this.needsPassword ? this.password : ''
        )
        this.$emit('added', data)
        this.hide()
      } catch (error) {
        if (errorCode(error) === 'ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED') {
          error.handler.handled()
          this.needsPassword = true
          this.$nextTick(() => this.$refs.password?.focus?.())
        } else {
          showSavedDashboardError(this, error)
        }
      } finally {
        this.submitting = false
      }
    },
  },
}
</script>
