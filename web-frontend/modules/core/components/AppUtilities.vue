<template>
  <!--
    Jadawel: workspace utilities pinned to the top inline-end corner of the
    content area — the top-left in Arabic. Rendered once by the app layout
    rather than by each page header, because there are five separate header
    components (table, dashboard, automation, builder, workspace home) and the
    group has to appear on all of them. `.layout__col-2-1` and
    `.dashboard__header` reserve the band with a padding, so this never lands on
    top of the header's own controls.

    The tools apply to the whole system, so the pages that span every
    workspace (the homepage, recently viewed, members) have them too, without a
    workspace (`workspace` is null): Members and Invite cover every workspace,
    and the notifications, which belong to one workspace, are left out. Those
    pages scroll as a whole, so they place the tools in their own header row
    rather than in a corner the content would scroll under.

    There is deliberately no search icon here: the view header already carries
    one, and two magnifiers in the same bar is exactly the duplication this
    layout is meant to remove. Global search stays on Ctrl/⌘ K.
  -->
  <div class="app-utilities" :class="{ 'app-utilities--inline': !workspace }">
    <a
      v-if="workspace"
      v-tooltip="$t('sidebar.notifications')"
      class="app-utilities__item"
      :aria-label="$t('sidebar.notifications')"
      @click="$refs.notificationPanel.toggle($event.currentTarget)"
    >
      <i class="iconoir-bell"></i>
      <BadgeCounter
        v-show="unreadNotificationCount"
        class="app-utilities__badge"
        :count="unreadNotificationCount"
        :limit="10"
      >
      </BadgeCounter>
    </a>

    <a
      ref="utilitiesAnchor"
      v-tooltip="$t('sidebar.quickTools')"
      class="app-utilities__item"
      :class="{ 'app-utilities__item--active': utilitiesOpen }"
      :aria-label="$t('sidebar.quickTools')"
      aria-haspopup="menu"
      :aria-expanded="utilitiesOpen"
      data-highlight="workspace-utilities"
      @click="
        $refs.utilitiesContext.toggle(
          $refs.utilitiesAnchor,
          'bottom',
          'left',
          8,
          0
        )
      "
    >
      <i class="iconoir-view-grid"></i>
    </a>

    <Context
      ref="utilitiesContext"
      class="app-utilities__context"
      @shown="utilitiesOpen = true"
      @hidden="utilitiesOpen = false"
    >
      <div class="context__menu-title app-utilities__context-title">
        {{ $t('sidebar.quickTools') }}
      </div>
      <ul class="context__menu app-utilities__menu" role="menu">
        <nuxt-link
          v-slot="{ href, navigate }"
          custom
          :to="{ name: 'arabase-workspace-members' }"
        >
          <li class="context__menu-item" role="none">
            <a
              :href="href"
              class="context__menu-item-link"
              role="menuitem"
              data-highlight="members"
              @click="openMembers(navigate, $event)"
            >
              <i class="context__menu-item-icon iconoir-group"></i>
              {{ $t('sidebar.members') }}
            </a>
          </li>
        </nuxt-link>

        <li v-if="canInviteSomewhere" class="context__menu-item" role="none">
          <a
            class="context__menu-item-link"
            role="menuitem"
            @click="showInviteModal"
          >
            <i class="context__menu-item-icon iconoir-add-user"></i>
            {{ $t('sidebar.inviteOthers') }}
          </a>
        </li>

        <li class="context__menu-item" role="none">
          <a
            class="context__menu-item-link"
            role="menuitem"
            @click="showTrashModal"
          >
            <i class="context__menu-item-icon iconoir-bin"></i>
            {{ $t('sidebar.trash') }}
          </a>
        </li>

        <component
          :is="component"
          v-for="(component, index) in pluginUtilityComponents"
          :key="`plugin-utility-${index}`"
          :workspace="workspace"
          @close="$refs.utilitiesContext.hide()"
        />
      </ul>

      <div class="app-utilities__theme">
        <div class="app-utilities__theme-heading">
          <i class="iconoir-palette"></i>
          {{ $t('interfaceTheme.title') }}
        </div>
        <div
          class="app-utilities__theme-options"
          :aria-label="$t('interfaceTheme.title')"
          role="radiogroup"
        >
          <button
            v-for="theme in interfaceThemes"
            :key="theme.id"
            v-tooltip="theme.label"
            class="app-utilities__theme-option"
            :class="{
              'app-utilities__theme-option--active': activeTheme === theme.id,
            }"
            :style="{
              '--theme-color': theme.swatch || theme.colors[500],
              '--theme-outline-color': theme.swatchOutline || theme.colors[500],
              '--theme-check-color': theme.checkColor || '#ffffff',
            }"
            type="button"
            role="radio"
            :aria-label="theme.label"
            :aria-checked="activeTheme === theme.id"
            @click="selectTheme(theme.id)"
          >
            <i v-if="activeTheme === theme.id" class="iconoir-check"></i>
          </button>
        </div>
      </div>
    </Context>

    <NotificationPanel v-if="workspace" ref="notificationPanel" />
    <WorkspaceMemberInviteModal
      ref="inviteModal"
      :workspace="workspace"
      :workspaces="workspaces"
      @invite-submitted="handleInvite"
    />
    <TrashModal ref="trashModal" :initial-workspace="workspace"></TrashModal>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import TrashModal from '@jadawel/modules/core/components/trash/TrashModal'
