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

    <section>
      <h2>{{ $t("organizations.members") }}</h2>
      <form @submit.prevent="invite">
        <label>
          {{ $t("organizations.email") }}
          <input
            v-model="email"
            type="email"
            dir="ltr"
            required
            :placeholder="$t('organizations.email')"
          />
        </label>
        <label>
          {{ $t("organizations.role") }}
          <select v-model="role">
            <option value="member">{{ $t("organizations.member") }}</option>
            <option value="admin">{{ $t("organizations.admin") }}</option>
          </select>
        </label>
        <button type="submit" :disabled="busy">
          {{ $t("organizations.sendInvite") }}
        </button>
      </form>
      <form @submit.prevent="addMember">
        <label>
          {{ $t("organizations.userId") }}
          <input v-model.number="userId" type="number" min="1" required />
        </label>
        <label>
          {{ $t("organizations.role") }}
          <select v-model="addRole">
            <option value="member">{{ $t("organizations.member") }}</option>
            <option value="admin">{{ $t("organizations.admin") }}</option>
          </select>
        </label>
        <button type="submit" :disabled="busy">
          {{ $t("organizations.addMember") }}
        </button>
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
            @change="updateRole(member, $event.target.value)"
          >
            <option value="member">{{ $t("organizations.member") }}</option>
            <option value="admin">{{ $t("organizations.admin") }}</option>
            <option value="owner">{{ $t("organizations.ownerRole") }}</option>
          </select>
          <button
            v-if="member.role !== 'owner'"
            type="button"
            @click="suspend(member, !member.suspended)"
          >
            {{
              member.suspended
                ? $t("organizations.reactivate")
                : $t("organizations.suspend")
            }}
          </button>
          <button
            v-if="member.role !== 'owner'"
            type="button"
            @click="remove(member)"
          >
            {{ $t("organizations.remove") }}
          </button>
        </li>
      </ul>
    </section>

    <section>
      <h2>{{ $t("organizations.invitations") }}</h2>
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
          <button
            v-if="!invitation.accepted_at && !invitation.revoked_at"
            type="button"
            @click="revokeInvitation(invitation)"
          >
            {{ $t("organizations.revokeInvitation") }}
          </button>
        </li>
      </ul>
    </section>

    <section>
      <h2>{{ $t("organizations.workspaces") }}</h2>
      <form @submit.prevent="bindWorkspace">
        <label>
          {{ $t("organizations.workspaceId") }}
          <input v-model.number="workspace" type="number" min="1" required />
        </label>
        <button type="submit" :disabled="busy">
          {{ $t("organizations.bindWorkspace") }}
        </button>
      </form>
      <ul>
        <li v-for="binding in organization.workspaces" :key="binding.id">
          <bdi>{{ binding.workspace.name }}</bdi>
          <span> — {{ binding.assigned_members }}</span>
          <form @submit.prevent="assignWorkspace(binding)">
            <label>
              {{ $t("organizations.assignmentMember") }}
              <select v-model.number="assignmentMembers[binding.id]" required>
                <option
                  v-for="member in activeMembers"
                  :key="member.id"
                  :value="member.id"
                >
                  {{ member.email }}
                </option>
              </select>
            </label>
            <button type="submit" :disabled="busy">
              {{ $t("organizations.assign") }}
            </button>
          </form>
          <button type="button" @click="unbindWorkspace(binding)">
            {{ $t("organizations.unbindWorkspace") }}
          </button>
        </li>
      </ul>
    </section>

    <section>
      <h2>{{ $t("organizations.lifecycle") }}</h2>
      <button type="button" @click="changeLifecycle('suspend')">
        {{ $t("organizations.suspend") }}
      </button>
      <button type="button" @click="changeLifecycle('reactivate')">
        {{ $t("organizations.reactivate") }}
      </button>
      <button type="button" @click="changeLifecycle('archive')">
        {{ $t("organizations.archive") }}
      </button>
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
      invitations: [],
      email: "",
      role: "member",
      userId: null,
      addRole: "member",
      token: "",
      workspace: null,
      assignmentMembers: {},
      busy: false,
      error: false,
    };
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      try {
        const [organization, invitations] = await Promise.all([
          this.$client.get(`/organizations/${this.currentOrganizationId}/`),
          this.$client.get(
            `/organizations/${this.currentOrganizationId}/invitations/`,
          ),
        ]);
        this.organization = organization.data;
        this.invitations = invitations.data;
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
      await this.run(async () => {
        await this.$client.post(
          `/organizations/${this.organization.id}/workspaces/bind/`,
          { workspace: this.workspace },
        );
        this.workspace = null;
      });
    },
    async assignWorkspace(binding) {
      await this.run(() =>
        this.$client.post(
          `/organizations/${this.organization.id}/workspaces/${binding.id}/members/${this.assignmentMembers[binding.id]}/`,
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
};
</script>

<style scoped>
.organization-page {
  max-inline-size: 960px;
  margin-inline: auto;
  padding: 32px;
}

.organization-page section {
  margin-block: 32px;
}

.organization-page form {
  display: grid;
  gap: 12px;
  max-inline-size: 480px;
  margin-block: 16px;
}

.organization-page label {
  display: grid;
  gap: 8px;
}

.organization-page li {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-block: 12px;
  flex-wrap: wrap;
}
</style>
