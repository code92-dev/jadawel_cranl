<template>
  <main class="organizations-admin-page">
    <h1>{{ $t("organizations.adminTitle") }}</h1>
    <p>{{ $t("organizations.freeNote") }}</p>
    <form @submit.prevent="create">
      <label>
        {{ $t("organizations.name") }}
        <input v-model="name" required class="input" />
      </label>
      <label>
        {{ $t("organizations.owner") }}
        <input v-model.number="owner" type="number" min="1" class="input" />
      </label>
      <label>
        {{ $t("organizations.ownerEmail") }}
        <input v-model.trim="ownerEmail" type="email" class="input" />
      </label>
      <label>
        {{ $t("organizations.plan") }}
        <select v-model="grant.plan" class="input">
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
          class="input"
        />
      </label>
      <label v-if="grant.plan">
        {{ $t("organizations.expiresAt") }}
        <input v-model="grant.expires_at" type="datetime-local" class="input" />
      </label>
      <label v-if="grant.plan">
        {{ $t("organizations.reason") }}
        <textarea
          v-model="grant.reason"
          required
          maxlength="500"
          class="input"
        />
      </label>
      <Button :disabled="busy">
        {{ $t("organizations.create") }}
      </Button>
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
          <input
            v-model.trim="reassignEmails[organization.id]"
            type="email"
            :placeholder="$t('organizations.ownerEmail')"
            dir="ltr"
            class="input"
          />
          <Button type="secondary" @click="resendOwner(organization)">
            {{ $t("organizations.resendOwner") }}
          </Button>
          <Button
            type="secondary"
            :disabled="!reassignEmails[organization.id]"
            @click="resendOwner(organization, reassignEmails[organization.id])"
          >
            {{ $t("organizations.reassignOwner") }}
          </Button>
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
      reassignEmails: {},
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
        const response = await this.$client.post(
          "/organizations/admin/create/",
          payload,
        );
        this.ownerSetupToken = response.data.owner_setup_token || "";
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
    async resendOwner(organization, email = "") {
      this.error = false;
      try {
        const response = await this.$client.post(
          `/organizations/admin/${organization.id}/owner-setup/`,
          email ? { email } : {},
        );
        this.ownerSetupToken = response.data.owner_setup_token;
        if (email) this.reassignEmails[organization.id] = "";
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
  background: var(--jadawel-content-background, #fcfdfc);
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

.organizations-admin-page input:not([type="checkbox"]),
.organizations-admin-page select,
.organizations-admin-page textarea {
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

.organizations-admin-page input:focus,
.organizations-admin-page select:focus,
.organizations-admin-page textarea:focus {
  border-color: var(--jadawel-primary-500, #278053);
  outline: 2px solid
    color-mix(in srgb, var(--jadawel-primary-500, #278053) 28%, transparent);
  outline-offset: 1px;
}
</style>
