<template>
  <section class="dashboard__section">
    <div class="dashboard__section-head">
      <h2 class="dashboard__section-title">
        {{ $t('workspaceItems.title') }}
        <span class="dashboard__section-count">{{ applications.length }}</span>
      </h2>

      <div class="workspace-items__controls">
        <Dropdown
          class="workspace-items__filter"
          :model-value="selectedTypes"
          :show-search="false"
          multiple
          @update:model-value="selectedTypes = $event"
        >
          <template #selectedValue>
            <span class="dropdown__selected-text">{{ filterLabel }}</span>
          </template>
          <template #defaultValue>
            <span class="dropdown__selected-text">{{ filterLabel }}</span>
          </template>
          <DropdownItem
            v-for="applicationType in applicationTypes"
            :key="applicationType.getType()"
            :name="applicationType.getName()"
            :value="applicationType.getType()"
            :icon="applicationType.iconClass"
          ></DropdownItem>
        </Dropdown>

        <Dropdown
          v-model="sortBy"
          class="workspace-items__sort"
          :show-search="false"
        >
          <DropdownItem
            v-for="option in sortOptions"
            :key="option.value"
            :name="option.name"
            :value="option.value"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>

    <div v-if="visibleApplications.length > 0" class="workspace-items__grid">
      <AllWorkspacesApplicationCard
        v-for="application in visibleApplications"
        :key="application.id"
        :application="application"
        :workspace="workspace"
        :sort-by="sortBy"
        @click="select(application)"
      ></AllWorkspacesApplicationCard>
    </div>
    <div v-else class="workspace-items__no-match">
      {{ $t('allWorkspaces.noFilterMatches') }}
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useNuxtApp, useRouter } from '#app'

import AllWorkspacesApplicationCard from '@jadawel/modules/core/components/allWorkspaces/AllWorkspacesApplicationCard'
import { provideNow } from '@jadawel/modules/core/composables/useNow'
import { useUserPreference } from '@jadawel/modules/core/composables/useUserPreference'
import {
  getApplicationComparator,
  isTypeFilterActive,
  SORT_BY_CREATED,
  SORT_BY_LAST_VIEWED,
  SORT_BY_NAME_ASC,
  SORT_BY_NAME_DESC,
} from '@jadawel/modules/core/utils/allWorkspaces'

/**
 * Everything in one workspace (databases, applications, dashboards and
 * automations) as the same cards the workspaces homepage uses, so an item
 * looks and behaves the same on both pages. The sort is shared with the
 * homepage too.
 */
const props = defineProps({
  workspace: {
    type: Object,
    required: true,
  },
  applications: {
    type: Array,
    required: true,
  },
})

const store = useStore()
const router = useRouter()
const { $registry, $i18n } = useNuxtApp()

const applicationTypes = $registry.getOrderedList('application')

// Nothing selected means "no filtering", as on the homepage.
const selectedTypes = ref([])
const sortBy = useUserPreference('all_workspaces_sort_by', SORT_BY_LAST_VIEWED)

const sortOptions = computed(() => [
  { value: SORT_BY_CREATED, name: $i18n.t('common.created') },
  { value: SORT_BY_LAST_VIEWED, name: $i18n.t('common.lastViewed') },
  { value: SORT_BY_NAME_ASC, name: $i18n.t('common.nameAsc') },
  { value: SORT_BY_NAME_DESC, name: $i18n.t('common.nameDesc') },
])

const filterActive = computed(() =>
  isTypeFilterActive(selectedTypes.value, applicationTypes.length)
)

const filterLabel = computed(() =>
  filterActive.value
    ? $i18n.t('allWorkspaces.itemsSelected', {
        count: selectedTypes.value.length,
      })
    : $i18n.t('allWorkspaces.allItems')
)

const visibleApplications = computed(() => {
  const applications = filterActive.value
    ? props.applications.filter((application) =>
        selectedTypes.value.includes(application.type)
      )
    : [...props.applications]
  return applications.sort(getApplicationComparator(sortBy.value))
})

// The cards show relative dates that must keep ageing while the page is open.
provideNow()

async function select(application) {
  if (application._.loading) {
    return
  }

  const type = $registry.get('application', application.type)
  await store.dispatch('application/setItemLoading', {
    application,
    value: true,
  })
  try {
    await type.select(application, { $router: router, $store: store, $i18n })
  } finally {
    await store.dispatch('application/setItemLoading', {
      application,
      value: false,
    })
  }
}
</script>
