<template>
  <main v-if="organization" class="organization-page">
    <h1>{{ organization.name }}</h1>
    <p>
      {{ $t("organizations.status") }}:
      {{ $t(`organizations.statuses.${organization.status}`) }} ·
      {{ $t(`organizations.provisioning.${organization.provisioning_status}`) }}
    </p>
    <p v-if="organization.effective_entitlement">
      {{ $t("organizations.accessSource") }}:
      {{
        $t(`organizations.sources.${organization.effective_entitlement.source}`)
      }}
      · {{ $t("organizations.seats") }}:
      {{ organization.effective_entitlement.seat_limit }}
    </p>
    <p v-if="organization.billing_subscription" role="status">
      {{ $t("organizations.paymentStatus") }}:
      {{
        $t(
          `organizations.subscriptionStatuses.${organization.billing_subscription.status}`,
        )
      }}
      <span v-if="organization.billing_subscription.period_end">
        · {{ $t("organizations.renewalThrough") }}:
        <time>{{
          formatDate(organization.billing_subscription.period_end)
        }}</time>
      </span>
    </p>
    <p v-else role="status">{{ $t("organizations.noPaidRenewal") }}</p>

    <section class="organization-settings">
      <h2>{{ $t("organizations.settings") }}</h2>
      <form
        data-testid="organization-settings-form"
        @submit.prevent="updateSettings"
      >
        <label>
          {{ $t("organizations.name") }}
          <input
            v-model="organizationName"
            required
            maxlength="160"
            class="input"
          />
        </label>
        <Button :disabled="busy">{{ $t("organizations.saveSettings") }}</Button>
      </form>
    </section>

    <section>
      <h2>{{ $t("organizations.members") }}</h2>
      <form class="organization-search" @submit.prevent="loadMembers">
        <label>
          {{ $t("organizations.search") }}
          <input
            v-model.trim="memberSearch"
            type="search"
            :placeholder="$t('organizations.searchMembers')"
          />
        </label>
        <Button type="secondary" :disabled="busy">
          {{ $t("organizations.search") }}
        </Button>
      </form>
      <form @submit.prevent="invite">
        <label>
          {{ $t("organizations.email") }}
          <input
            v-model="email"
            type="email"
            dir="ltr"
            required
            :placeholder="$t('organizations.email')"
            class="input"
          />
        </label>
        <label>
          {{ $t("organizations.role") }}
          <select v-model="role" class="input">
            <option value="member">{{ $t("organizations.member") }}</option>
            <option value="admin">{{ $t("organizations.admin") }}</option>
          </select>
        </label>
        <Button :disabled="busy">
          {{ $t("organizations.sendInvite") }}
        </Button>
      </form>
      <form data-testid="member-add-form" @submit.prevent="addMember">
        <label>
          {{ $t("organizations.userId") }}
          <input
            v-model.number="userId"
            type="number"
            min="1"
            required
            class="input"
          />
        </label>
        <label>
          {{ $t("organizations.role") }}
          <select v-model="addRole" class="input">
            <option value="member">{{ $t("organizations.member") }}</option>
            <option value="admin">{{ $t("organizations.admin") }}</option>
          </select>
        </label>
        <Button :disabled="busy">
          {{ $t("organizations.addMember") }}
        </Button>
      </form>
      <p v-if="token" role="status">
        {{ $t("organizations.invitationToken") }}:
        <code dir="ltr">{{ token }}</code>
      </p>
      <ul>
        <li v-for="member in organization.members" :key="member.id">
          <bdi>{{ member.email }}</bdi> —
          {{ $t(`organizations.roles.${member.role}`) }}
          <select
            v-if="member.role !== 'owner'"
            :value="member.role"
            class="input"
            @change="updateRole(member, $event.target.value)"
          >
            <option value="member">{{ $t("organizations.member") }}</option>
            <option value="admin">{{ $t("organizations.admin") }}</option>
            <option value="owner">{{ $t("organizations.ownerRole") }}</option>
          </select>
          <Button
            v-if="member.role !== 'owner'"
            type="secondary"
            @click="suspend(member, !member.suspended)"
          >
            {{
              member.suspended
                ? $t("organizations.reactivate")
                : $t("organizations.suspend")
            }}
          </Button>
          <Button
            v-if="member.role !== 'owner'"
            type="danger"
            @click="remove(member)"
          >
            {{ $t("organizations.remove") }}
          </Button>
        </li>
      </ul>
      <Button
        v-if="membersNext"
        type="secondary"
        :disabled="busy"
        @click="loadMoreMembers"
      >
        {{ $t("organizations.more") }}
      </Button>
    </section>

    <section>
      <h2>{{ $t("organizations.invitations") }}</h2>
      <form class="organization-search" @submit.prevent="loadInvitations">
        <label>
          {{ $t("organizations.search") }}
          <input
            v-model.trim="invitationSearch"
            type="search"
            :placeholder="$t('organizations.searchInvitations')"
          />
        </label>
        <Button type="secondary" :disabled="busy">
          {{ $t("organizations.search") }}
        </Button>
      </form>
      <p v-if="!invitations.length">{{ $t("organizations.empty") }}</p>
      <ul v-else>
        <li v-for="invitation in invitations" :key="invitation.id">
          <bdi>{{ invitation.email }}</bdi> —
          {{ $t(`organizations.roles.${invitation.role}`) }}
          <span v-if="invitation.accepted_at">{{
            $t("organizations.accepted")
          }}</span>
          <span v-else-if="invitation.revoked_at">{{
            $t("organizations.revoked")
          }}</span>
          <span v-else>{{ $t("organizations.pending") }}</span>
          <Button
            v-if="!invitation.accepted_at && !invitation.revoked_at"
            type="secondary"
            @click="revokeInvitation(invitation)"
          >
            {{ $t("organizations.revokeInvitation") }}
          </Button>
        </li>
      </ul>
      <Button
        v-if="invitationsNext"
        type="secondary"
        :disabled="busy"
        @click="loadMoreInvitations"
      >
        {{ $t("organizations.more") }}
      </Button>
    </section>

    <section>
      <h2>{{ $t("organizations.workspaces") }}</h2>
      <form class="organization-search" @submit.prevent="loadWorkspaces">
        <label>
          {{ $t("organizations.search") }}
          <input
            v-model.trim="workspaceSearch"
            type="search"
            :placeholder="$t('organizations.searchWorkspaces')"
          />
        </label>
        <Button type="secondary" :disabled="busy">
          {{ $t("organizations.search") }}
        </Button>
      </form>
      <form data-testid="workspace-bind-form" @submit.prevent="bindWorkspace">
        <label>
          {{ $t("organizations.workspaceId") }}
          <input
            v-model.number="workspace"
            type="number"
            min="1"
            required
            class="input"
          />
        </label>
        <Button :disabled="busy">
          {{
            workspacePreview
              ? $t("organizations.confirmBindWorkspace")
              : $t("organizations.previewWorkspace")
          }}
        </Button>
      </form>
      <aside v-if="workspacePreview" class="workspace-preview" role="status">
        <p>
          {{ $t("organizations.previewSummary") }}
          {{ workspacePreview.outsiders.length }}
        </p>
        <ul v-if="workspacePreview.outsiders.length">
          <li
            v-for="outsider in workspacePreview.outsiders"
            :key="outsider.user_id"
          >
            <bdi>{{ outsider.user__email }}</bdi>
          </li>
        </ul>
        <p v-if="workspacePreview.pending_invitations.length">
          {{ $t("organizations.pendingInvitations") }}:
          {{ workspacePreview.pending_invitations.length }}
        </p>
        <Button type="secondary" @click="workspacePreview = null">
          {{ $t("organizations.cancel") }}
        </Button>
      </aside>
      <ul>
        <li v-for="binding in organization.workspaces" :key="binding.id">
          <bdi>{{ binding.workspace.name }}</bdi>
          <span> — {{ binding.assigned_members }}</span>
          <ul
            v-if="binding.assignments && binding.assignments.length"
            class="workspace-assignments"
          >
            <li
              v-for="assignment in binding.assignments"
              :key="assignment.membership_id"
            >
              <bdi>{{ assignment.email }}</bdi> —
              {{
                $t(
                  `organizations.workspacePermissions.${assignment.permissions.toLowerCase()}`,
                )
              }}
              <Button
                type="danger"
                data-testid="unassign-workspace-member"
                @click="unassignWorkspace(binding, assignment)"
              >
                {{ $t("organizations.unassignWorkspaceMember") }}
              </Button>
            </li>
          </ul>
          <form @submit.prevent="assignWorkspace(binding)">
            <label>
              {{ $t("organizations.assignmentMember") }}
              <select
                v-model.number="assignmentMembers[binding.id]"
                required
                class="input"
              >
                <option
                  v-for="member in activeMembers"
                  :key="member.id"
                  :value="member.id"
                  dir="auto"
                >
                  {{ member.email }}
                </option>
              </select>
            </label>
            <label>
              {{ $t("organizations.workspacePermission") }}
              <select
                v-model="assignmentPermissions[binding.id]"
                required
                class="input"
              >
                <option value="ADMIN">
                  {{ $t("organizations.workspaceAdmin") }}
                </option>
                <option value="MEMBER">
                  {{ $t("organizations.workspaceMember") }}
                </option>
                <option value="VIEWER">
                  {{ $t("organizations.workspaceViewer") }}
                </option>
              </select>
            </label>
            <Button :disabled="busy">
              {{ $t("organizations.assign") }}
            </Button>
          </form>
          <Button type="danger" @click="unbindWorkspace(binding)">
            {{ $t("organizations.unbindWorkspace") }}
          </Button>
        </li>
      </ul>
      <Button
        v-if="workspacesNext"
        type="secondary"
        :disabled="busy"
        @click="loadMoreWorkspaces"
      >
        {{ $t("organizations.more") }}
      </Button>
    </section>

    <section>
      <h2>{{ $t("organizations.lifecycle") }}</h2>
      <Button type="secondary" @click="changeLifecycle('suspend')">
        {{ $t("organizations.suspend") }}
      </Button>
      <Button type="secondary" @click="changeLifecycle('reactivate')">
        {{ $t("organizations.reactivate") }}
      </Button>
      <Button type="danger" @click="changeLifecycle('archive')">
        {{ $t("organizations.archive") }}
      </Button>
    </section>

    <section>
      <h2>{{ $t("organizations.transition") }}</h2>
      <p>{{ $t("organizations.transitionNote") }}</p>
      <Button type="secondary" :disabled="busy" @click="transitionToPersonal">
        {{ $t("organizations.transitionToPersonal") }}
      </Button>
    </section>

    <p v-if="error" role="alert">{{ $t("organizations.error") }}</p>
  </main>
  <p v-else-if="error" role="alert">{{ $t("organizations.error") }}</p>
  <p v-else role="status">{{ $t("organizations.loading") }}</p>
