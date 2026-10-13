<template>
  <main class="organizations-admin-page">
    <header class="organizations-admin-page__header">
      <h1>{{ $t("organizations.adminTitle") }}</h1>
      <p>{{ $t("organizations.freeNote") }}</p>
    </header>
    <form class="organization-search" @submit.prevent="load">
      <label>
        {{ $t("organizations.search") }}
        <input
          v-model.trim="search"
          type="search"
          class="input"
          :placeholder="$t('organizations.searchOrganizations')"
        />
      </label>
      <Button type="secondary" button-type="submit" :disabled="loading">
        {{ $t("organizations.search") }}
      </Button>
    </form>
    <form class="organization-setup" @submit.prevent="create">
      <h2>{{ $t("organizations.setupTitle") }}</h2>
      <p>{{ $t("organizations.setupNote") }}</p>
      <label>
        {{ $t("organizations.name") }}
        <input v-model="name" required class="input" />
      </label>
      <label>
        {{ $t("organizations.ownerAccountEmail") }}
        <input
          v-model.trim="ownerEmail"
          type="email"
          required
          dir="ltr"
          class="input"
        />
      </label>
      <fieldset class="organization-setup__members">
        <legend>{{ $t("organizations.members") }}</legend>
        <div
          v-for="(member, index) in members"
          :key="member.key"
          class="organization-setup__member"
        >
          <input
            v-model.trim="member.email"
            type="email"
            required
            dir="ltr"
            class="input"
            :placeholder="$t('organizations.email')"
            :aria-label="$t('organizations.email')"
          />
          <select
            v-model="member.role"
            class="input"
            :aria-label="$t('organizations.role')"
          >
            <option value="member">{{ $t("organizations.member") }}</option>
            <option value="admin">{{ $t("organizations.admin") }}</option>
          </select>
          <Button type="secondary" @click="members.splice(index, 1)">
            {{ $t("organizations.remove") }}
          </Button>
        </div>
        <Button type="secondary" @click="addMemberRow">
          {{ $t("organizations.addMemberRow") }}
        </Button>
      </fieldset>
      <label>
        {{ $t("organizations.plan") }}
        <select v-model="grant.plan" required class="input">
          <option
            v-for="plan in plans"
            :key="plan.id"
            :value="plan.id"
            dir="auto"
          >
            {{ plan.name }}
          </option>
        </select>
      </label>
      <label>
        {{ $t("organizations.seatLimit") }}
        <input
          v-model.number="grant.seat_limit"
          type="number"
          :min="minimumSeats"
          :placeholder="String(minimumSeats)"
          class="input"
        />
        <small>
          {{ $t("organizations.seatLimitHint", { count: minimumSeats }) }}
        </small>
      </label>
      <label>
        {{ $t("organizations.expiresAt") }}
        <input v-model="grant.expires_at" type="datetime-local" class="input" />
      </label>
      <label>
        {{ $t("organizations.reasonOptional") }}
        <textarea v-model="grant.reason" maxlength="500" class="input" />
      </label>
      <label class="organization-setup__checkbox">
        <input v-model="createWorkspace" type="checkbox" />
        {{ $t("organizations.createWorkspace") }}
      </label>
      <Button button-type="submit" :disabled="busy || !plans.length">
        {{ $t("organizations.create") }}
      </Button>
    </form>
    <section
      v-if="setupResult"
      role="status"
      class="organization-setup__result"
    >
      <p>{{ $t("organizations.setupDone", { name: setupResult.name }) }}</p>
      <template v-if="setupResult.credentials.length">
        <p>
          <strong>{{ $t("organizations.credentialsWarning") }}</strong>
        </p>
        <table>
          <thead>
            <tr>
              <th>{{ $t("organizations.email") }}</th>
              <th>{{ $t("organizations.temporaryPassword") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="credential in setupResult.credentials"
              :key="credential.email"
            >
              <td>
                <bdi>{{ credential.email }}</bdi>
              </td>
              <td>
                <code dir="ltr">{{ credential.password }}</code>
              </td>
            </tr>
          </tbody>
        </table>
        <Button type="secondary" @click="copyCredentials">
          {{
            copied
              ? $t("organizations.copied")
              : $t("organizations.copyCredentials")
          }}
        </Button>
      </template>
    </section>
    <p v-if="loading" role="status">{{ $t("organizations.loading") }}</p>
    <p v-else-if="!organizations.length">{{ $t("organizations.empty") }}</p>
    <ul v-else>
      <li v-for="organization in organizations" :key="organization.id">
        <div class="organizations-admin-page__identity">
          <NuxtLink :to="`/organizations/${organization.id}`">
            {{ organization.name }}
          </NuxtLink>
          <bdi>{{
            organization.owner_email || $t("organizations.ownerNotAssigned")
          }}</bdi>
        </div>
        <div class="organizations-admin-page__details">
          <span>
            {{ $t("organizations.status") }}:
            {{ $t(`organizations.statuses.${organization.status}`) }}
          </span>
          <span>
            {{ $t("organizations.accessSource") }}:
            {{ $t(`organizations.sources.${organization.effective_source}`) }}
          </span>
          <span>
            {{ $t("organizations.seats") }}:
            {{ organization.effective_seat_limit }}
          </span>
          <span>
            {{ organization.members_count }} {{ $t("organizations.members") }}
          </span>
          <span v-if="organization.subscription_status">
            {{ $t("organizations.paymentStatus") }}:
            {{
              $t(
                `organizations.subscriptionStatuses.${organization.subscription_status}`,
              )
            }}
          </span>
        </div>
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
    <Button
      v-if="organizationsNext"
      type="secondary"
      :disabled="loading"
      @click="loadMoreOrganizations"
    >
      {{ $t("organizations.more") }}
    </Button>
    <p v-if="ownerSetupToken" role="status">
      {{ $t("organizations.ownerSetupToken") }}:
      <code dir="ltr">{{ ownerSetupToken }}</code>
    </p>
    <p v-if="error" role="alert">
      {{ $t("organizations.error") }}
      <span v-if="errorDetail" dir="auto">— {{ errorDetail }}</span>
    </p>
  </main>
</template>

<script setup>
definePageMeta({
  layout: "app",
  middleware: "staff",
});
</script>

<script>
/* eslint-disable import/first -- Nuxt page metadata uses a separate setup block. */
import { uuid } from "@jadawel/modules/core/utils/string";
import { describeApiError } from "../utils/apiError";
/* eslint-enable import/first */

export default {
  name: "OrganizationsAdmin",
  data() {
    return {
      name: "",
      ownerEmail: "",
      members: [],
      createWorkspace: true,
      setupResult: null,
      copied: false,
      ownerSetupToken: "",
      creationKey: null,
      plans: [],
      grant: { plan: "", seat_limit: null, expires_at: "", reason: "" },
      organizations: [],
      organizationsNext: null,
      search: "",
      reassignEmails: {},
      loading: true,
      busy: false,
      error: false,
      errorDetail: "",
    };
  },
  computed: {
    // The server raises the seat limit to fit the owner and every member.
    minimumSeats() {
      return 1 + this.members.length;
    },
  },
  async mounted() {
    await this.load();
  },
  methods: {
    addMemberRow() {
      this.members.push({ key: uuid(), email: "", role: "member" });
    },
    async copyCredentials() {
      const text = this.setupResult.credentials
        .map((credential) => `${credential.email}\t${credential.password}`)
        .join("\n");
      await navigator.clipboard.writeText(text);
      this.copied = true;
    },
    // The admin endpoints answer with DRF field errors ("owner":
    // "choose_id_or_email"). Swallowing them left a 400 in the console and no
    // way to tell which field the server rejected.
    fail(error) {
      this.error = true;
      this.errorDetail = describeApiError(error);
    },
    async load() {
      this.loading = true;
      this.error = false;
      this.errorDetail = "";
      try {
        const [organizations, plans] = await Promise.all([
          this.$client.get("/organizations/admin/", {
            params: this.search ? { search: this.search } : {},
          }),
          this.$client.get("/billing/admin/plans/"),
        ]);
        this.organizations = organizations.data.results || organizations.data;
        this.organizationsNext = organizations.data.next || null;
        this.plans = (plans.data.results || plans.data).filter(
          (plan) => plan.kind === "TEAM",
        );
        if (!this.grant.plan && this.plans.length) {
          this.grant.plan = this.plans[0].id;
        }
      } catch (error) {
        this.fail(error);
      } finally {
        this.loading = false;
      }
    },
    async create() {
      this.busy = true;
      this.error = false;
      this.errorDetail = "";
      this.setupResult = null;
      this.copied = false;
      this.creationKey = this.creationKey || uuid();
      try {
        const payload = {
          name: this.name,
          owner_email: this.ownerEmail,
          members: this.members.map(({ email, role }) => ({ email, role })),
          plan: Number(this.grant.plan),
          create_workspace: this.createWorkspace,
        };
        if (this.grant.seat_limit) payload.seat_limit = this.grant.seat_limit;
        if (this.grant.reason) payload.reason = this.grant.reason;
        if (this.grant.expires_at) payload.expires_at = this.grant.expires_at;
        const response = await this.$client.post(
          "/organizations/admin/setup/",
          payload,
          { headers: { "Idempotency-Key": this.creationKey } },
        );
        this.creationKey = null;
        this.setupResult = {
          name: response.data.name,
          credentials: response.data.credentials || [],
        };
        this.name = "";
        this.ownerEmail = "";
        this.members = [];
        this.createWorkspace = true;
        this.grant = {
          plan: this.grant.plan,
          seat_limit: null,
          expires_at: "",
          reason: "",
        };
        await this.load();
      } catch (error) {
        this.fail(error);
      } finally {
        this.busy = false;
      }
    },
    async resendOwner(organization, email = "") {
      this.error = false;
      this.errorDetail = "";
      try {
        const response = await this.$client.post(
          `/organizations/admin/${organization.id}/owner-setup/`,
          email ? { email } : {},
        );
        this.ownerSetupToken = response.data.owner_setup_token;
        if (email) this.reassignEmails[organization.id] = "";
      } catch (error) {
        this.fail(error);
      }
    },
    async loadMoreOrganizations() {
      if (!this.organizationsNext || this.loading) return;
      this.loading = true;
      this.error = false;
      this.errorDetail = "";
      try {
        const response = await this.$client.get(this.organizationsNext);
        const data = response.data;
        this.organizations.push(...(data.results || data));
        this.organizationsNext = data.next || null;
      } catch (error) {
        this.fail(error);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.organizations-admin-page {
  max-inline-size: 1040px;
  margin-inline: auto;
  padding: 32px;
  background: var(--jadawel-content-background, #fcfdfc);
}
.organizations-admin-page__header {
  margin-block-end: 24px;
}
.organizations-admin-page__header p {
  margin-block: 6px 0;
  color: var(--jadawel-text-secondary, #66756d);
}
.organizations-admin-page article {
  margin-block: 20px;
  padding: 20px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 12px;
  background: var(--jadawel-raised-background, #fbfdfb);
  box-shadow: 0 8px 24px rgb(20 65 42 / 6%);
}
.organizations-admin-page ul {
  padding: 0;
  list-style: none;
}
.organizations-admin-page li {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  padding: 12px;
  border-block-end: 1px solid var(--jadawel-border-color, #e0f1e7);
}
.organizations-admin-page__identity {
  display: grid;
  gap: 4px;
  min-inline-size: 220px;
}
.organizations-admin-page__identity bdi {
  color: var(--jadawel-text-secondary, #66756d);
  font-size: 13px;
}
.organizations-admin-page__details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  align-items: center;
  color: var(--jadawel-text-secondary, #66756d);
  font-size: 13px;
}

.organizations-admin-page form {
  display: grid;
  gap: 12px;
  max-inline-size: 480px;
  margin-block: 24px;
}

.organization-setup__members {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 12px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 6px;
}

.organization-setup__members > :last-child {
  justify-self: start;
}

.organization-setup__member {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px auto;
  gap: 8px;
  align-items: center;
}

.organizations-admin-page .organization-setup__checkbox {
  display: flex;
  gap: 8px;
  align-items: center;
}

.organization-setup small {
  color: var(--jadawel-text-secondary, #66756d);
}

.organization-setup__result {
  max-inline-size: 640px;
  padding: 16px;
  border: 1px solid var(--jadawel-primary-500, #278053);
  border-radius: 12px;
}

.organization-setup__result table {
  inline-size: 100%;
  margin-block: 8px 12px;
  border-collapse: collapse;
}

.organization-setup__result th,
.organization-setup__result td {
  padding: 6px 8px;
  border-block-end: 1px solid var(--jadawel-border-color, #e0f1e7);
  text-align: start;
}

.organizations-admin-page .organization-search {
  display: flex;
  gap: 12px;
  align-items: end;
  flex-wrap: wrap;
  max-inline-size: 640px;
}

.organizations-admin-page .organization-search label {
  flex: 1 1 280px;
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

@media (max-width: 640px) {
  .organizations-admin-page {
    padding: 20px 16px;
  }
  .organizations-admin-page section,
  .organizations-admin-page article {
    padding: 16px;
  }
  .organization-setup__member {
    grid-template-columns: minmax(0, 1fr) auto;
  }
  .organization-setup__member input {
    grid-column: 1 / -1;
  }
}
</style>
