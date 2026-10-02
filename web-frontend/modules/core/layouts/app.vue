<template>
  <div>
    <Toasts />
    <GuidedTour />

    <div ref="app" class="layout">
      <div class="layout__col-1" :style="{ width: col1Width + 'px' }">
        <SidebarAllWorkspaces
          v-if="sidebarType === SIDEBAR_TYPES.ALL_WORKSPACES"
          :workspaces="workspaces"
          :selected-workspace="selectedWorkspace"
          :collapsed="isCollapsed"
          :width="col1Width"
          @set-col1-width="col1Width = $event"
        />
        <Sidebar
          v-else
          :workspaces="workspaces"
          :selected-workspace="selectedWorkspace"
          :applications="applications"
          :collapsed="isCollapsed"
          :width="col1Width"
          :right-sidebar-open="col3Visible"
          @set-col1-width="col1Width = $event"
        />
      </div>

      <div
        class="layout__col-2"
        :style="{
          insetInlineStart: col1Width + 'px',
          insetInlineEnd: col3Shown ? col3Width + 'px' : 0,
        }"
      >
        <slot />

        <!--
          Jadawel: not on the pages with the all workspaces sidebar. Their header
          leaves no room for it, and a workspace is only still selected there
          when the user came from one, so it would overlap the header then and be
          missing after a reload.
        -->
        <AppUtilities
          v-if="
            sidebarType !== SIDEBAR_TYPES.ALL_WORKSPACES &&
            selectedWorkspace &&
            selectedWorkspace.id
          "
          :workspace="selectedWorkspace"
        />
      </div>

      <div
        v-if="col3Shown"
        class="layout__col-3"
        :style="{ width: col3Width + 'px', insetInlineEnd: 0 }"
      >
        <RightSidebar :workspace="selectedWorkspace" />
      </div>

      <HorizontalResize
        class="layout__resize"
        :width="col1Width"
        :style="{ insetInlineStart: col1Width - 2 + 'px' }"
        :min="52"
        :max="300"
        @move="resizeCol1"
      />

      <HorizontalResize
        v-if="col3Shown"
        class="layout__resize"
        :width="col3Width"
        :style="{ insetInlineEnd: col3Width - 3 + 'px' }"
        :min="300"
        :max="500"
        :right="true"
        @move="resizeCol3"
      />

      <component
        :is="component"
        v-for="(component, index) in appLayoutComponents"
        :key="index"
      />
    </div>

    <WorkspaceSearchModal ref="workspaceSearchModal" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'

import Toasts from '@jadawel/modules/core/components/toasts/Toasts.vue'
import Sidebar from '@jadawel/modules/core/components/sidebar/Sidebar.vue'
import SidebarAllWorkspaces from '@jadawel/modules/core/components/sidebar/SidebarAllWorkspaces.vue'
import RightSidebar from '@jadawel/modules/core/components/sidebar/RightSidebar.vue'
import HorizontalResize from '@jadawel/modules/core/components/HorizontalResize.vue'
import GuidedTour from '@jadawel/modules/core/components/guidedTour/GuidedTour.vue'
import WorkspaceSearchModal from '@jadawel/modules/core/components/workspace/WorkspaceSearchModal.vue'
import AppUtilities from '@jadawel/modules/core/components/AppUtilities.vue'
import {
  CORE_ACTION_SCOPES,
  getSidebarActionScopes,
} from '@jadawel/modules/core/utils/undoRedoConstants'
import {
  isOsSpecificModifierPressed,
  keyboardShortcutsToPriorityEventBus,
} from '@jadawel/modules/core/utils/events'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import { SIDEBAR_TYPES } from '@jadawel/modules/core/utils/constants'

const store = useStore()
const { $registry, $priorityBus, $realtime, $bus } = useNuxtApp()

const col1Width = ref(240)
const col3Width = ref(400)
const col3Visible = ref(false)
const app = ref()

const workspaceSearchModal = ref(null)

const workspaces = computed(() => store.getters['workspace/getAll'])
const selectedWorkspace = computed(() => store.getters['workspace/getSelected'])
const applications = computed(() => store.getters['application/getAll'])

const isCollapsed = computed(() => col1Width.value < 170)
const MOBILE_LAYOUT_BREAKPOINT = 700

const route = useRoute()
const router = useRouter()