</template>

<script>
export default {
  name: "OrganizationDetail",
  layout: "app",
  middleware: "authenticated",
  props: {
    routeOrganizationId: { type: String, default: "" },
  },
  data() {
    return {
      organization: null,
      organizationName: "",
      invitations: [],
      invitationsNext: null,
      invitationSearch: "",
      membersNext: null,
      memberSearch: "",
      workspacesNext: null,
      workspaceSearch: "",
      email: "",
      role: "member",
      userId: null,
      addRole: "member",
      token: "",
      workspace: null,
      workspacePreview: null,
      assignmentMembers: {},
      assignmentPermissions: {},
      busy: false,
      error: false,
    };
  },
  computed: {
    currentOrganizationId() {
      return this.routeOrganizationId || this.$route?.params?.id || "";
    },
    activeMembers() {
      return (this.organization?.members || []).filter(
        (member) => !member.suspended,
      );
    },
  },
  async mounted() {
    await this.load();
  },
  methods: {
    formatDate(value) {
      return value ? new Date(value).toLocaleString(this.$i18n.locale) : "";
    },
    async load() {
      try {
        const [organization, invitations, members, workspaces] =
          await Promise.all([
            this.$client.get(`/organizations/${this.currentOrganizationId}/`),
            this.$client.get(
              `/organizations/${this.currentOrganizationId}/invitations/`,
            ),
            this.$client.get(
              `/organizations/${this.currentOrganizationId}/members/`,
            ),
            this.$client.get(
              `/organizations/${this.currentOrganizationId}/workspaces/`,
            ),
          ]);
        this.organization = organization.data;
        this.organizationName = organization.data.name;
        this.invitations = invitations.data.results || invitations.data;
        this.invitationsNext = invitations.data.next || null;
        const memberData = members.data;
        this.organization.members = memberData.results || memberData;
        this.membersNext = memberData.next || null;
        const workspaceData = workspaces.data;
        this.organization.workspaces = workspaceData.results || workspaceData;
        this.workspacesNext = workspaceData.next || null;
      } catch {
        this.error = true;
      }
    },
    async run(action) {
      this.busy = true;
      this.error = false;
      try {
        await action();
        await this.load();
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async loadMembers() {
      const { data } = await this.$client.get(
        `/organizations/${this.currentOrganizationId}/members/`,
        { params: this.memberSearch ? { search: this.memberSearch } : {} },
      );
      this.organization.members = data.results || data;
      this.membersNext = data.next || null;
    },
    async loadInvitations() {
      const { data } = await this.$client.get(
        `/organizations/${this.currentOrganizationId}/invitations/`,
        {
          params: this.invitationSearch
            ? { search: this.invitationSearch }
            : {},
        },
      );
      this.invitations = data.results || data;
      this.invitationsNext = data.next || null;
    },
    async loadWorkspaces() {
      const { data } = await this.$client.get(
        `/organizations/${this.currentOrganizationId}/workspaces/`,
        {
          params: this.workspaceSearch ? { search: this.workspaceSearch } : {},
        },
      );
      this.organization.workspaces = data.results || data;
      this.workspacesNext = data.next || null;
    },
    async loadMoreMembers() {
      if (!this.membersNext || this.busy) return;
      const { data } = await this.$client.get(this.membersNext);
      this.organization.members.push(...(data.results || data));
      this.membersNext = data.next || null;
    },
    async loadMoreInvitations() {
      if (!this.invitationsNext || this.busy) return;
      const { data } = await this.$client.get(this.invitationsNext);
      this.invitations.push(...(data.results || data));
      this.invitationsNext = data.next || null;
    },
    async loadMoreWorkspaces() {
      if (!this.workspacesNext || this.busy) return;
      const { data } = await this.$client.get(this.workspacesNext);
      this.organization.workspaces.push(...(data.results || data));
      this.workspacesNext = data.next || null;
    },
    async invite() {
      await this.run(async () => {
        const response = await this.$client.post(
          `/organizations/${this.organization.id}/invitations/`,
          { email: this.email, role: this.role },
        );
        this.token = response.data.token;
        this.email = "";
      });
    },
    async updateSettings() {
      await this.run(async () => {
        const response = await this.$client.patch(
          `/organizations/${this.organization.id}/`,
          { name: this.organizationName },
        );
        this.organization = { ...this.organization, ...response.data };
      });
    },
    async addMember() {
      await this.run(async () => {
        await this.$client.post(
          `/organizations/${this.organization.id}/members/`,
          { user: this.userId, role: this.addRole },
        );
        this.userId = null;
      });
    },
    async revokeInvitation(invitation) {
      await this.run(() =>
        this.$client.delete(
          `/organizations/${this.organization.id}/invitations/${invitation.id}/`,
        ),
      );
    },
    async remove(member) {
      await this.run(() =>
        this.$client.delete(
          `/organizations/${this.organization.id}/members/${member.id}/`,
        ),
      );
    },
    async suspend(member, suspended) {
      await this.run(() =>
        this.$client.patch(
          `/organizations/${this.organization.id}/members/${member.id}/`,
          { suspended },
        ),
      );
    },
    async updateRole(member, role) {
      await this.run(() =>
        this.$client.patch(
          `/organizations/${this.organization.id}/members/${member.id}/`,
          { role },
        ),
      );
    },
    async bindWorkspace() {
      if (!this.workspacePreview) {
        await this.previewWorkspace();
        return;
      }
      if (String(this.workspacePreview.workspace) !== String(this.workspace)) {
        await this.previewWorkspace();
        return;
      }
      await this.run(async () => {
        await this.$client.post(
          `/organizations/${this.organization.id}/workspaces/bind/`,
          { workspace: this.workspace, confirm_outsiders: true },
        );
        this.workspace = null;
        this.workspacePreview = null;
      });
    },
    async previewWorkspace() {
      if (!this.workspace) return;
      this.error = false;
      try {
        const { data } = await this.$client.get(
          `/organizations/${this.organization.id}/workspaces/bind/?workspace=${this.workspace}`,
        );
        this.workspacePreview = data;
      } catch {
        this.error = true;
      }
    },
    async assignWorkspace(binding) {
      await this.run(() =>
        this.$client.post(
          `/organizations/${this.organization.id}/workspaces/${binding.id}/members/${this.assignmentMembers[binding.id]}/`,
          { permissions: this.assignmentPermissions[binding.id] || "MEMBER" },
        ),
      );
    },
    async unassignWorkspace(binding, assignment) {
      await this.run(() =>
        this.$client.delete(
          `/organizations/${this.organization.id}/workspaces/${binding.id}/members/${assignment.membership_id}/`,
        ),
      );
    },
    async unbindWorkspace(binding) {
      await this.run(() =>
        this.$client.delete(
          `/organizations/${this.organization.id}/workspaces/${binding.id}/`,
        ),
      );
    },
    async changeLifecycle(action) {
      await this.run(() =>
        this.$client.post(`/organizations/${this.organization.id}/lifecycle/`, {
          action,
        }),
      );
    },
    async transitionToPersonal() {
      await this.run(async () => {
        await this.$client.post(
          `/organizations/${this.organization.id}/transition-to-personal/`,
        );
        await this.$router.push("/billing");
      });
    },
  },
};
</script>

<style scoped>
.organization-page {
  max-inline-size: 960px;
  margin-inline: auto;
  padding: 32px;
  background: var(--jadawel-content-background, #fcfdfc);
}

.organization-page section {
  margin-block: 32px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 8px;
  padding: 20px;
  background: var(--jadawel-raised-background, #fbfdfb);
}

.organization-page form {
  display: grid;
  gap: 12px;
  max-inline-size: 480px;
  margin-block: 16px;
}

.organization-page .organization-search {
  display: flex;
  gap: 12px;
  align-items: end;
  flex-wrap: wrap;
  max-inline-size: 640px;
}

.organization-page .organization-search label {
  flex: 1 1 280px;
}

.organization-page label {
  display: grid;
  gap: 8px;
}

.organization-page input:not([type="checkbox"]),
.organization-page select,
.organization-page textarea {
  box-sizing: border-box;
  min-block-size: 36px;
  inline-size: 100%;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 6px;
  padding: 8px 10px;
  background: var(--jadawel-raised-background, #fbfdfb);
  color: inherit;
  font: inherit;
}

.organization-page input:focus,
.organization-page select:focus,
.organization-page textarea:focus {
  border-color: var(--jadawel-primary-500, #278053);
  outline: 2px solid
    color-mix(in srgb, var(--jadawel-primary-500, #278053) 28%, transparent);
  outline-offset: 1px;
}

.organization-page li {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-block: 12px;
  flex-wrap: wrap;
}

.workspace-preview {
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  padding: 16px;
  margin-block: 16px;
  background: var(--jadawel-header-background, #f0f7f3);
}

.workspace-assignments {
  flex-basis: 100%;
  margin-block: 0;
  padding-inline-start: 24px;
}
</style>
