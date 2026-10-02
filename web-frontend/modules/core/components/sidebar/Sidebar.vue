<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <component
      :is="component"
      v-for="(component, index) in impersonateComponent"
      :key="index"
    ></component>
    <template v-if="showAdmin">
      <div class="sidebar__head">
        <a class="sidebar__back" @click="leaveAdmin()">
          <i class="iconoir-nav-arrow-left"></i>
        </a>
        <div v-show="!collapsed" class="sidebar__title">
          {{ $t('sidebar.adminSettings') }}
        </div>
      </div>
      <SidebarAdmin v-show="!collapsed"></SidebarAdmin>
    </template>
    <template v-if="!showAdmin">
      <div
        ref="workspaceContextAnchor"
        class="sidebar__workspaces-selector"
        data-highlight="workspaces"
      >
        <nuxt-link
          v-show="!collapsed"
          v-tooltip="$t('sidebar.backToHome')"
          tooltip-position="right"
          tooltip-no-arrow
          tooltip-show-delay="500"
          class="sidebar__back"
          :aria-label="$t('sidebar.backToHome')"
          :to="{ name: 'all-workspaces' }"
        >
          <i class="iconoir-nav-arrow-left"></i>
        </nuxt-link>
        <!--
          Jadawel: the name leads to the workspaces homepage and the arrows
          beside it open the menu (other workspaces, settings, log out).
          Collapsed, only the avatar is left, so it opens the menu.
        -->
        <a
          v-if="collapsed"
          class="sidebar__workspaces-selector-link"
          @click="toggleWorkspacesContext()"
        >
          <Avatar
            :initials="
              $filters.nameAbbreviation(selectedWorkspace.name || name)
            "
          ></Avatar>
        </a>
        <nuxt-link
          v-else
          class="sidebar__workspaces-selector-link"
          :to="{ name: 'all-workspaces' }"
        >
          <Avatar
            :initials="
              $filters.nameAbbreviation(selectedWorkspace.name || name)
            "
          ></Avatar>
          <span class="sidebar__workspaces-selector-selected-workspace">{{
            selectedWorkspace.name || name
          }}</span>
          <span
            v-if="unreadNotificationsInOtherWorkspaces"
            class="sidebar__unread-notifications-icon"
          ></span>
        </nuxt-link>
        <a
          v-show="!collapsed"
          v-tooltip="$t('sidebar.openWorkspacesMenu')"
          tooltip-position="right"
          tooltip-no-arrow
          tooltip-show-delay="500"
          class="sidebar__workspaces-selector-toggle"
          role="button"
          tabindex="0"
          :aria-label="$t('sidebar.openWorkspacesMenu')"
          @click="toggleWorkspacesContext()"
          @keydown.enter.prevent="toggleWorkspacesContext()"
          @keydown.space.prevent="toggleWorkspacesContext()"
        >
          <i
            class="sidebar__workspaces-selector-icon jadawel-icon-up-down-arrows"
          ></i>
        </a>
      </div>
      <SidebarUserContext
        ref="workspacesContext"
        :workspaces="workspaces"
        :selected-workspace="selectedWorkspace"
        @toggle-admin="setShowAdmin($event)"
      ></SidebarUserContext>

      <SidebarMenu
        v-show="!collapsed"
        v-if="hasSelectedWorkspace"
        :selected-workspace="selectedWorkspace"
        :right-sidebar-open="rightSidebarOpen"
      ></SidebarMenu>

      <SidebarWithWorkspace
        v-show="!collapsed"
        v-if="hasSelectedWorkspace"
        :applications="applications"
        :selected-workspace="selectedWorkspace"
      ></SidebarWithWorkspace>

      <SidebarWithoutWorkspace
        v-show="!collapsed"
        v-if="!hasSelectedWorkspace"
        :workspaces="workspaces"
      ></SidebarWithoutWorkspace>
    </template>
    <SidebarFoot
      :collapsed="collapsed"
      :width="width"
      @set-col1-width="$emit('set-col1-width', $event)"
    ></SidebarFoot>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import SidebarUserContext from '@jadawel/modules/core/components/sidebar/SidebarUserContext'
import SidebarWithWorkspace from '@jadawel/modules/core/components/sidebar/SidebarWithWorkspace'
import SidebarWithoutWorkspace from '@jadawel/modules/core/components/sidebar/SidebarWithoutWorkspace'
import SidebarAdmin from '@jadawel/modules/core/components/sidebar/SidebarAdmin'
import SidebarFoot from '@jadawel/modules/core/components/sidebar/SidebarFoot'
import SidebarMenu from '@jadawel/modules/core/components/sidebar/SidebarMenu'
import SidebarAdminItem from './SidebarAdminItem.vue'

export default {
  name: 'Sidebar',
  components: {
    SidebarAdmin,
    SidebarWithoutWorkspace,
    SidebarWithWorkspace,
    SidebarUserContext,
    SidebarMenu,
    SidebarFoot,
  },
  props: {
    applications: {
      type: Array,
      required: true,
    },
    workspaces: {
      type: Array,
      required: true,
    },
    selectedWorkspace: {
      type: Object,
      required: true,
    },
    collapsed: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    width: {
      type: Number,
      required: false,
      default: 240,
    },
    rightSidebarOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['set-col1-width'],
  data() {
    return {
      showAdmin: false,
    }
  },

  computed: {
    SidebarAdminItem() {
      return SidebarAdminItem
    },
    impersonateComponent() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getImpersonateComponent())
        .filter((component) => component !== null)
    },
    hasSelectedWorkspace() {
      return Object.prototype.hasOwnProperty.call(this.selectedWorkspace, 'id')
    },
    ...mapGetters({
      name: 'auth/getName',
      unreadNotificationsInOtherWorkspaces:
        'notification/anyOtherWorkspaceWithUnread',
    }),
  },
  created() {
    // Checks whether the rendered page is an admin page. If so, switch the left sidebar
    // navigation to the admin.
    this.showAdmin = Object.values(this.$registry.getAll('admin')).some(
      (adminType) => {
        return this.$route.matched.some(
          ({ name }) => name === adminType.routeName
        )
      }
    )
  },
  methods: {
    toggleWorkspacesContext() {
      this.$refs.workspacesContext.toggle(
        this.$refs.workspaceContextAnchor,
        'bottom',
        'left',
        4,
        16
      )
    },
    setShowAdmin(value) {
      this.showAdmin = value
      this.$forceUpdate()
    },
    /**
     * If no workspace is selected, for example when an admin page was loaded
     * directly, then toggling back would show an empty workspace sidebar, so the
     * user is navigated to the all workspaces homepage instead.
     */
    leaveAdmin() {
      if (this.hasSelectedWorkspace) {
        this.setShowAdmin(false)
      } else {
        this.$router.push({ name: 'all-workspaces' })
      }
    },
  },
}
</script>
