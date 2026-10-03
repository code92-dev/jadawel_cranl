<template>
  <div class="layout__col-2-scroll layout__col-2-scroll--white-background">
    <div class="workspace-members">
      <div class="workspace-members__header">
        <h1 class="workspace-members__title">
          {{ $t('workspaceMembers.title') }}
        </h1>
        <Button
          v-if="adminWorkspaces.length > 0"
          type="primary"
          icon="iconoir-add-user"
          tag="a"
          @click="invite(null)"
          >{{ $t('workspaceMembers.invite') }}</Button
        >
        <AppUtilities></AppUtilities>
      </div>

      <div class="workspace-members__boxes">
        <section
          v-for="workspace in workspaces"
          :key="workspace.id"
          class="workspace-box workspace-members__box"
        >
          <div class="workspace-box__header">
            <a class="workspace-box__avatar-link" @click="open(workspace)">
              <Avatar
                :initials="initialOf(workspace.name)"
                color="blue"
                size="x-large"
              ></Avatar>
            </a>
            <div class="workspace-box__title">
              <div class="workspace-box__name-row">
                <div class="workspace-box__name" @click="open(workspace)">
                  {{ workspace.name }}
                </div>
                <span
                  v-if="roleName(workspace.permissions)"
                  class="workspace-box__role"
                  >{{ roleName(workspace.permissions) }}</span
                >
              </div>
              <div class="workspace-box__meta">
                <span class="workspace-box__meta-text">{{
                  $t('allWorkspaces.membersCount', {
                    count: workspace.users?.length ?? 0,
                  })
                }}</span>
              </div>
            </div>
            <div v-if="isAdmin(workspace)" class="workspace-box__actions">
              <Button
                class="workspace-box__action"
                type="secondary"
                size="tiny"
                icon="iconoir-add-user"
                tag="a"
                @click="invite(workspace)"
                >{{ $t('workspaceMembers.inviteShort') }}</Button
              >
              <Button
                class="workspace-box__action"
                type="secondary"
                size="tiny"
                tag="a"
                @click="manage(workspace)"
                >{{ $t('workspaceMembers.manage') }}</Button
              >
            </div>
          </div>

          <ul v-if="isAdmin(workspace)" class="workspace-members__list">
            <li
              v-for="member in membersOf(workspace)"
              :key="member.id"
              class="workspace-members__member"
            >
              <Avatar
                :initials="initialOf(member.name || member.email)"
                size="large"
              ></Avatar>
              <div class="workspace-members__member-details">
                <div class="workspace-members__member-name">
                  {{ member.name || member.email }}
                  <span
                    v-if="member.user_id === userId"
                    class="workspace-members__you"
                    >{{ $t('workspaceMembers.you') }}</span
                  >
                </div>
                <div class="workspace-members__member-email">
                  {{ member.email }}
                </div>
              </div>
              <span class="workspace-members__member-role">{{
                roleName(member.permissions)
              }}</span>
            </li>
          </ul>
          <p v-else class="workspace-members__hidden">
            {{ $t('workspaceMembers.adminsOnly') }}
          </p>
        </section>
      </div>
    </div>

    <WorkspaceMemberInviteModal
      ref="inviteModal"
      :workspace="inviteWorkspace"
      :workspaces="workspaces"
      @invite-submitted="invited"
    ></WorkspaceMemberInviteModal>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { useHead, useNuxtApp } from '#imports'

import AppUtilities from '@jadawel/modules/core/components/AppUtilities'
import WorkspaceMemberInviteModal from '@jadawel/modules/core/components/workspace/WorkspaceMemberInviteModal'
import { getRoleTranslations } from '@jadawel/modules/core/store/workspace'
import { SIDEBAR_TYPES } from '@jadawel/modules/core/utils/constants'
import { collatedStringCompare } from '@jadawel/modules/core/utils/string'

definePageMeta({
  layout: 'app',
  sidebarType: SIDEBAR_TYPES.ALL_WORKSPACES,
  middleware: [
    'settings',
    'authenticated',
    'impersonate',
    'workspacesAndApplications',
  ],
})

/**
 * Every workspace with its members, reached from the app-wide tools menu and
 * the workspaces sidebar. Listing members is admin only, so a workspace where
 * the user is not an admin shows its member count without the names. Changing
 * roles and removing members stay on the workspace's own members page
 * ("Manage").
 */
const store = useStore()
const router = useRouter()
const { $registry, $i18n } = useNuxtApp()

const inviteModal = ref(null)
const inviteWorkspace = ref(null)

const workspaces = computed(() => store.getters['workspace/getAllSorted'])
const userId = computed(() => store.getters['auth/getUserId'])
const roleTranslations = computed(() => getRoleTranslations($registry))

const adminWorkspaces = computed(() =>
  workspaces.value.filter((workspace) => isAdmin(workspace))
)

function isAdmin(workspace) {
  return workspace.permissions === 'ADMIN'
}

function roleName(uid) {
  return roleTranslations.value[uid]?.name ?? ''
}

function initialOf(name) {
  return (name || '?').trim().charAt(0).toUpperCase()
}

// The user first, then everyone else by name.
function membersOf(workspace) {
  return [...(workspace.users || [])].sort((a, b) => {
    if (a.user_id === userId.value) return -1
    if (b.user_id === userId.value) return 1
    return collatedStringCompare(a.name || a.email, b.name || b.email, 'ASC')
  })
}

function open(workspace) {
  router.push({ name: 'workspace', params: { workspaceId: workspace.id } })
}

function manage(workspace) {
  router.push({
    name: 'settings-members',
    params: { workspaceId: workspace.id },
  })
}

function invite(workspace) {
  inviteWorkspace.value = workspace
  inviteModal.value.show()
}

function invited(workspace) {
  store.dispatch('toast/success', {
    title: $i18n.t('sidebar.inviteSent', { name: workspace.name }),
  })
}

useHead(() => ({
  title: $i18n.t('workspaceMembers.title'),
}))
</script>