// Pages can render an alternative sidebar via
// `definePageMeta({ sidebarType: SIDEBAR_TYPES.ALL_WORKSPACES })`.
const sidebarType = computed(
  () => route.meta.sidebarType ?? SIDEBAR_TYPES.WORKSPACE
)

// The sidebar decides which workspace and application level actions the user
// can undo, so the corresponding scopes follow it and the store selections here
// rather than in every page. The selections stay in the store when navigating
// to a page that doesn't select anything (settings, the homepage), so the
// scopes are re-derived from them whenever the sidebar changes.
const selectedApplication = computed(
  () => store.getters['application/getSelected']
)
watch(
  () => [
    sidebarType.value,
    selectedWorkspace.value?.id ?? null,
    selectedApplication.value?.id ?? null,
  ],
  ([type, workspaceId, applicationId]) => {
    store.dispatch(
      'undoRedo/updateCurrentScopeSet',
      getSidebarActionScopes({ sidebarType: type, workspaceId, applicationId })
    )
  },
  { immediate: true }
)

// The all workspaces sidebar shows no selected application, and application
// types redirect away on delete while their application is still selected, so
// the selection of a previously opened application must not linger.
watch(sidebarType, (type) => {
  if (type === SIDEBAR_TYPES.ALL_WORKSPACES) {
    store.dispatch('application/unselect')
  }
})

// The right sidebar contains workspace specific components, like the assistant, so
// it must not render on pages without a workspace context. The open state is kept,
// so it shows again when navigating back to a workspace page.
const col3Shown = computed(
  () => col3Visible.value && sidebarType.value === 'workspace'
)

// Preserve authentication logic
if (route.query.token) {
  const newQuery = { ...route.query }
  delete newQuery.token
  router.replace({ query: newQuery })
}

function openWorkspaceSearch() {
  if (selectedWorkspace.value?.id && workspaceSearchModal.value) {
    workspaceSearchModal.value.show()
  }
}

function resizeCol1(v) {
  col1Width.value = v
}
function resizeCol3(v) {
  col3Width.value = v
}

function syncMobileLayout() {
  if (window.innerWidth <= MOBILE_LAYOUT_BREAKPOINT) {
    col1Width.value = 52
  } else if (col1Width.value === 52) {
    col1Width.value = 240
  }
}

function toggleRightSidebar(value = !col3Visible.value) {
  col3Visible.value = value
  localStorage.setItem('jadawel.rightSidebarOpen', col3Visible.value)
}

function keyDown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    openWorkspaceSearch()
    return
  }

  if (isOsSpecificModifierPressed(event) && event.key.toLowerCase() === 'z') {
    const el = document.activeElement
    const avoid =
      ['input', 'textarea', 'select'].includes(el.tagName.toLowerCase()) ||
      el.isContentEditable

    if (!avoid) {
      const actionName = event.shiftKey ? 'undoRedo/redo' : 'undoRedo/undo'
      store.dispatch(actionName, { showLoadingToast: true }).catch(notifyIf)
      event.preventDefault()
    }
  }

  keyboardShortcutsToPriorityEventBus(event, $priorityBus)
}

onMounted(() => {
  $realtime.connect()

  syncMobileLayout()
  window.addEventListener('resize', syncMobileLayout)

  const handler = (e) => keyDown(e)
  document.body.addEventListener('keydown', handler)
  //nuxtApp.$el = { keydownEvent: handler }
  app.value.keydownEvent = handler

  store.dispatch('undoRedo/updateCurrentScopeSet', CORE_ACTION_SCOPES.root())

  store.dispatch('job/initializePoller')

  $bus.$on('toggle-right-sidebar', toggleRightSidebar)
})

onBeforeUnmount(() => {
  $realtime.disconnect()
  window.removeEventListener('resize', syncMobileLayout)

  if (app.value?.keydownEvent) {
    document.body.removeEventListener('keydown', app.value?.keydownEvent)
  }

  store.dispatch(
    'undoRedo/updateCurrentScopeSet',
    CORE_ACTION_SCOPES.root(false)
  )

  $bus.$off('toggle-right-sidebar', toggleRightSidebar)
})

const appLayoutComponents = computed(() => {
  return Object.values($registry.getAll('plugin'))
    .map((plugin) => plugin.getAppLayoutComponent())
    .filter((component) => component !== null)
})
</script>
