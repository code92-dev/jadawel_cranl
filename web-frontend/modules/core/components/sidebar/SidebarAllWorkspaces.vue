<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <component
      :is="component"
      v-for="(component, index) in impersonateComponent"
      :key="index"
    ></component>
    <!--
      Jadawel: the name leads to this homepage, as it does inside a workspace,
      and the arrows beside it open the menu (workspaces, settings, log out).
      Collapsed, only the avatar is left, so it opens the menu.
    -->
    <div ref="userContextAnchor" class="sidebar__workspaces-selector">
      <a
        v-if="collapsed"
        class="sidebar__workspaces-selector-link"
        @click="toggleUserContext()"
      >
        <Avatar :initials="$filters.nameAbbreviation(name)"></Avatar>
      </a>
      <nuxt-link
        v-else
        class="sidebar__workspaces-selector-link"
        :to="{ name: 'all-workspaces' }"
      >
        <Avatar :initials="$filters.nameAbbreviation(name)"></Avatar>
        <span class="sidebar__workspaces-selector-selected-workspace">{{
          name
        }}</span>
        <span
          v-if="unreadNotificationsInAnyWorkspace"
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
        @click="toggleUserContext()"
        @keydown.enter.prevent="toggleUserContext()"
        @keydown.space.prevent="toggleUserContext()"
      >
        <i
          class="sidebar__workspaces-selector-icon jadawel-icon-up-down-arrows"
        ></i>
      </a>
    </div>
    <SidebarUserContext
      ref="userContext"
      :workspaces="workspaces"
      :selected-workspace="selectedWorkspace"
    ></SidebarUserContext>

    <SidebarAllWorkspacesMenu v-show="!collapsed"></SidebarAllWorkspacesMenu>

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
import SidebarAllWorkspacesMenu from '@jadawel/modules/core/components/sidebar/SidebarAllWorkspacesMenu'
import SidebarFoot from '@jadawel/modules/core/components/sidebar/SidebarFoot'

export default {
  name: 'SidebarAllWorkspaces',
  components: {
    SidebarUserContext,
    SidebarAllWorkspacesMenu,
    SidebarFoot,
  },
  props: {
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
  },
  emits: ['set-col1-width'],
  computed: {
    impersonateComponent() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getImpersonateComponent())
        .filter((component) => component !== null)
    },
    ...mapGetters({
      name: 'auth/getName',
      unreadNotificationsInAnyWorkspace: 'notification/anyWorkspaceWithUnread',
    }),
  },
  methods: {
    toggleUserContext() {
      this.$refs.userContext.toggle(
        this.$refs.userContextAnchor,
        'bottom',
        'left',
        4,
        16
      )
    },
  },
}
</script>
