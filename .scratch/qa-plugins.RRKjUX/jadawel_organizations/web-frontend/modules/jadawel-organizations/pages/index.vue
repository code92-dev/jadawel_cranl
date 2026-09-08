<template>
  <main class="organizations-page">
    <h1>{{ $t("organizations.title") }}</h1>
    <form @submit.prevent="startTeam">
      <label>
        {{ $t("organizations.name") }}
        <input v-model="teamName" required class="input" />
      </label>
      <Button :disabled="busy">
        {{ $t("organizations.create") }}
      </Button>
    </form>
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
      <Button type="secondary" :disabled="loading">
        {{ $t("organizations.search") }}
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
          — {{ organization.members_count }} {{ $t("organizations.members") }}
        </span>
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
  </main>
</template>

<script setup>
definePageMeta({
  layout: "app",
  middleware: "authenticated",
});
</script>

<script>
import { uuid } from "@jadawel/modules/core/utils/string";

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
  max-inline-size: 840px;
  margin-inline: auto;
  padding: 32px;
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
