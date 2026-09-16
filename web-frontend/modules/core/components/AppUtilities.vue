<template>
  <!--
    Jadawel: workspace utilities pinned to the top inline-end corner of the
    content area — the top-left in Arabic. Rendered once by the app layout
    rather than by each page header, because there are five separate header
    components (table, dashboard, automation, builder, workspace home) and the
    group has to appear on all of them. `.layout__col-2-1` and
    `.dashboard__header` reserve the band with a padding, so this never lands on
    top of the header's own controls.

    There is deliberately no search icon here: the view header already carries
    one, and two magnifiers in the same bar is exactly the duplication this
    layout is meant to remove. Global search stays on Ctrl/⌘ K.
  -->
  <div class="app-utilities">
    <a
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
          v-if="
            $hasPermission(
              'workspace.list_workspace_users',
              workspace,
              workspace.id
            )
          "
          v-slot="{ href, navigate }"
          custom
          :to="{
            name: 'settings-members',
            params: { workspaceId: workspace.id },
          }"
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
              {{ membersTooltip }}
            </a>
          </li>
        </nuxt-link>

        <li
          v-if="
            $hasPermission(
              'workspace.create_invitation',
              workspace,
              workspace.id
            )
          "
          class="context__menu-item"
          role="none"
        >
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

    <NotificationPanel ref="notificationPanel" />
    <WorkspaceMemberInviteModal
      ref="inviteModal"
      :workspace="workspace"
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
    workspace: {
      type: Object,
      required: true,
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
     * The member count used to sit next to a text label. An icon has no room
     * for it, so it moves into the tooltip rather than being dropped.
     */
    membersTooltip() {
      const label = this.$t('sidebar.members')
      const count = this.workspace.users?.length
      return count ? `${label} (${count})` : label
    },
    ...mapGetters({
      unreadNotificationCount: 'notification/getUnreadCount',
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
    handleInvite() {
      if (this.$route.name !== 'settings-invites') {
        this.$router.push({
          name: 'settings-invites',
          params: { workspaceId: this.workspace.id },
        })
      }
    },
  },
}
</script>
