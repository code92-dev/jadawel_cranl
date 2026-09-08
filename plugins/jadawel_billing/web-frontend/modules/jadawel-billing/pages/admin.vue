<template>
  <div class="layout__col-2-scroll">
    <main class="billing-admin">
      <h1>{{ $t("billing.title") }}</h1>
      <p>{{ $t("billing.description") }}</p>
      <p v-if="error" role="alert">{{ $t("billing.error") }}</p>
      <p v-if="loading" role="status">{{ $t("billing.loading") }}</p>
      <section>
        <h2>{{ $t("billing.accounts") }}</h2>
        <form data-testid="account-form" @submit.prevent="createAccount">
          <label
            >{{ $t("billing.email")
            }}<input
              v-model="account.responsible_email"
              name="responsible_email"
              type="email"
              dir="ltr"
              required
              class="input"
          /></label>
          <label
            >{{ $t("billing.kind")
            }}<select v-model="account.kind" class="input">
              <option value="INDIVIDUAL">{{ $t("billing.individual") }}</option>
              <option value="TEAM">{{ $t("billing.team") }}</option>
            </select></label
          >
          <Button :disabled="saving" button-type="submit">{{
            $t("billing.createAccount")
          }}</Button>
        </form>
        <ul data-testid="account-list">
          <li v-for="item in accounts" :key="item.id">
            <bdi>{{ item.owner_email }}</bdi> ·
            {{ $t("billing." + item.kind.toLowerCase()) }}
            <small dir="ltr">{{ item.id }}</small>
            <Button type="secondary" @click="selectedAccount = item">{{
              $t("billing.manualAccess")
            }}</Button>
          </li>
        </ul>
        <p v-if="!loading && !accounts.length">{{ $t("billing.empty") }}</p>
        <Button
          v-if="accountsNext"
          type="secondary"
          @click="loadMoreAccounts"
          >{{ $t("billing.more") }}</Button
        >
      </section>
      <GrantPanel
        v-if="selectedAccount"
        :key="selectedAccount.id"
        :account="selectedAccount"
        :plans="plans"
      />
      <section>
        <h2>{{ $t("billing.plans") }}</h2>
        <form @submit.prevent="createPlan">
          <label
            >{{ $t("billing.code")
            }}<input
              v-model="plan.code"
              class="input"
              required
              pattern="[a-z0-9_-]+"
              dir="ltr"
          /></label>
          <label
            >{{ $t("billing.name")
            }}<input v-model="plan.name" class="input" required maxlength="100"
          /></label>
          <label
            >{{ $t("billing.kind")
            }}<select v-model="plan.kind" class="input">
              <option value="INDIVIDUAL">{{ $t("billing.individual") }}</option>
              <option value="TEAM">{{ $t("billing.team") }}</option>
            </select></label
          >
          <Button :disabled="saving" button-type="submit">{{
            $t("billing.createPlan")
          }}</Button>
        </form>
        <p>{{ $t("billing.priceNote") }}</p>
        <article v-for="item in plans" :key="item.id">
          <h3>
            <bdi>{{ item.name }}</bdi>
          </h3>
          <p>
            {{ $t(item.available ? "billing.available" : "billing.archived") }}
          </p>
          <Button
            type="secondary"
            :disabled="saving"
            @click="togglePlan(item)"
            >{{
              $t(item.available ? "billing.archive" : "billing.enable")
            }}</Button
          >
          <Button
            type="secondary"
            :disabled="saving"
            @click="selectPlan(item)"
            >{{ $t("billing.prices") }}</Button
          >
        </article>
        <Button v-if="plansNext" type="secondary" @click="loadMorePlans">{{
          $t("billing.more")
        }}</Button>
      </section>
      <section>
        <h2>{{ $t("billing.payments") }}</h2>
        <ul data-testid="payment-list">
          <li v-for="item in orders" :key="item.id">
            <bdi>{{ item.owner_email }}</bdi> ·
            <bdi>{{ item.payment_id }}</bdi> · {{ money(item.amount) }} ·
            {{ $t("billing.paymentStatus." + item.status) }}
            <Button
              v-if="item.status === 'pending'"
              type="secondary"
              :disabled="saving"
              @click="reconcileOrder(item)"
              >{{ $t("billing.reconcile") }}</Button
            >
            <Button
              v-if="
                item.status === 'paid' &&
                !['succeeded', 'processing'].includes(item.refund_status)
              "
              type="secondary"
              :disabled="saving"
              @click="selectRefund(item)"
              >{{ $t("billing.refund") }}</Button
            >
          </li>
        </ul>
        <p v-if="!loading && !orders.length">
          {{ $t("billing.emptyPayments") }}
        </p>
        <Button v-if="ordersNext" type="secondary" @click="loadMoreOrders">{{
          $t("billing.more")
        }}</Button>
        <form
          v-if="selectedRefundOrder"
          data-testid="refund-form"
          @submit.prevent="submitRefund"
        >
          <p>
            {{ $t("billing.refundableAmount") }}:
            {{ money(selectedRefundOrder.refundable_amount) }}
          </p>
          <label
            >{{ $t("billing.refundAmount")
            }}<input
              v-model.number="refund.amount"
              type="number"
              min="1"
              :max="selectedRefundOrder.refundable_amount"
              class="input"
              required
          /></label>
          <label
            >{{ $t("billing.reason")
            }}<textarea
              v-model="refund.reason"
              class="input"
              maxlength="500"
              required
            />
          </label>
          <Button :disabled="saving" button-type="submit">{{
            $t("billing.confirmRefund")
          }}</Button>
          <Button type="secondary" @click="selectedRefundOrder = null">{{
            $t("billing.cancel")
          }}</Button>
        </form>
        <p v-if="refundResult" role="status">
          {{ $t("billing.refundStatus") }}:
          {{ $t("billing.refundStates." + refundResult.status) }}
        </p>
      </section>
      <section>
        <h2>{{ $t("billing.externalPayments") }}</h2>
        <form
          data-testid="external-payment-form"
          @submit.prevent="recordExternalPayment"
        >
          <label
            >{{ $t("billing.accounts")
            }}<select v-model="externalPayment.account" required class="input">
              <option value="" disabled>{{ $t("billing.accounts") }}</option>
              <option v-for="item in accounts" :key="item.id" :value="item.id">
                {{ item.owner_email }} ·
                {{ $t("billing." + item.kind.toLowerCase()) }}
              </option>
            </select></label
          >
          <label
            >{{ $t("billing.amount")
            }}<input
              v-model.number="externalPayment.amount"
              type="number"
              min="1"
              class="input"
              required
          /></label>
          <label
            >{{ $t("billing.reference")
            }}<input
              v-model.trim="externalPayment.reference"
              dir="ltr"
              maxlength="120"
              class="input"
              required
          /></label>
          <label
            >{{ $t("billing.paidAt")
            }}<input
              v-model="externalPayment.paid_at"
              type="datetime-local"
              class="input"
              required
          /></label>
          <label
            >{{ $t("billing.notes")
            }}<textarea
              v-model="externalPayment.notes"
              maxlength="500"
              class="input"
            />
          </label>
          <Button :disabled="saving" button-type="submit">{{
            $t("billing.recordExternalPayment")
          }}</Button>
        </form>
        <ul data-testid="external-payment-list">
          <li v-for="payment in externalPayments" :key="payment.id">
            <bdi>{{ payment.reference }}</bdi> · {{ money(payment.amount) }} ·
            <time>{{ formatDate(payment.paid_at) }}</time>
          </li>
        </ul>
        <p v-if="!loading && !externalPayments.length">
          {{ $t("billing.emptyExternalPayments") }}
        </p>
      </section>
      <section>
        <h2>{{ $t("billing.providerEvents") }}</h2>
        <ul data-testid="provider-event-list">
          <li v-for="event in providerEvents" :key="event.id">
            <bdi>{{ event.event_id }}</bdi> ·
            <bdi>{{ event.payment_id }}</bdi> ·
            {{ $t("billing.eventStatus." + event.status) }} ·
            {{ $t("billing.attempts") }}: {{ event.attempts }}
            <span v-if="event.error_code">
              · <span dir="auto">{{ event.error_code }}</span>
            </span>
          </li>
        </ul>
        <p v-if="!loading && !providerEvents.length">
          {{ $t("billing.emptyProviderEvents") }}
        </p>
      </section>
      <section v-if="selectedPlan">
        <h2>
          {{ $t("billing.prices") }} — <bdi>{{ selectedPlan.name }}</bdi>
        </h2>
        <form @submit.prevent="createPrice">
          <label
            >{{ $t("billing.amount")
            }}<input
              v-model.number="price.amount"
              type="number"
              min="1"
              max="2147483647"
              step="1"
              class="input"
              required
              dir="ltr"
          /></label>
          <label
            >{{ $t("billing.interval")
            }}<select v-model="price.interval" class="input">
              <option value="MONTH">{{ $t("billing.month") }}</option>
              <option value="YEAR">{{ $t("billing.year") }}</option>
            </select></label
          >
          <Button :disabled="saving" button-type="submit">{{
            $t("billing.createPrice")
          }}</Button>
        </form>
        <ul>
          <li v-for="item in prices" :key="item.id">
            {{ money(item.amount) }} ·
            {{ $t("billing." + item.interval.toLowerCase()) }} ·
            {{ $t(item.available ? "billing.available" : "billing.archived") }}
            <Button
              type="secondary"
              :disabled="saving"
              @click="togglePrice(item)"
              >{{
                $t(item.available ? "billing.archive" : "billing.enable")
              }}</Button
            >
          </li>
        </ul>
        <Button v-if="pricesNext" type="secondary" @click="loadMorePrices">{{
          $t("billing.more")
        }}</Button>
      </section>
    </main>
  </div>
