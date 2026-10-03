<template>
  <Modal ref="modal">
    <h2 class="box__title">
      {{ $t('membersSettings.membersInviteModal.title') }}
    </h2>
    <Error :error="error"></Error>
    <!--
      Jadawel: opened from the app-wide tools menu, the modal is given every
      workspace and lets the user choose which one to invite to. Only the
      workspaces where they may invite are offered.
    -->
    <template v-if="workspaces">
      <div v-if="preparing" class="loading margin-bottom-2"></div>
      <p v-else-if="invitableWorkspaces.length === 0">
        {{ $t('membersSettings.membersInviteModal.noInvitableWorkspace') }}
      </p>
      <FormGroup
        v-else
        small-label
        :label="$t('membersSettings.membersInviteModal.workspace')"
        required
        class="margin-bottom-2"
      >
        <Dropdown
          v-model="chosenWorkspaceId"
          class="workspace-member-invite-modal__workspace"
          :show-search="invitableWorkspaces.length > 5"
          fixed-items
        >
          <DropdownItem
            v-for="option in invitableWorkspaces"
            :key="option.id"
            :name="option.name"
            :value="option.id"
          ></DropdownItem>
        </Dropdown>
      </FormGroup>
    </template>
    <WorkspaceInviteForm
      v-if="targetWorkspace && !preparing"
      ref="inviteForm"
      :key="targetWorkspace.id"
      :workspace="targetWorkspace"
      @submitted="inviteSubmitted"
    >
      <template #default>
        <div class="col col-12 align-right margin-top-2">
          <Button
            type="primary"
            :loading="inviteLoading"
            :disabled="inviteLoading"
          >
            {{ $t('membersSettings.membersInviteModal.submit') }}
          </Button>
        </div>
      </template>
      <template #roleSelectorLabel>
        <HelpIcon
          class="margin-right-1"
          :tooltip="$t('membersSettings.membersInviteModal.helpIconText')"
        />
      </template>
    </WorkspaceInviteForm>
  </Modal>
</template>

<script>
import modal from '@jadawel/modules/core/mixins/modal'
import error from '@jadawel/modules/core/mixins/error'
import WorkspaceInviteForm from '@jadawel/modules/core/components/workspace/WorkspaceInviteForm'
import WorkspaceService from '@jadawel/modules/core/services/workspace'
import { ResponseErrorMessage } from '@jadawel/modules/core/plugins/clientHandler'

export default {
  name: 'MembersInviteModal',
  components: { WorkspaceInviteForm },
  mixins: [modal, error],
  props: {
    /**
     * The workspace to invite to, or the one preselected when `workspaces` is
     * given.
     */
    workspace: {
      type: Object,
      required: false,
      default: null,
    },
    /**
     * Jadawel: when given, the user picks the workspace from these.
     */
    workspaces: {
      type: Array,
      required: false,
      default: null,
    },
  },
  emits: ['invite-submitted'],
  data() {
    return {
      inviteLoading: false,
      preparing: false,
      chosenWorkspaceId: null,
    }
  },
  computed: {
    invitableWorkspaces() {
      return (this.workspaces || []).filter(
        (workspace) =>
          workspace._.permissionsLoaded &&
          workspace._.rolesLoaded &&
          this.$hasPermission(
            'workspace.create_invitation',
            workspace,
            workspace.id
          )
      )
    },
    targetWorkspace() {
      if (!this.workspaces) {
        return this.workspace
      }
      return (
        this.invitableWorkspaces.find(
          (workspace) => workspace.id === this.chosenWorkspaceId
        ) || null
      )
    },
  },
  methods: {
    async show(...args) {
      this.hideError()
      modal.methods.show.call(this, ...args)
      if (this.workspaces) {
        await this.prepareWorkspaces()
      }
    },
    /**
     * Whether the user may invite, and with which roles, is only loaded for the
     * workspace that is open, so it is loaded here for the others. Workspaces
     * where they are not an admin are skipped: inviting is admin only.
     */
    async prepareWorkspaces() {
      this.preparing = true
      try {
        await Promise.all(
          this.workspaces
            .filter((workspace) => workspace.permissions === 'ADMIN')
            .map(async (workspace) => {
              await this.$store.dispatch(
                'workspace/fetchPermissions',
                workspace
              )
              await this.$store.dispatch('workspace/fetchRoles', workspace)
            })
        )
      } catch (error) {
        this.handleError(error, 'workspace')
      } finally {
        this.preparing = false
      }
      const ids = this.invitableWorkspaces.map((workspace) => workspace.id)
      if (!ids.includes(this.chosenWorkspaceId)) {
        this.chosenWorkspaceId = ids.includes(this.workspace?.id)
          ? this.workspace.id
          : (ids[0] ?? null)
      }
    },
    async inviteSubmitted(values) {
      const workspace = this.targetWorkspace
      this.inviteLoading = true
      this.hideError()

      try {
        // The public accept url is the page where the user can publicly navigate too,
        // to accept the workspace invitation.
        const acceptUrl = `${this.$config.public.jadawelEmbeddedShareUrl}/workspace-invitation`
        const { data } = await WorkspaceService(this.$client).sendInvitation(
          workspace.id,
          acceptUrl,
          values
        )
        this.$bus.$emit('invite-submitted', data)
        this.$emit('invite-submitted', workspace)
        this.hide()
      } catch (error) {
        this.handleError(error, 'workspace', {
          ERROR_GROUP_USER_ALREADY_EXISTS: new ResponseErrorMessage(
            this.$t(
              'membersSettings.membersInviteModal.errors.userAlreadyInWorkspace.title'
            ),
            this.$t(
              'membersSettings.membersInviteModal.errors.userAlreadyInWorkspace.text'
            )
          ),
        })
      }

      this.inviteLoading = false
    },
  },
}
</script>