import NotificationPanel from '@jadawel/modules/core/components/NotificationPanel'
import WorkspaceMemberInviteModal from '@jadawel/modules/core/components/workspace/WorkspaceMemberInviteModal'
import BadgeCounter from '@jadawel/modules/core/components/BadgeCounter'
import Context from '@jadawel/modules/core/components/Context'
import {
  applyInterfaceTheme,
  DEFAULT_INTERFACE_THEME,
  initializeInterfaceTheme,
  INTERFACE_THEMES,
  INTERFACE_THEME_STORAGE_KEY,
} from '@jadawel/modules/core/utils/interfaceThemes'

export default {
  name: 'AppUtilities',
  components: {
    TrashModal,
    NotificationPanel,
    WorkspaceMemberInviteModal,
    BadgeCounter,
    Context,
  },
  props: {
    /**
     * The workspace being worked in, or null on the pages that span every
     * workspace (the workspaces homepage, recently viewed, members).
     */
    workspace: {
      type: Object,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      activeTheme: DEFAULT_INTERFACE_THEME,
      utilitiesOpen: false,
    }
  },
  computed: {
    interfaceThemes() {
      return INTERFACE_THEMES.map((theme) => ({
        ...theme,
        label: this.$t(`interfaceTheme.${theme.id}`),
      }))
    },
    /**
     * Tools other modules add through `getWorkspaceUtilityComponents`. They act
     * on the open workspace (Sanad opens beside it), so they need one.
     */
    pluginUtilityComponents() {
      if (!this.workspace) {
        return []
      }
      return Object.values(this.$registry.getAll('plugin')).flatMap(
        (plugin) => plugin.getWorkspaceUtilityComponents(this.workspace) || []
      )
    },
    /**
     * Inviting is admin only, and the user's own role is known for every
     * workspace without loading its permissions.
     */
    canInviteSomewhere() {
      return this.workspaces.some(
        (workspace) => workspace.permissions === 'ADMIN'
      )
    },
    ...mapGetters({
      unreadNotificationCount: 'notification/getUnreadCount',
      workspaces: 'workspace/getAllSorted',
    }),
  },
  mounted() {
    this.activeTheme = initializeInterfaceTheme()
  },
  methods: {
    selectTheme(themeId) {
      this.activeTheme = applyInterfaceTheme(themeId)
      localStorage.setItem(INTERFACE_THEME_STORAGE_KEY, this.activeTheme)
    },
    openMembers(navigate, event) {
      this.$refs.utilitiesContext.hide()
      navigate(event)
    },
    showInviteModal() {
      this.$refs.utilitiesContext.hide()
      this.$refs.inviteModal.show()
    },
    showTrashModal() {
      this.$refs.utilitiesContext.hide()
      this.$refs.trashModal.show()
    },
    /**
     * Shows the pending invitations of the workspace invited to, as before.
     * The members page stays put: it is where the user chose to be.
     */
    handleInvite(workspace) {
      if (this.$route.name === 'arabase-workspace-members') {
        this.$store.dispatch('toast/success', {
          title: this.$t('sidebar.inviteSent', { name: workspace.name }),
        })
        return
      }
      if (this.$route.name !== 'settings-invites') {
        this.$router.push({
          name: 'settings-invites',
          params: { workspaceId: workspace.id },
        })
      }
    },
  },
}
</script>