</template>

<script>
import GrantPanel from "../components/GrantPanel.vue";
export default {
  name: "BillingAdmin",
  components: { GrantPanel },
  layout: "app",
  middleware: "staff",
  data() {
    return {
      selectedAccount: null,
      loading: true,
      saving: false,
      error: false,
      accounts: [],
      accountsNext: null,
      plans: [],
      plansNext: null,
      orders: [],
      ordersNext: null,
      providerEvents: [],
      externalPayments: [],
      prices: [],
      pricesNext: null,
      selectedPlan: null,
      account: { kind: "INDIVIDUAL", responsible_email: "" },
      plan: { code: "", name: "", kind: "INDIVIDUAL" },
      price: { amount: 0, interval: "MONTH" },
      selectedRefundOrder: null,
      refund: { amount: 0, reason: "" },
      refundResult: null,
      externalPayment: {
        account: "",
        amount: 0,
        reference: "",
        paid_at: "",
        notes: "",
      },
    };
  },
  async mounted() {
    await this.refresh();
  },
  methods: {
    money(amount) {
      return new Intl.NumberFormat(this.$i18n.locale, {
        style: "currency",
        currency: "SAR",
      }).format(amount / 100);
    },
    formatDate(value) {
      return value ? new Date(value).toLocaleString(this.$i18n.locale) : "";
    },
    async refresh() {
      this.loading = true;
      this.error = false;
      try {
        const [accounts, plans, orders, providerEvents, externalPayments] =
          await Promise.all([
            this.$client.get("/billing/admin/accounts/"),
            this.$client.get("/billing/admin/plans/"),
            this.$client.get("/billing/admin/orders/"),
            this.$client.get("/billing/admin/provider-events/"),
            this.$client.get("/billing/admin/external-payments/"),
          ]);
        this.accounts = accounts.data.results;
        this.accountsNext = accounts.data.next;
        this.plans = plans.data.results;
        this.plansNext = plans.data.next;
        this.orders = orders.data.results;
        this.ordersNext = orders.data.next;
        this.providerEvents = providerEvents.data.results;
        this.externalPayments = externalPayments.data.results;
        if (!this.externalPayment.account) {
          this.externalPayment.account = this.accounts[0]?.id || "";
        }
      } catch {
        this.error = true;
      } finally {
        this.loading = false;
      }
    },
    async mutate(action) {
      if (this.saving) return;
      this.saving = true;
      this.error = false;
      try {
        await action();
      } catch {
        this.error = true;
      } finally {
        this.saving = false;
      }
    },
    async createAccount() {
      await this.mutate(async () => {
        await this.$client.post("/billing/admin/accounts/", this.account);
        await this.refresh();
        this.account.responsible_email = "";
      });
    },
    async createPlan() {
      await this.mutate(async () => {
        await this.$client.post("/billing/admin/plans/", this.plan);
        await this.refresh();
        this.plan.code = "";
        this.plan.name = "";
      });
    },
    async togglePlan(plan) {
      await this.mutate(async () => {
        await this.$client.patch("/billing/admin/plans/" + plan.id + "/", {
          available: !plan.available,
        });
        await this.refresh();
      });
    },
    async selectPlan(plan) {
      this.error = false;
      try {
        const { data } = await this.$client.get(
          "/billing/admin/plans/" + plan.id + "/prices/",
        );
        this.selectedPlan = plan;
        this.prices = data.results;
        this.pricesNext = data.next;
      } catch {
        this.error = true;
      }
    },
    async createPrice() {
      await this.mutate(async () => {
        await this.$client.post(
          "/billing/admin/plans/" + this.selectedPlan.id + "/prices/",
          this.price,
        );
        await this.selectPlan(this.selectedPlan);
      });
    },
    async togglePrice(price) {
      await this.mutate(async () => {
        await this.$client.patch("/billing/admin/prices/" + price.id + "/", {
          available: !price.available,
        });
        await this.selectPlan(this.selectedPlan);
      });
    },
    async loadPage(url, items, next) {
      if (this.saving) return;
      await this.mutate(async () => {
        const { data } = await this.$client.get(url);
        this[items].push(...data.results);
        this[next] = data.next;
      });
    },
    async loadMoreAccounts() {
      await this.loadPage(this.accountsNext, "accounts", "accountsNext");
    },
    async loadMorePlans() {
      await this.loadPage(this.plansNext, "plans", "plansNext");
    },
    async loadMoreOrders() {
      await this.loadPage(this.ordersNext, "orders", "ordersNext");
    },
    async loadMorePrices() {
      await this.loadPage(this.pricesNext, "prices", "pricesNext");
    },
    async reconcileOrder(order) {
      await this.mutate(async () => {
        const { data } = await this.$client.post(
          "/billing/admin/orders/" + order.id + "/reconcile/",
        );
        const index = this.orders.findIndex((item) => item.id === order.id);
        if (index !== -1) this.orders.splice(index, 1, data);
      });
    },
    selectRefund(order) {
      this.refund = {
        amount: order.refundable_amount || order.amount,
        reason: "",
      };
      this.refundResult = null;
      this.selectedRefundOrder = order;
    },
    async submitRefund() {
      if (!this.selectedRefundOrder) return;
      await this.mutate(async () => {
        const { data } = await this.$client.post(
          "/billing/admin/orders/" + this.selectedRefundOrder.id + "/refund/",
          this.refund,
        );
        this.refundResult = data;
        const index = this.orders.findIndex(
          (item) => item.id === this.selectedRefundOrder.id,
        );
        if (index !== -1) {
          this.orders.splice(index, 1, {
            ...this.orders[index],
            refund_status: data.status,
            refunded_amount: data.amount,
            refund_attempts: data.attempts,
            refund_last_error: data.last_error,
            refundable_amount:
              data.status === "succeeded"
                ? Math.max(0, this.orders[index].amount - data.amount)
                : data.amount,
          });
        }
        this.selectedRefundOrder = null;
      });
    },
    async recordExternalPayment() {
      await this.mutate(async () => {
        const { data } = await this.$client.post(
          "/billing/admin/external-payments/",
          {
            ...this.externalPayment,
            paid_at: new Date(this.externalPayment.paid_at).toISOString(),
          },
        );
        this.externalPayments.unshift(data);
        this.externalPayment.amount = 0;
        this.externalPayment.reference = "";
        this.externalPayment.paid_at = "";
        this.externalPayment.notes = "";
      });
    },
  },
};
</script>

<style scoped>
.billing-admin {
  max-inline-size: 960px;
  margin-inline: auto;
  padding: 32px;
  background: var(--jadawel-content-background, #fcfdfc);
}
.billing-admin section {
  margin-block: 32px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 8px;
  padding: 20px;
  background: var(--jadawel-raised-background, #fbfdfb);
}
.billing-admin form {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: end;
}
.billing-admin label {
  display: grid;
  gap: 8px;
}
.billing-admin input:not([type="checkbox"]),
.billing-admin select,
.billing-admin textarea {
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
.billing-admin input:focus,
.billing-admin select:focus,
.billing-admin textarea:focus {
  border-color: var(--jadawel-primary-500, #278053);
  outline: 2px solid
    color-mix(in srgb, var(--jadawel-primary-500, #278053) 28%, transparent);
  outline-offset: 1px;
}
.billing-admin li {
  margin-block: 12px;
}
.billing-admin small {
  display: inline-block;
  margin-inline-start: 8px;
}
.billing-admin article {
  border-block-end: 1px solid var(--jadawel-border-color, #e0f1e7);
  padding-block: 16px;
}
</style>
