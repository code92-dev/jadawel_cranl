<template>
  <main class="organizations-admin-page">
    <h1>{{ $t("organizations.adminTitle") }}</h1>
    <p>{{ $t("organizations.freeNote") }}</p>
    <form @submit.prevent="create">
      <label>
        {{ $t("organizations.name") }}
        <input v-model="name" required />
      </label>
      <label>
        {{ $t("organizations.owner") }}
        <input v-model.number="owner" type="number" min="1" />
      </label>
      <label>
        {{ $t("organizations.ownerEmail") }}
        <input v-model.trim="ownerEmail" type="email" />
      </label>
      <label>
        {{ $t("organizations.plan") }}
        <select v-model="grant.plan">
          <option value="">{{ $t("organizations.noGrant") }}</option>
          <option v-for="plan in plans" :key="plan.id" :value="plan.id">
            {{ plan.name }}
          </option>
        </select>
      </label>
      <label v-if="grant.plan">
        {{ $t("organizations.seatLimit") }}
        <input
          v-model.number="grant.seat_limit"
          type="number"
          min="1"
          required
        />
      </label>
      <label v-if="grant.plan">
        {{ $t("organizations.expiresAt") }}
        <input v-model="grant.expires_at" type="datetime-local" />
      </label>
      <label v-if="grant.plan">
        {{ $t("organizations.reason") }}
        <textarea v-model="grant.reason" required maxlength="500" />
      </label>
      <button type="submit" :disabled="busy">
        {{ $t("organizations.create") }}
      </button>
    </form>
    <p v-if="loading" role="status">{{ $t("organizations.loading") }}</p>
    <p v-else-if="!organizations.length">{{ $t("organizations.empty") }}</p>
    <ul v-else>
      <li v-for="organization in organizations" :key="organization.id">
        <NuxtLink :to="`/organizations/${organization.id}`">
          {{ organization.name }}
        </NuxtLink>
        <span>
          — {{ $t(`organizations.statuses.${organization.status}`) }} ·
          {{ $t("organizations.accessSource") }}:
          {{ $t(`organizations.sources.${organization.effective_source}`) }}
          · {{ $t("organizations.seats") }}:
          {{ organization.effective_seat_limit }}
        </span>
        <span v-if="organization.pending_owner_email">
          — {{ $t("organizations.pendingOwner") }}:
          <bdi>{{ organization.pending_owner_email }}</bdi>
          <button type="button" @click="resendOwner(organization)">
            {{ $t("organizations.resendOwner") }}
          </button>
        </span>
      </li>
    </ul>
    <p v-if="ownerSetupToken" role="status">
      {{ $t("organizations.ownerSetupToken") }}:
      <code dir="ltr">{{ ownerSetupToken }}</code>
    </p>
    <p v-if="error" role="alert">{{ $t("organizations.error") }}</p>
  </main>
</template>

<script>
export default {
  name: "OrganizationsAdmin",
  layout: "app",
  middleware: "staff",
  data() {
    return {
      name: "",
      owner: null,
      ownerEmail: "",
      ownerSetupToken: "",
      plans: [],
      grant: { plan: "", seat_limit: 1, expires_at: "", reason: "" },
      organizations: [],
      loading: true,
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
        const [organizations, plans] = await Promise.all([
          this.$client.get("/organizations/admin/"),
          this.$client.get("/billing/admin/plans/"),
        ]);
        this.organizations = organizations.data.results || organizations.data;
        this.plans = (plans.data.results || plans.data).filter(
          (plan) => plan.kind === "TEAM",
        );
      } catch {
        this.error = true;
      } finally {
        this.loading = false;
      }
    },
    async create() {
      this.busy = true;
      this.error = false;
      try {
        const payload = {
          name: this.name,
        };
        if (this.owner) payload.owner = this.owner;
        if (this.ownerEmail) payload.owner_email = this.ownerEmail;
        if (this.grant.plan) {
          payload.plan = Number(this.grant.plan);
          payload.seat_limit = this.grant.seat_limit;
          payload.reason = this.grant.reason;
          if (this.grant.expires_at) payload.expires_at = this.grant.expires_at;
        }
        await this.$client.post("/organizations/admin/create/", payload);
        this.name = "";
        this.owner = null;
        this.ownerEmail = "";
        this.grant = { plan: "", seat_limit: 1, expires_at: "", reason: "" };
        await this.load();
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async resendOwner(organization) {
      this.error = false;
      try {
        const response = await this.$client.post(
          `/organizations/admin/${organization.id}/owner-setup/`,
          {},
        );
        this.ownerSetupToken = response.data.owner_setup_token;
      } catch {
        this.error = true;
      }
    },
  },
};
</script>

<style scoped>
.organizations-admin-page {
  max-inline-size: 840px;
  margin-inline: auto;
  padding: 32px;
}

.organizations-admin-page form {
  display: grid;
  gap: 12px;
  max-inline-size: 480px;
  margin-block: 24px;
}

.organizations-admin-page label {
  display: grid;
  gap: 8px;
}
</style>
