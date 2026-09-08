<template>
  <section class="billing-grant">
    <h2>
      {{ $t("billing.manualAccess") }} — <bdi>{{ account.owner_email }}</bdi>
    </h2>
    <p v-if="error" role="alert">{{ $t("billing.error") }}</p>
    <p data-testid="effective-access" role="status">
      {{ $t("billing.source." + access.effective.source) }} ·
      {{ $t("billing.seats") }}: {{ access.effective.seat_limit }}
    </p>
    <p data-testid="renewal-status" role="status">
      {{
        access.subscription
          ? $t("billing.renewal", {
              date: new Date(access.subscription.period_end).toLocaleDateString(
                $i18n.locale,
              ),
            })
          : $t("billing.noRenewal")
      }}
    </p>
    <p>{{ $t("billing.grantNote") }}</p>
    <form @submit.prevent="review">
      <label
        >{{ $t("billing.plans") }}
        <select v-model.number="form.plan" name="plan" required class="input">
          <option :value="null" disabled>{{ $t("billing.choosePlan") }}</option>
          <option v-for="plan in eligiblePlans" :key="plan.id" :value="plan.id">
            {{ plan.name }}
          </option>
        </select>
      </label>
      <label
        >{{ $t("billing.seats")
        }}<input
          v-model.number="form.seat_limit"
          name="seats"
          type="number"
          min="1"
          :max="account.kind === 'INDIVIDUAL' ? 1 : 100000"
          required
          class="input"
      /></label>
      <label
        >{{ $t("billing.expires")
        }}<input v-model="expires" type="datetime-local" class="input"
      /></label>
      <label
        >{{ $t("billing.reason")
        }}<textarea
          v-model="form.reason"
          name="reason"
          required
          maxlength="500"
          class="input"
        />
      </label>
      <Button :disabled="busy" button-type="submit">{{
        $t("billing.reviewGrant")
      }}</Button>
    </form>
    <div v-if="preview" role="region" :aria-label="$t('billing.reviewGrant')">
      <p>
        {{ $t("billing.plan") }}:
        <bdi>{{ planName(preview.plan) }}</bdi>
      </p>
      <p>
        {{ $t("billing.starts") }}:
        <time>{{ formatDate(preview.starts_at) }}</time>
      </p>
      <p>
        {{ $t("billing.seats") }}: {{ access.effective.seat_limit }} →
        {{ preview.seat_limit }}
      </p>
      <p>
        {{ $t("billing.expires") }}:
        {{ preview.expires_at || $t("billing.noExpiry") }}
      </p>
      <p>
        <bdi>{{ preview.reason }}</bdi>
      </p>
      <p>
        {{ $t("billing.effectiveAfter") }}:
        {{
          $t("billing.source." + (preview.effective_after?.source || "manual"))
        }}
      </p>
      <p v-if="preview.subscription">
        {{ $t("billing.renewal") }}:
        {{ formatDate(preview.subscription.period_end) }}
      </p>
      <Button
        ref="confirm"
        data-testid="confirm-grant"
        :disabled="busy"
        @click="save"
        >{{ $t("billing.confirm") }}</Button
      >
      <Button type="secondary" @click="preview = null">{{
        $t("billing.cancel")
      }}</Button>
    </div>
    <div class="billing-grant__actions">
      <Button
        v-if="access.grant && !access.grant.revoked_at"
        type="secondary"
        :disabled="busy || !form.reason.trim()"
        @click="pendingAction = 'revoke'"
        >{{ $t("billing.revoke") }}</Button
      >
      <Button
        type="secondary"
        :disabled="busy || !form.reason.trim()"
        @click="
          pendingAction =
            access.effective.source === 'suspended' ? 'resume' : 'suspend'
        "
        >{{
          $t(
            access.effective.source === "suspended"
              ? "billing.resume"
              : "billing.suspend",
          )
        }}</Button
      >
    </div>
    <div v-if="pendingAction" role="region" :aria-label="$t('billing.confirm')">
      <p>{{ $t("billing.actionWarning") }}</p>
      <p>
        {{ $t("billing." + pendingAction) }} — <bdi>{{ form.reason }}</bdi>
      </p>
      <Button :disabled="busy" @click="performAction">{{
        $t("billing.confirm")
      }}</Button>
      <Button type="secondary" @click="pendingAction = null">{{
        $t("billing.cancel")
      }}</Button>
    </div>
    <h3>{{ $t("billing.audit") }}</h3>
    <ul>
      <li v-for="event in events" :key="event.id">
        <time>{{
          new Date(event.created_at).toLocaleString($i18n.locale)
        }}</time>
        · {{ $t("billing.auditAction." + event.action.replaceAll(".", "_")) }}
      </li>
    </ul>
  </section>
