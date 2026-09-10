<template>
  <main class="organizations-page">
    <header class="organizations-page__header">
      <div>
        <h1>{{ $t("organizations.title") }}</h1>
        <p class="organizations-page__description">
          {{ $t("organizations.description") }}
        </p>
      </div>
    </header>
    <section class="organizations-page__card">
      <h2>{{ $t("organizations.create") }}</h2>
      <form @submit.prevent="startTeam">
        <label>
          {{ $t("organizations.name") }}
          <input v-model="teamName" required class="input" />
        </label>
        <Button button-type="submit" :disabled="busy">
          {{ $t("organizations.create") }}
        </Button>
      </form>
    </section>
    <section class="organizations-page__card">
      <h2>{{ $t("organizations.search") }}</h2>
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
      <p v-if="loading" role="status">{{ $t("organizations.loading") }}</p>
      <p v-else-if="!organizations.length">{{ $t("organizations.empty") }}</p>
      <ul v-else class="organizations-page__list">
        <li v-for="organization in organizations" :key="organization.id">
          <div class="organizations-page__identity">
            <NuxtLink :to="`/organizations/${organization.id}`">
              {{ organization.name }}
            </NuxtLink>
            <bdi>
              {{
                organization.owner?.email ||
                organization.pending_owner_email ||
                $t("organizations.ownerNotAssigned")
              }}
            </bdi>
          </div>
          <div class="organizations-page__details">
            <span>
              {{ $t("organizations.status") }}:
              {{ $t(`organizations.statuses.${organization.status}`) }}
            </span>
            <span>
              {{ $t("organizations.accessSource") }}:
              {{
                $t(
                  `organizations.sources.${organization.effective_entitlement?.source}`,
                )
              }}
            </span>
            <span>
              {{ $t("organizations.seats") }}:
              {{ organization.effective_entitlement?.seat_limit ?? 0 }}
            </span>
            <span>
              {{ organization.members_count ?? 0 }}
              {{ $t("organizations.members") }}
            </span>
          </div>
        </li>
      </ul>
      <Button
        v-if="organizationsNext"
        type="secondary"
        :disabled="loading"
        @click="loadMore"
      >
        {{ $t("organizations.more") }}
      </Button>
      <p v-if="error" role="alert">{{ $t("organizations.error") }}</p>
    </section>
  </main>
</template>

<script setup>
definePageMeta({
  layout: "app",
  middleware: "authenticated",
});
</script>

<script>
/* eslint-disable import/first -- Nuxt page metadata uses a separate setup block. */
import { uuid } from "@jadawel/modules/core/utils/string";
/* eslint-enable import/first */

export default {
  name: "OrganizationsIndex",
  data() {
    return {
      organizations: [],
      organizationsNext: null,
      teamName: "",
      creationKey: null,
      search: "",
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
      this.error = false;
      this.loading = true;
      try {
        const response = await this.$client.get("/organizations/", {
          params: this.search ? { search: this.search } : {},
        });
        const data = response.data;
        this.organizations = data.results || data;
        this.organizationsNext = data.next || null;
      } catch {
        this.error = true;
      } finally {
        this.loading = false;
      }
    },
    async loadMore() {
      if (!this.organizationsNext || this.loading) return;
      this.loading = true;
      this.error = false;
      try {
        const response = await this.$client.get(this.organizationsNext);
        const data = response.data;
        this.organizations.push(...(data.results || data));
        this.organizationsNext = data.next || null;
      } catch {
        this.error = true;
      } finally {
        this.loading = false;
      }
    },
    async startTeam() {
      this.busy = true;
      this.error = false;
      this.creationKey = this.creationKey || uuid();
      try {
        const response = await this.$client.post(
          "/organizations/start-team/",
          {
            name: this.teamName,
            creation_key: this.creationKey,
          },
          {
            headers: { "Idempotency-Key": this.creationKey },
          },
        );
        this.creationKey = null;
        this.$router.push({
          path: "/billing",
          query: { account: response.data.billing_account },
        });
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
  },
};
</script>

<style scoped>
.organizations-page {
  max-inline-size: 1040px;
  margin-inline: auto;
  padding: 32px;
}
.organizations-page__header {
  margin-block-end: 24px;
}
.organizations-page__description {
  margin-block: 6px 0;
  color: var(--jadawel-text-secondary, #66756d);
}
.organizations-page__eyebrow {
  margin: 0;
  color: var(--jadawel-primary-500, #278053);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.organizations-page__card {
  margin-block: 20px;
  padding: 20px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 12px;
  background: var(--jadawel-raised-background, #fbfdfb);
  box-shadow: 0 8px 24px rgb(20 65 42 / 6%);
}
.organizations-page__list {
  display: grid;
  gap: 10px;
  padding: 0;
  list-style: none;
}
.organizations-page__list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 14px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 8px;
}
.organizations-page__identity {
  display: grid;
  gap: 4px;
  min-inline-size: 220px;
}
.organizations-page__identity bdi {
  color: var(--jadawel-text-secondary, #66756d);
  font-size: 13px;
}
.organizations-page__details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  align-items: center;
  color: var(--jadawel-text-secondary, #66756d);
  font-size: 13px;
  text-align: start;
}
.organizations-page__list a {
  font-weight: 700;
  color: var(--jadawel-primary-500, #278053);
}

@media (max-width: 640px) {
  .organizations-page {
    padding: 20px 16px;
  }
  .organizations-page__card {
    padding: 16px;
  }
}

.organizations-page form {
  display: grid;
  gap: 12px;
  max-inline-size: 480px;
  margin-block: 24px;
}

.organizations-page .organization-search {
  display: flex;
  gap: 12px;
  align-items: end;
  flex-wrap: wrap;
}

.organizations-page .organization-search label {
  flex: 1 1 280px;
}

.organizations-page label {
  display: grid;
  gap: 8px;
}
</style>
