<template>
  <div class="dashboard-app saved-dashboard">
    <header class="layout__col-2-1 header saved-dashboard__header">
      <span v-if="dashboard" class="saved-dashboard__name">{{
        dashboard.name
      }}</span>
      <nuxt-link
        :to="{ name: 'arabase-my-dashboards' }"
        class="saved-dashboard__back"
      >
        <i class="iconoir-arrow-left"></i>
        {{ $t('myDashboards.title') }}
      </nuxt-link>
    </header>

    <div v-if="state === 'loading'" class="loading-absolute-center"></div>

    <DashboardContent
      v-else-if="state === 'ok'"
      :dashboard="dashboard"
      store-prefix="saved/"
    />

    <div v-else-if="state === 'password'" class="saved-dashboard__notice">
      <i class="iconoir-lock saved-dashboard__notice-icon"></i>
      <h2>{{ $t('myDashboards.passwordTitle') }}</h2>
      <p>{{ $t('myDashboards.passwordChangedShort') }}</p>
      <Error :error="error"></Error>
      <form class="saved-dashboard__password" @submit.prevent="unlock">
        <FormInput
          v-model="password"
          type="password"
          autocomplete="off"
          :disabled="unlocking"
          :placeholder="$t('myDashboards.passwordLabel')"
        />
        <Button
          type="primary"
          :loading="unlocking"
          :disabled="unlocking || !password"
        >
          {{ $t('myDashboards.unlock') }}
        </Button>
      </form>
    </div>

    <div v-else class="saved-dashboard__notice">
      <i
        class="saved-dashboard__notice-icon"
        :class="
          state === 'unreachable'
            ? 'iconoir-cloud-sync'
            : 'iconoir-warning-triangle'
        "
      ></i>
      <h2>{{ $t(`myDashboards.errors.${errorKey}.title`) }}</h2>
      <p>{{ $t(`myDashboards.errors.${errorKey}.message`) }}</p>
      <Button v-if="state === 'unreachable'" type="secondary" @click="load">
        {{ $t('myDashboards.retry') }}
      </Button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useHead, useNuxtApp } from '#imports'

import DashboardContent from '@jadawel/modules/dashboard/components/DashboardContent'
import SavedDashboardsService from '@jadawel/modules/arabase/services/savedDashboards'
import {
  KNOWN_ERRORS,
  errorCode,
} from '@jadawel/modules/arabase/savedDashboards/errors'
import { PUBLIC_PLACEHOLDER_ENTITY_ID } from '@jadawel/modules/database/utils/constants'

definePageMeta({
  layout: 'app',
  middleware: [
    'settings',
    'authenticated',
    'impersonate',
    'workspacesAndApplications',
  ],
})

/**
 * One saved dashboard, full size and read-only, whatever its source: the
 * `saved/` store loads it through `/arabase/my-dashboards/<id>/`.
 */
const route = useRoute()
const { $store, $client, $i18n } = useNuxtApp()

const STATES = {
  ERROR_SAVED_DASHBOARD_PASSWORD_REQUIRED: 'password',
  ERROR_SAVED_DASHBOARD_UNREACHABLE: 'unreachable',
}

const state = ref('loading')
const dashboard = ref(null)
const errorKey = ref('ERROR_SAVED_DASHBOARD_UNAVAILABLE')
const password = ref('')
const unlocking = ref(false)
const error = reactive({ visible: false, title: '', message: '' })

const savedDashboardId = computed(() => parseInt(route.params.savedDashboardId))

useHead(() => ({
  title: dashboard.value?.name || $i18n.t('myDashboards.title'),
}))

async function load() {
  state.value = 'loading'
  try {
    const loaded = await $store.dispatch(
      'saved/dashboardApplication/fetchInitial',
      { savedDashboardId: savedDashboardId.value }
    )
    dashboard.value = {
      ...loaded,
      // As on the public page: a workspace id that grants nothing, so every
      // widget renders read-only, even for the owner of the dashboard.
      workspace: { id: PUBLIC_PLACEHOLDER_ENTITY_ID },
    }
    state.value = 'ok'
  } catch (e) {
    const code = errorCode(e)
    e.handler?.handled()
    state.value = STATES[code] || 'unavailable'
    errorKey.value = KNOWN_ERRORS.includes(code)
      ? code
      : 'ERROR_SAVED_DASHBOARD_UNAVAILABLE'
  }
}

async function unlock() {
  if (!password.value || unlocking.value) {
    return
  }
  unlocking.value = true
  error.visible = false
  try {
    await SavedDashboardsService($client).enterPassword(
      savedDashboardId.value,
      password.value
    )
    password.value = ''
    await load()
  } catch (e) {
    const code = errorCode(e)
    const key = KNOWN_ERRORS.includes(code)
      ? code
      : 'ERROR_SAVED_DASHBOARD_UNAVAILABLE'
    e.handler?.handled()
    Object.assign(error, {
      visible: true,
      title: $i18n.t(`myDashboards.errors.${key}.title`),
      message: $i18n.t(`myDashboards.errors.${key}.message`),
    })
  } finally {
    unlocking.value = false
  }
}

onMounted(load)

onBeforeUnmount(() => {
  $store.dispatch('saved/dashboardApplication/reset')
})
</script>
