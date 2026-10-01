<template>
  <div v-if="workspaceExists">
    <div class="dashboard__header" ph-autocapture="dashboard-header">
      <div class="dashboard__header-left">
        <h1
          ref="contextLink"
          class="dashboard__workspace-name"
          @click="
            $refs.context.toggle($refs.contextLink, 'bottom', 'left', -14)
          "
        >
          <div class="dashboard__workspace-name-text">
            <Editable
              ref="rename"
              :value="selectedWorkspace.name"
              @change="renameWorkspace(selectedWorkspace, $event)"
            >
            </Editable>
          </div>
          <i class="dashboard__workspace-name-icon iconoir-nav-arrow-down"></i>
        </h1>
        <component
          :is="component"
          v-for="(component, index) in dashboardWorkspacePlanBadge"
          :key="index"
          :workspace="selectedWorkspace"
          :component-arguments="workspaceComponentArguments"
        ></component>
      </div>
      <WorkspaceContext
        ref="context"
        :workspace="selectedWorkspace"
        @rename="enableRename()"
      ></WorkspaceContext>
      <div class="dashboard__header-right">
        <component
          :is="component"
          v-for="(component, index) in dashboardWorkspaceRowUsageComponent"
          :key="index"
          :workspace="selectedWorkspace"
          :component-arguments="workspaceComponentArguments"
          @workspace-updated="workspaceUpdated($event)"
        ></component>
        <div class="dashboard__header-actions">
          <span
            v-if="canCreateCreateApplication"
            ref="createApplicationContextLink"
          >
            <Button
              icon="iconoir-plus"
              tag="a"
              @click="
                $refs.createApplicationContext.toggle(
                  $refs.createApplicationContextLink
                )
              "
              >{{ $t('dashboard.addNew') }}</Button
            >
          </span>
          <span
            ref="workspaceContextLink"
            @click="
              $refs.context.toggle(
                $refs.workspaceContextLink,
                'bottom',
                'right',
                4
              )
            "
          >
            <ButtonIcon
              type="secondary"
              icon="jadawel-icon-more-vertical"
            ></ButtonIcon>
          </span>
        </div>
      </div>
    </div>
    <div
      class="dashboard__scroll-container"
      ph-autocapture="dashboard-container"
    >
      <div class="dashboard__main">
        <component
          :is="component"
          v-for="(component, index) in dashboardTopComponents"
          :key="index"
          :workspace="selectedWorkspace"
        ></component>
        <div class="dashboard__extras">
          <div class="dashboard__resources">
            <div class="dashboard__resources-wrapper">
              <a
                v-if="canCreateCreateApplication"
                class="dashboard__resource"
                role="button"
                tabindex="0"
                @click="$refs.templateModal.show()"
                @keydown.enter.prevent="$refs.templateModal.show()"
                @keydown.space.prevent="$refs.templateModal.show()"
              >
                <div class="dashboard__resource-inner">
                  <span class="dashboard__resource-icon">
                    <i class="iconoir-page"></i
                  ></span>

                  <div class="dashboard__resource-content">
                    <h4 class="dashboard__resource-title">
                      {{ $t('dashboard.templates') }}
                    </h4>
                    <p class="dashboard__resource-text">
                      {{ $t('dashboard.templatesMessage') }}
                    </p>
                  </div>
                </div>
              </a>
              <component
                :is="component"
                v-for="(component, index) in resourceLinksComponents"
                :key="index"
              ></component>
            </div>
          </div>
        </div>
        <div class="dashboard__wrapper">
          <!--
            One list for everything in the workspace (databases, applications,
            dashboards, automations and the views and pages inside them), most
            recently viewed first, instead of one list per application type.
          -->
          <RecentlyViewed
            v-if="orderedApplicationsInSelectedWorkspace.length"
            :workspace="selectedWorkspace"
            :title="$t('recentlyViewed.yourItems')"
            view-mode-preference-key="workspace_recently_viewed_view_mode"
          >
            <template #empty-action>
              <span
                v-if="canCreateCreateApplication"
                ref="createApplicationContextLink2"
              >
                <Button
                  icon="iconoir-plus"
                  tag="a"
                  @click="
                    $refs.createApplicationContext.toggle(
                      $refs.createApplicationContextLink2
                    )
                  "
                  >{{ $t('dashboard.addNew') }}</Button
                >
              </span>
            </template>
          </RecentlyViewed>
          <div v-else class="dashboard__no-application">
            <img
              src="@jadawel/modules/core/assets/images/empty_workspace_illustration.png"
              srcset="
                @jadawel/modules/core/assets/images/empty_workspace_illustration@2x.png 2x
              "
            />
            <h4>{{ $t('dashboard.emptyWorkspace') }}</h4>
            <p v-if="canCreateCreateApplication">
              {{ $t('dashboard.emptyWorkspaceMessage') }}
            </p>
            <span
              v-if="canCreateCreateApplication"
              ref="createApplicationContextLink2"
            >
              <Button
                icon="iconoir-plus"
                tag="a"
                @click="
                  $refs.createApplicationContext.toggle(
                    $refs.createApplicationContextLink2
                  )
                "
                >{{ $t('dashboard.addNew') }}</Button
              >
            </span>
          </div>
        </div>
        <!--
          Jadawel fork: the workspace's own numbers (databases, tables, rows,
          members and recent activity) stay under the list of items.
        -->
        <DashboardOverview
          v-if="orderedApplicationsInSelectedWorkspace.length"
          :workspace="selectedWorkspace"
          :applications="orderedApplicationsInSelectedWorkspace"
          :stats="databaseStats"
          :activity="workspaceActivity"
        />
      </div>
      <CreateApplicationContext
        ref="createApplicationContext"
        :workspace="selectedWorkspace"
      >
      </CreateApplicationContext>
    </div>
    <component
      :is="component"
      v-for="(component, index) in dashboardHelpComponents"
      :key="index"
    ></component>
    <TemplateModal
      ref="templateModal"
      :workspace="selectedWorkspace"
    ></TemplateModal>
  </div>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue'