</template>

<script>
export default {
  name: "BillingGrantPanel",
  props: {
    account: { type: Object, required: true },
    plans: { type: Array, required: true },
  },
  data() {
    return {
      access: {
        grant: null,
        effective: { source: "restricted", seat_limit: 0 },
      },
      form: { plan: null, seat_limit: 1, reason: "" },
      expires: "",
      preview: null,
      pendingAction: null,
      busy: false,
      error: false,
      events: [],
    };
  },
  computed: {
    url() {
      return "/billing/admin/accounts/" + this.account.id + "/";
    },
    eligiblePlans() {
      return this.plans.filter((plan) => plan.kind === this.account.kind);
    },
  },
  async mounted() {
    await this.load();
  },
  methods: {
    planName(planId) {
      return this.plans.find((plan) => plan.id === planId)?.name || planId;
    },
    formatDate(value) {
      return value
        ? new Date(value).toLocaleString(this.$i18n.locale)
        : this.$t("billing.noExpiry");
    },
    async load() {
      try {
        const [access, audit] = await Promise.all([
          this.$client.get(this.url + "grant/"),
          this.$client.get(this.url + "audit/"),
        ]);
        this.access = access.data;
        this.events = audit.data.results;
        if (this.access.grant) {
          const grant = this.access.grant;
          this.form = {
            plan: grant.plan,
            seat_limit: grant.seat_limit,
            reason: grant.reason,
          };
          if (grant.expires_at) {
            const date = new Date(grant.expires_at);
            date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
            this.expires = date.toISOString().slice(0, 16);
          }
        }
      } catch {
        this.error = true;
      }
    },
    async review() {
      if (this.busy) return;
      this.busy = true;
      this.error = false;
      try {
        const { data } = await this.$client.post(this.url + "grant/preview/", {
          ...this.form,
          starts_at: new Date().toISOString(),
          expires_at: this.expires
            ? new Date(this.expires).toISOString()
            : null,
        });
        this.preview = data;
        await this.$nextTick();
        this.$refs.confirm?.$el?.focus();
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async save() {
      if (this.busy) return;
      this.busy = true;
      this.error = false;
      try {
        const { data } = await this.$client.put(
          this.url + "grant/",
          this.preview,
        );
        this.access = data;
        this.preview = null;
        const audit = await this.$client.get(this.url + "audit/");
        this.events = audit.data.results;
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async performAction() {
      if (this.busy) return;
      this.busy = true;
      this.error = false;
      try {
        const action = this.pendingAction;
        const { data } = await this.$client.post(
          this.url + (action === "revoke" ? "grant/revoke/" : "suspension/"),
          {
            reason: this.form.reason,
            ...(action === "revoke" ? {} : { suspended: action === "suspend" }),
          },
        );
        this.access = data;
        this.pendingAction = null;
        const audit = await this.$client.get(this.url + "audit/");
        this.events = audit.data.results;
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
.billing-grant {
  border-block: 1px solid #e5e7eb;
  padding-block: 24px;
}
.billing-grant form {
  display: grid;
  gap: 12px;
  max-inline-size: 480px;
}
.billing-grant label {
  display: grid;
  gap: 8px;
}
.billing-grant__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-block: 16px;
}
</style>
