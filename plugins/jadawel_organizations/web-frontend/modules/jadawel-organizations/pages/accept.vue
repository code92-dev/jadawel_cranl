<template>
  <main class="organization-invitation-page">
    <h1>{{ $t("organizations.accept") }}</h1>
    <form @submit.prevent="accept">
      <label>
        {{ $t("organizations.tokenInput") }}
        <input
          v-model="token"
          dir="ltr"
          minlength="20"
          required
          class="input"
        />
      </label>
      <Button :disabled="busy">
        {{ $t("organizations.accept") }}
      </Button>
    </form>
    <p v-if="accepted" role="status">
      {{ $t("organizations.invitationAccepted") }}
    </p>
    <p v-if="error" role="alert">{{ $t("organizations.error") }}</p>
  </main>
</template>

<script>
export default {
  name: "AcceptOrganizationInvitation",
  layout: "app",
  middleware: "authenticated",
  data() {
    return {
      token: this.$route.query.token || "",
      busy: false,
      accepted: false,
      error: false,
    };
  },
  methods: {
    async accept() {
      this.busy = true;
      this.error = false;
      try {
        await this.$client.post("/organizations/invitations/accept/", {
          token: this.token,
        });
        this.accepted = true;
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
.organization-invitation-page {
  max-inline-size: 560px;
  margin-inline: auto;
  padding: 32px;
}

.organization-invitation-page form {
  display: grid;
  gap: 12px;
  margin-block: 24px;
}

.organization-invitation-page label {
  display: grid;
  gap: 8px;
}
</style>