import { useRoute, useNuxtApp, createError } from '#app'
import { useHead, useAsyncData } from '#imports'

import WorkspaceContext from '@jadawel/modules/core/components/workspace/WorkspaceContext'
import CreateApplicationContext from '@jadawel/modules/core/components/application/CreateApplicationContext'
import RecentlyViewed from '@jadawel/modules/core/components/recentlyViewed/RecentlyViewed'
import editWorkspace from '@jadawel/modules/core/mixins/editWorkspace'
import DashboardOverview from '@jadawel/modules/core/components/dashboard/DashboardOverview'
import TemplateModal from '@jadawel/modules/core/components/template/TemplateModal'
import DatabaseStatsService from '@jadawel/modules/arabase/services/databaseStats'
import WorkspaceActivityService from '@jadawel/modules/arabase/services/workspaceActivity'

definePageMeta({
  layout: 'app',
  // Note: these middlewares must be explicitly listed because child pages
  // don't automatically inherit parent middleware in Nuxt 3's page meta
  middleware: [
    'settings',
    'authenticated',
    'impersonate',
    'workspacesAndApplications',
  ],
})

defineOptions({
  mixins: [editWorkspace],
})

const route = useRoute()
const nuxtApp = useNuxtApp()
const { $store, $registry, $i18n, $hasPermission, $client } = nuxtApp

/**
 * Row / field / table counters keyed by database id, for the overview.
 *
 * Fetched client-side, after the page has rendered, rather than awaited in
 * `useAsyncData` with the rest of the workspace payload. Row counting is a
 * COUNT(*) per table, so blocking the first paint on it would make the whole
 * page as slow as the largest workspace.
 */
const databaseStats = ref({})

/**
 * Rows created per day over the last month, or null until it resolves.
 *
 * Fetched separately from the counters above: this query groups as well as
 * counts, so a workspace big enough to make it slow should not hold up the
 * counters.
 */
const workspaceActivity = ref(null)

const ACTIVITY_DAYS = 30

// ----------------------------------------------------------------------------
// STATE
// ----------------------------------------------------------------------------
const selectedWorkspace = ref(null)
const workspaceComponentArguments = ref({})

// refs used in template
const context = ref(null)
const contextLink = ref(null)
const createApplicationContext = ref(null)
const createApplicationContextLink = ref(null)
const createApplicationContextLink2 = ref(null)
const workspaceContextLink = ref(null)
const rename = ref(null)
const templateModal = ref(null)

async function fetchWorkspaceExtraData(workspace) {
  const plugins = Object.values($registry.getAll('plugin'))
  let mergedData = {
    selectedWorkspace: workspace,
    workspaceComponentArguments: { usageData: [] },
  }

  for (const p of plugins) {
    const workspaceData = await p.fetchAsyncDashboardData(nuxtApp, workspace.id)

    if (workspaceData) {
      mergedData = p.mergeDashboardData(mergedData, workspaceData)
    }
  }

  return mergedData
}

/**
 * Fetch all dashboard-related data for the current workspace.
 * `useAsyncData` returns the data and we hydrate our refs from it.
 */
