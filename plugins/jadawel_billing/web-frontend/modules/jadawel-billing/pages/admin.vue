<template>
  <div class="layout__col-2-scroll">
    <main class="billing-admin">
      <header class="billing-admin__header">
        <div>
          <h1>{{ $t("billing.title") }}</h1>
          <p>{{ $t("billing.description") }}</p>
        </div>
        <span v-if="providerHealth" class="billing-admin__status" role="status">
          {{
            $t(
              `billing.providerHealthStatus.${providerHealth.status}`,
              providerHealth.status,
            )
          }}
        </span>
      </header>
      <p v-if="error" role="alert">
        {{ $t("billing.error") }}
        <span v-if="errorDetail" dir="auto">— {{ errorDetail }}</span>
      </p>
      <p v-if="loading" role="status">{{ $t("billing.loading") }}</p>
      <ul
        class="billing-admin__summary"
        :aria-label="$t('billing.adminSummary')"
      >
        <li>
          <strong>{{ accounts.length }}</strong>
          <span>{{ $t("billing.summary.accounts") }}</span>
        </li>
        <li>
          <strong>{{ plans.length }}</strong>
          <span>{{ $t("billing.summary.plans") }}</span>
        </li>
        <li>
          <strong>{{ orders.length }}</strong>
          <span>{{ $t("billing.summary.payments") }}</span>
        </li>
        <li>
          <strong>{{ subscriptions.length }}</strong>
          <span>{{ $t("billing.summary.subscriptions") }}</span>
        </li>
      </ul>
      <nav
        class="billing-admin__tabs"
        :aria-label="$t('billing.adminSections')"
        role="tablist"
      >
        <button
          v-for="section in adminSections"
          :key="section.id"
          :id="`billing-admin-tab-${section.id}`"
          type="button"
          role="tab"
          :aria-selected="adminSection === section.id"
          :aria-controls="`billing-admin-${section.id}`"
          :class="{ 'is-selected': adminSection === section.id }"
          @click="adminSection = section.id"
        >
          {{ $t(`billing.sections.${section.id}`) }}
        </button>
      </nav>
      <section
        v-show="adminSection === 'accounts'"
        id="billing-admin-accounts"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-accounts"
      >
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
        <GrantPanel
          v-if="selectedAccount"
          :key="selectedAccount.id"
          :account="selectedAccount"
          :plans="plans"
        />
      </section>
      <section
        v-show="adminSection === 'plans'"
        id="billing-admin-plans"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-plans"
      >
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
            @click="requestPlanToggle(item)"
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
        <div
          v-if="pendingPlan"
          class="billing-admin__confirmation"
          role="alertdialog"
        >
          <p>
            {{
              $t(
                pendingPlan.available
                  ? "billing.confirmArchivePlan"
                  : "billing.confirmEnablePlan",
                { name: pendingPlan.name },
              )
            }}
          </p>
          <Button
            button-type="button"
            :disabled="saving"
            @click="togglePlan(pendingPlan)"
            >{{ $t("billing.confirm") }}</Button
          >
          <Button
            type="secondary"
            button-type="button"
            @click="pendingPlan = null"
            >{{ $t("billing.cancel") }}</Button
          >
        </div>
        <Button v-if="plansNext" type="secondary" @click="loadMorePlans">{{
          $t("billing.more")
        }}</Button>
      </section>
      <section
        v-show="adminSection === 'payments'"
        id="billing-admin-payments"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-payments"
      >
        <h2>{{ $t("billing.payments") }}</h2>
        <form class="billing-history-search" @submit.prevent="refresh">
          <label>
            {{ $t("billing.searchHistory") }}
            <input
              v-model.trim="orderSearch"
              type="search"
              class="input"
              :placeholder="$t('billing.searchHistory')"
            />
          </label>
          <Button type="secondary" button-type="submit" :disabled="loading">
            {{ $t("billing.search") }}
          </Button>
        </form>
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
          @submit.prevent="reviewRefund"
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
            $t("billing.reviewRefund")
          }}</Button>
          <Button type="secondary" @click.prevent="cancelRefund">{{
            $t("billing.cancel")
          }}</Button>
        </form>
        <div
          v-if="pendingRefund"
          class="billing-admin__confirmation"
          role="alertdialog"
        >
          <p>
            {{
              $t("billing.confirmRefundDescription", {
                amount: money(refund.amount),
              })
            }}
          </p>
          <Button
            button-type="button"
            :disabled="saving"
            @click="submitRefund"
            >{{ $t("billing.confirmRefund") }}</Button
          >
          <Button type="secondary" button-type="button" @click="cancelRefund">{{
            $t("billing.cancel")
          }}</Button>
        </div>
        <p v-if="refundResult" role="status">
          {{ $t("billing.refundStatus") }}:
          {{ $t("billing.refundStates." + refundResult.status) }}
        </p>
      </section>
      <section
        v-show="adminSection === 'subscriptions'"
        id="billing-admin-subscriptions"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-subscriptions"
      >
        <h2>{{ $t("billing.subscriptions") }}</h2>
        <form
          class="billing-history-search"
          @submit.prevent="loadSubscriptions"
        >
          <label>
            {{ $t("billing.searchHistory") }}
            <input
              v-model.trim="subscriptionSearch"
              type="search"
              class="input"
              :placeholder="$t('billing.searchHistory')"
            />
          </label>
          <Button type="secondary" button-type="submit" :disabled="loading">
            {{ $t("billing.search") }}
          </Button>
        </form>
        <ul data-testid="subscription-list">
          <li v-for="item in subscriptions" :key="item.id">
            <bdi>{{ item.owner_email }}</bdi> · <bdi>{{ item.plan }}</bdi> ·
            {{ $t("billing.seats") }}: {{ item.seats }} ·
            {{ $t("billing.subscriptionStatus." + item.status) }} ·
            {{ $t("billing.renewalThrough") }}:
            <time>{{ formatDate(item.period_end) }}</time>
            <Button
              v-if="item.status !== 'canceled'"
              type="secondary"
              :disabled="saving"
              @click="requestSubscriptionToggle(item)"
            >
              {{
                item.cancel_at_period_end
                  ? $t("billing.resumeRenewal")
                  : $t("billing.cancelRenewal")
              }}
            </Button>
          </li>
        </ul>
        <div
          v-if="pendingSubscription"
          class="billing-admin__confirmation"
          role="alertdialog"
        >
          <p>
            {{
              $t(
                pendingSubscription.cancel_at_period_end
                  ? "billing.confirmResumeRenewal"
                  : "billing.confirmCancelRenewal",
              )
            }}
          </p>
          <Button
            button-type="button"
            :disabled="saving"
            @click="toggleSubscription(pendingSubscription)"
            >{{ $t("billing.confirm") }}</Button
          >
          <Button
            type="secondary"
            button-type="button"
            @click="pendingSubscription = null"
            >{{ $t("billing.cancel") }}</Button
          >
        </div>
        <p v-if="!loading && !subscriptions.length">
          {{ $t("billing.emptySubscriptions") }}
        </p>
        <Button
          v-if="subscriptionsNext"
          type="secondary"
          @click="loadMoreSubscriptions"
        >
          {{ $t("billing.more") }}
        </Button>
      </section>
      <section
        v-show="adminSection === 'external'"
        id="billing-admin-external"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-external"
      >
        <h2>{{ $t("billing.externalPayments") }}</h2>
        <form
          class="billing-history-search"
          @submit.prevent="loadExternalPayments"
        >
          <label>
            {{ $t("billing.searchHistory") }}
            <input
              v-model.trim="externalPaymentSearch"
              type="search"
              class="input"
              :placeholder="$t('billing.searchHistory')"
            />
          </label>
          <Button type="secondary" button-type="submit" :disabled="loading">
            {{ $t("billing.search") }}
          </Button>
        </form>
        <form
          data-testid="external-payment-form"
          @submit.prevent="recordExternalPayment"
        >
          <label
            >{{ $t("billing.accounts")
            }}<select v-model="externalPayment.account" required class="input">
              <option value="" disabled>{{ $t("billing.accounts") }}</option>
              <option
                v-for="item in accounts"
                :key="item.id"
                :value="item.id"
                dir="auto"
              >
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
        <Button
          v-if="externalPaymentsNext"
          type="secondary"
          :disabled="loading"
          @click="loadMoreExternalPayments"
        >
          {{ $t("billing.more") }}
        </Button>
        <p v-if="!loading && !externalPayments.length">
          {{ $t("billing.emptyExternalPayments") }}
        </p>
      </section>
      <section
        v-show="adminSection === 'provider'"
        id="billing-admin-provider"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-provider"
      >
        <h2>{{ $t("billing.providerEvents") }}</h2>
        <form
          class="billing-history-search"
          @submit.prevent="loadProviderEvents"
        >
          <label>
            {{ $t("billing.searchHistory") }}
            <input
              v-model.trim="providerEventSearch"
              type="search"
              class="input"
              :placeholder="$t('billing.searchHistory')"
            />
          </label>
          <Button type="secondary" button-type="submit" :disabled="loading">
            {{ $t("billing.search") }}
          </Button>
        </form>
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
        <Button
          v-if="providerEventsNext"
          type="secondary"
          :disabled="loading"
          @click="loadMoreProviderEvents"
        >
          {{ $t("billing.more") }}
        </Button>
      </section>
      <section
        v-show="adminSection === 'provider'"
        id="billing-admin-provider-health"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-provider"
      >
        <h2>{{ $t("billing.providerHealth") }}</h2>
        <p v-if="providerHealth" role="status">
          {{ $t("billing.providerHealthMode") }}: {{ providerHealth.mode }} ·
          {{
            $t(
              `billing.providerHealthStatus.${providerHealth.status}`,
              providerHealth.status,
            )
          }}
        </p>
        <Button
          type="secondary"
          :disabled="loading"
          @click="checkProviderHealth"
        >
          {{ $t("billing.providerHealthCheck") }}
        </Button>
      </section>
      <section
        v-if="selectedPlan"
        v-show="adminSection === 'plans'"
        id="billing-admin-prices"
        role="tabpanel"
        aria-labelledby="billing-admin-tab-plans"
      >
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

