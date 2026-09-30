<template>
  <div>
    <!-- The themed bar every other page has, so the workspace tools and
    notifications pinned to its corner sit on the theme colour. -->
    <header class="layout__col-2-1 header my-dashboards__bar">
      <h1 class="my-dashboards__bar-title">
        <i class="jadawel-icon-dashboard"></i>
        {{ $t('myDashboards.title') }}
      </h1>
    </header>
    <div class="layout__col-2-2 my-dashboards__scroll">
      <div class="my-dashboards">
        <header class="my-dashboards__header">
          <p class="my-dashboards__description">
            {{ $t('myDashboards.description') }}
          </p>
          <Button icon="iconoir-plus" @click="addModal.show()">
            {{ $t('myDashboards.addDashboard') }}
          </Button>
        </header>

        <div v-if="loading" class="loading-absolute-center"></div>

        <div v-else-if="!cards.length" class="my-dashboards__empty">
          <i class="my-dashboards__empty-icon jadawel-icon-dashboard"></i>
          <h2>{{ $t('myDashboards.emptyTitle') }}</h2>
          <p>{{ $t('myDashboards.emptyText') }}</p>
          <Button icon="iconoir-plus" @click="addModal.show()">
            {{ $t('myDashboards.addDashboard') }}
          </Button>
        </div>

        <div v-else class="my-dashboards__grid">
          <SavedDashboardCard
            v-for="card in cards"
            :key="card.id"
            v-grid-sortable="{
              id: card.id,
              update: reorder,
              handle: '.saved-dashboard-card__footer',
            }"
            :card="card"
            @open="open"
            @open-in-workspace="openInWorkspace"
            @password="passwordModal.open($event)"
            @remove="remove"
          />
        </div>
      </div>
    </div>

    <AddSavedDashboardModal ref="addModal" @added="added" />
    <SavedDashboardPasswordModal ref="passwordModal" @unlocked="replace" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useHead, useNuxtApp } from '#imports'

import SavedDashboardsService from '@jadawel/modules/arabase/services/savedDashboards'
import SavedDashboardCard from '@jadawel/modules/arabase/savedDashboards/components/SavedDashboardCard'
import AddSavedDashboardModal from '@jadawel/modules/arabase/savedDashboards/components/AddSavedDashboardModal'
import SavedDashboardPasswordModal from '@jadawel/modules/arabase/savedDashboards/components/SavedDashboardPasswordModal'
import { notifyIf } from '@jadawel/modules/core/utils/error'

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
 * "My dashboards" (لوحاتي): every dashboard the user collected, from their own
 * workspaces or by link, as a gallery. A card opens its dashboard full size
 * (`arabase-my-dashboard`). docs/MY_DASHBOARDS.md.
 */
const router = useRouter()
const { $client, $i18n } = useNuxtApp()
const service = SavedDashboardsService($client)

const cards = ref([])
const loading = ref(true)
const addModal = ref(null)
const passwordModal = ref(null)

useHead({ title: $i18n.t('myDashboards.title') })

onMounted(async () => {
  try {
    const { data } = await service.list()
    cards.value = data
  } catch (error) {
    notifyIf(error, 'dashboard')
  } finally {
    loading.value = false
  }
})

function added(card) {
  if (!cards.value.some((existing) => existing.id === card.id)) {
    cards.value.push(card)
  }
}

function replace(card) {
  cards.value = cards.value.map((existing) =>
    existing.id === card.id ? card : existing
  )
}

function open(card) {
  router.push({
    name: 'arabase-my-dashboard',
    params: { savedDashboardId: card.id },
  })
}

function openInWorkspace(card) {
  router.push({
    name: 'dashboard-application',
    params: { dashboardId: card.dashboard_id },
  })
}

async function remove(card) {
  const before = cards.value
  cards.value = cards.value.filter((existing) => existing.id !== card.id)
  try {
    await service.remove(card.id)
  } catch (error) {
    cards.value = before
    notifyIf(error, 'dashboard')
  }
}

async function reorder(newOrder) {
  const before = cards.value
  const byId = Object.fromEntries(cards.value.map((card) => [card.id, card]))
  cards.value = newOrder.map((id) => byId[id]).filter(Boolean)
  try {
    await service.order(newOrder)
  } catch (error) {
    cards.value = before
    notifyIf(error, 'dashboard')
  }
}
</script>