const { data: dashboardData, error } = await useAsyncData(
  `current-workspace-${route.params.workspaceId}`,
  async () => {
    const workspaceId = parseInt(route.params.workspaceId, 10)

    let workspace
    try {
      workspace = await $store.dispatch('workspace/selectById', workspaceId)
    } catch (e) {
      throw createError({
        statusCode: 404,
        message: 'Workspace not found.',
      })
    }

    try {
      return await fetchWorkspaceExtraData(workspace)
    } catch {
      throw createError({
        statusCode: 400,
        message: 'Error loading dashboard.',
      })
    }
  }
)

if (error.value) {
  throw error.value
}

/**
 * Hydrate local refs from the async data.
 * Keeps `selectedWorkspace` and `workspaceComponentArguments` reactive and
 * writable for later updates (e.g. `workspaceUpdated`).
 */
watchEffect(() => {
  if (!dashboardData.value) return
  selectedWorkspace.value = dashboardData.value.selectedWorkspace
  workspaceComponentArguments.value =
    dashboardData.value.workspaceComponentArguments
})

/**
 * Load the overview numbers whenever the selected workspace changes.
 *
 * Failures are swallowed on purpose: the overview is a decoration on a page
 * that is fully usable without it.
 */
watchEffect(async () => {
  const workspace = selectedWorkspace.value
  if (!workspace) return

  databaseStats.value = {}
  workspaceActivity.value = null

  try {
    const { data } = await DatabaseStatsService($client).fetchAll(workspace.id)
    // Guard against a slower response for a workspace the user has since left.
    if (selectedWorkspace.value?.id === workspace.id) {
      databaseStats.value = data
    }
  } catch {
    databaseStats.value = {}
  }

  try {
    const { data } = await WorkspaceActivityService($client).fetch(
      workspace.id,
      ACTIVITY_DAYS
    )
    if (selectedWorkspace.value?.id === workspace.id) {
      workspaceActivity.value = data
    }
  } catch {
    workspaceActivity.value = null
  }
})

useHead(() => ({
  title: $i18n.t('dashboard.title'),
}))

const getAllOfWorkspace = (ws) =>
  $store.getters['application/getAllOfWorkspace'](ws)

const dashboardHelpComponents = computed(() =>
  Object.values($registry.getAll('plugin'))
    .reduce(
      (components, plugin) =>
        components.concat(plugin.getDashboardHelpComponents()),
      []
    )
    .filter((c) => c !== null)
)

const dashboardWorkspaceRowUsageComponent = computed(() =>
  Object.values($registry.getAll('plugin'))
    .map((p) => p.getDashboardWorkspaceRowUsageComponent())
    .filter((c) => c !== null)
)

const dashboardWorkspacePlanBadge = computed(() =>
  Object.values($registry.getAll('plugin'))
    .map((p) => p.getDashboardWorkspacePlanBadge())
    .filter((c) => c !== null)
)

const dashboardTopComponents = computed(() =>
  Object.values($registry.getAll('plugin'))
    .reduce(
      (components, plugin) =>
        components.concat(
          plugin.getDashboardTopComponents(selectedWorkspace.value)
        ),
      []
    )
    .filter((c) => c !== null)
)

const resourceLinksComponents = computed(() =>
  Object.values($registry.getAll('plugin'))
    .map((p) => p.getDashboardResourceLinksComponent())
    .filter((c) => c !== null)
)

const orderedApplicationsInSelectedWorkspace = computed(() =>
  !selectedWorkspace.value
    ? []
    : getAllOfWorkspace(selectedWorkspace.value).sort(
        (a, b) => a.order - b.order
      )
)

const canCreateCreateApplication = computed(() => {
  if (!selectedWorkspace.value) return false
  return $hasPermission(
    'workspace.create_application',
    selectedWorkspace.value,
    selectedWorkspace.value.id
  )
})

/**
 * Check if the workspace exists, because if not, it doesn't make any sense to
 * render anything. This can happen when the workspace is a state where it's
 * deleted, for example.
 */
const workspaceExists = computed(() => {
  if (!selectedWorkspace.value) return false
  return $store.getters['workspace/getAll'].some(
    (w) => w.id === selectedWorkspace.value.id
  )
})

// ----------------------------------------------------------------------------
// METHODS
// ----------------------------------------------------------------------------
async function workspaceUpdated(workspace) {
  const extraData = await fetchWorkspaceExtraData(workspace)
  workspaceComponentArguments.value = extraData.workspaceComponentArguments
}
</script>