<script setup>
definePageMeta({
  layout: "app",
  middleware: "staff",
});
</script>

<script>
/* eslint-disable import/first -- Nuxt page metadata uses a separate setup block. */
import GrantPanel from "../components/GrantPanel.vue";
import { describeApiError } from "../utils/apiError";
/* eslint-enable import/first */
export default {
  name: "BillingAdmin",
  components: { GrantPanel },
  data() {
    return {
      adminSection: "accounts",
      adminSections: [
        { id: "accounts" },
        { id: "plans" },
        { id: "payments" },
        { id: "subscriptions" },
        { id: "external" },
        { id: "provider" },
      ],
      selectedAccount: null,
      pendingPlan: null,
      pendingSubscription: null,
      loading: true,
      saving: false,
      error: false,
      errorDetail: "",
      accounts: [],
      accountsNext: null,
      plans: [],
      plansNext: null,
      orders: [],
      ordersNext: null,
      orderSearch: "",
      subscriptions: [],
      subscriptionsNext: null,
      subscriptionSearch: "",
      providerEvents: [],
      providerEventsNext: null,
      providerEventSearch: "",
      externalPayments: [],
      externalPaymentsNext: null,
      externalPaymentSearch: "",
      providerHealth: null,
      prices: [],
      pricesNext: null,
      selectedPlan: null,
      account: { kind: "INDIVIDUAL", responsible_email: "" },
      plan: { code: "", name: "", kind: "INDIVIDUAL" },
      price: { amount: 0, interval: "MONTH" },
      selectedRefundOrder: null,
      pendingRefund: false,
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
    // The admin endpoints answer with DRF field errors ("responsible_email":
    // "user_not_found"). Swallowing them left a 400 in the console and no way
    // to tell which field the server rejected.
    fail(error) {
      this.error = true;
      this.errorDetail = describeApiError(error);
    },
    formatDate(value) {
      return value ? new Date(value).toLocaleString(this.$i18n.locale) : "";
    },
    async refresh() {
      this.loading = true;
      this.error = false;
      this.errorDetail = "";
      try {
        const [
          accounts,
          plans,
          orders,
          subscriptions,
          providerEvents,
          externalPayments,
          health,
        ] = await Promise.all([
          this.$client.get("/billing/admin/accounts/"),
          this.$client.get("/billing/admin/plans/"),
          this.$client.get("/billing/admin/orders/", {
            params: this.orderSearch ? { search: this.orderSearch } : {},
          }),
          this.$client
            .get("/billing/admin/subscriptions/", {
              params: this.subscriptionSearch
                ? { search: this.subscriptionSearch }
                : {},
            })
            .catch(() => ({ data: { results: [], next: null } })),
          this.$client.get("/billing/admin/provider-events/", {
            params: this.providerEventSearch
              ? { search: this.providerEventSearch }
              : {},
          }),
          this.$client.get("/billing/admin/external-payments/", {
            params: this.externalPaymentSearch
              ? { search: this.externalPaymentSearch }
              : {},
          }),
          this.$client
            .get("/billing/admin/provider-health/")
            .catch(() => ({ data: null })),
        ]);
        this.accounts = accounts.data.results;
        this.accountsNext = accounts.data.next;
        this.plans = plans.data.results;
        this.plansNext = plans.data.next;
        this.orders = orders.data.results;
        this.ordersNext = orders.data.next;
        this.subscriptions = subscriptions.data.results;
        this.subscriptionsNext = subscriptions.data.next;
        this.providerEvents = providerEvents.data.results;
        this.providerEventsNext = providerEvents.data.next;
        this.externalPayments = externalPayments.data.results;
        this.externalPaymentsNext = externalPayments.data.next;
        this.providerHealth = health.data;
        if (!this.externalPayment.account) {
          this.externalPayment.account = this.accounts[0]?.id || "";
        }
      } catch (error) {
        this.fail(error);
      } finally {
        this.loading = false;
      }
    },
    async mutate(action) {
      if (this.saving) return;
      this.saving = true;
      this.error = false;
      this.errorDetail = "";
      try {
        await action();
      } catch (error) {
        this.fail(error);
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
        this.pendingPlan = null;
      });
    },
    requestPlanToggle(plan) {
      this.pendingPlan = plan;
    },
    async selectPlan(plan) {
      this.error = false;
      this.errorDetail = "";
      try {
        const { data } = await this.$client.get(
          "/billing/admin/plans/" + plan.id + "/prices/",
        );
        this.selectedPlan = plan;
        this.prices = data.results;
        this.pricesNext = data.next;
      } catch (error) {
        this.fail(error);
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
    async loadSubscriptions() {
      await this.mutate(async () => {
        const { data } = await this.$client.get(
          "/billing/admin/subscriptions/",
          {
            params: this.subscriptionSearch
              ? { search: this.subscriptionSearch }
              : {},
          },
        );
        this.subscriptions = data.results;
        this.subscriptionsNext = data.next;
      });
    },
    async loadMoreSubscriptions() {
      await this.loadPage(
        this.subscriptionsNext,
        "subscriptions",
        "subscriptionsNext",
      );
    },
    async toggleSubscription(subscription) {
      await this.mutate(async () => {
        const { data } = await this.$client.patch(
          "/billing/admin/subscriptions/" + subscription.id + "/",
          { cancel_at_period_end: !subscription.cancel_at_period_end },
        );
        const index = this.subscriptions.findIndex(
          (item) => item.id === subscription.id,
        );
        if (index !== -1) this.subscriptions.splice(index, 1, data);
        this.pendingSubscription = null;
      });
    },
    requestSubscriptionToggle(subscription) {
      this.pendingSubscription = subscription;
    },
    async loadProviderEvents() {
      await this.mutate(async () => {
        const { data } = await this.$client.get(
          "/billing/admin/provider-events/",
          {
            params: this.providerEventSearch
              ? { search: this.providerEventSearch }
              : {},
          },
        );
        this.providerEvents = data.results;
        this.providerEventsNext = data.next;
      });
    },
    async loadMoreProviderEvents() {
      await this.loadPage(
        this.providerEventsNext,
        "providerEvents",
        "providerEventsNext",
      );
    },
    async loadExternalPayments() {
      await this.mutate(async () => {
        const { data } = await this.$client.get(
          "/billing/admin/external-payments/",
          {
            params: this.externalPaymentSearch
              ? { search: this.externalPaymentSearch }
              : {},
          },
        );
        this.externalPayments = data.results;
        this.externalPaymentsNext = data.next;
      });
    },
    async loadMoreExternalPayments() {
      await this.loadPage(
        this.externalPaymentsNext,
        "externalPayments",
        "externalPaymentsNext",
      );
    },
    async checkProviderHealth() {
      await this.mutate(async () => {
        const { data } = await this.$client.get(
          "/billing/admin/provider-health/",
        );
        this.providerHealth = data;
      });
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
      this.pendingRefund = false;
    },
    reviewRefund() {
      if (!this.selectedRefundOrder || this.saving) return;
      this.pendingRefund = true;
    },
    cancelRefund() {
      this.selectedRefundOrder = null;
      this.pendingRefund = false;
    },
    async submitRefund() {
      if (!this.selectedRefundOrder || this.saving) return;
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
        this.pendingRefund = false;
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
  max-inline-size: 1180px;
  margin-inline: auto;
  padding: 32px;
  background: var(--jadawel-content-background, #fcfdfc);
}
.billing-admin__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-block-end: 24px;
}
.billing-admin__eyebrow {
  margin: 0;
  color: var(--jadawel-primary-500, #278053);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.billing-admin__status {
  padding: 8px 12px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 999px;
  white-space: nowrap;
}
.billing-admin__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-block: 0 24px;
}
.billing-admin__summary li {
  display: grid;
  gap: 4px;
  margin: 0;
  padding: 14px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 8px;
  background: var(--jadawel-raised-background, #fbfdfb);
}
.billing-admin__summary strong {
  color: var(--jadawel-primary-500, #278053);
  font-size: 24px;
  line-height: 1;
}
.billing-admin__summary span {
  color: var(--jadawel-text-secondary, #66756d);
  font-size: 12px;
}
.billing-admin__tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-block-end: 24px;
  border-block-end: 1px solid var(--jadawel-border-color, #e0f1e7);
}
.billing-admin__tabs button {
  border: 0;
  border-block-end: 3px solid transparent;
  padding: 10px 12px;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}
.billing-admin__tabs button.is-selected {
  border-block-end-color: var(--jadawel-primary-500, #278053);
  color: var(--jadawel-primary-500, #278053);
  font-weight: 700;
}
.billing-admin__confirmation {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-block: 12px;
  padding: 14px;
  border: 1px solid var(--jadawel-warning-500, #b7791f);
  border-radius: 8px;
  background: color-mix(
    in srgb,
    var(--jadawel-warning-500, #b7791f) 8%,
    transparent
  );
}
.billing-admin section {
  box-shadow: 0 8px 24px rgb(20 65 42 / 6%);
}
.billing-admin ul {
  padding: 0;
  list-style: none;
}
.billing-admin li {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px;
  border-block-end: 1px solid var(--jadawel-border-color, #e0f1e7);
}
@media (max-width: 640px) {
  .billing-admin {
    padding: 20px 16px;
  }
  .billing-admin__header {
    flex-direction: column;
  }
  .billing-admin__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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
