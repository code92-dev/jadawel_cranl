<template>
  <div class="layout__col-2-scroll">
    <main class="customer-billing">
      <h1>{{ $t("billing.title") }}</h1>
      <p v-if="error" role="alert">{{ $t("billing.paymentError") }}</p>
      <p v-if="loading" role="status">{{ $t("billing.loading") }}</p>
      <template v-if="options">
        <p v-if="options.mode === 'test'" role="status">
          {{ $t("billing.sandbox") }}
        </p>
        <section
          v-if="accountState"
          class="billing-account"
          data-testid="account-state"
        >
          <h2>{{ $t("billing.accountStatus") }}</h2>
          <p role="status">
            {{ $t("billing.source." + accountState.effective.source) }} ·
            {{ $t("billing.seats") }}:
            {{ accountState.effective.seat_limit }}
          </p>
          <p v-if="accountState.effective.valid_until">
            {{ $t("billing.accessUntil") }}:
            <time>{{ formatDate(accountState.effective.valid_until) }}</time>
          </p>
          <template v-if="accountState.subscription">
            <p>
              {{
                $t("billing.renewal", {
                  date: formatDate(accountState.subscription.period_end),
                })
              }}
            </p>
            <Button
              type="secondary"
              :disabled="busy"
              @click="toggleCancellation"
            >
              {{
                accountState.subscription.cancel_at_period_end
                  ? $t("billing.resumeRenewal")
                  : $t("billing.cancelRenewal")
              }}
            </Button>
            <form @submit.prevent="scheduleChange">
              <label>
                {{ $t("billing.changePlan") }}
                <select v-model.number="subscriptionChange.price" class="input">
                  <option
                    v-for="item in availablePrices"
                    :key="item.id"
                    :value="item.id"
                  >
                    {{ item.name }} — {{ money(item.amount) }} /
                    {{ $t("billing." + item.interval.toLowerCase()) }}
                  </option>
                </select>
              </label>
              <label v-if="selectedAccountKind === 'TEAM'">
                {{ $t("billing.changeSeats") }}
                <input
                  v-model.number="subscriptionChange.seats"
                  type="number"
                  min="1"
                  :max="accountState.subscription.seats"
                  required
                  class="input"
                />
              </label>
              <Button type="secondary" :disabled="busy" button-type="submit">
                {{ $t("billing.scheduleChange") }}
              </Button>
            </form>
            <form
              v-if="selectedAccountKind === 'TEAM'"
              @submit.prevent="increaseSeatsNow"
            >
              <label>
                {{ $t("billing.addSeats") }}
                <input
                  v-model.number="seatIncrease.seats"
                  type="number"
                  :min="accountState.subscription.seats + 1"
                  required
                  class="input"
                />
              </label>
              <Button type="secondary" :disabled="busy" button-type="submit">
                {{ $t("billing.purchaseSeats") }}
              </Button>
            </form>
          </template>
        </section>
        <section v-if="accountState" class="payment-methods">
          <h2>{{ $t("billing.paymentMethods") }}</h2>
          <p v-if="!paymentMethods.length">
            {{ $t("billing.noPaymentMethods") }}
          </p>
          <ul v-else>
            <li v-for="method in paymentMethods" :key="method.id">
              <bdi>{{ method.brand }}</bdi> ·
              <span dir="ltr">•••• {{ method.last4 }}</span>
              <Button
                type="secondary"
                :disabled="busy"
                @click="revokePaymentMethod(method)"
              >
                {{ $t("billing.removePaymentMethod") }}
              </Button>
            </li>
          </ul>
        </section>
        <form v-if="!order" @submit.prevent="prepare">
          <label
            >{{ $t("billing.accounts")
            }}<select
              v-model="account"
              required
              class="input"
              @change="loadAccount"
            >
              <option
                v-for="item in options.accounts"
                :key="item.id"
                :value="item.id"
              >
                {{ $t("billing." + item.kind.toLowerCase()) }} — {{ item.id }}
              </option>
            </select></label
          >
          <label v-if="selectedAccountKind === 'TEAM'">
            {{ $t("billing.seats") }}
            <input
              v-model.number="seats"
              type="number"
              min="1"
              required
              class="input"
            />
          </label>
          <label
            >{{ $t("billing.plans")
            }}<select v-model="price" required class="input">
              <option
                v-for="item in availablePrices"
                :key="item.id"
                :value="item.id"
              >
                {{ item.name }} — {{ money(item.amount) }} /
                {{ $t("billing." + item.interval.toLowerCase()) }}
              </option>
            </select></label
          >
          <Button button-type="submit" :disabled="busy">{{
            $t("billing.checkout")
          }}</Button>
        </form>
        <section v-if="order">
          <h2>{{ money(order.amount) }}</h2>
          <p role="status">{{ $t("billing.paymentStatus." + order.status) }}</p>
          <section v-if="order.receipt" data-testid="receipt" role="region">
            <h3>{{ $t("billing.receipt") }}</h3>
            <p>
              {{ $t("billing.providerReference") }}:
              <bdi>{{ order.receipt.provider_payment_id }}</bdi>
            </p>
            <p v-if="order.receipt.period_end">
              {{ $t("billing.periodEnd") }}:
              <time>{{
                new Date(order.receipt.period_end).toLocaleDateString(
                  $i18n.locale,
                )
              }}</time>
            </p>
          </section>
          <p v-if="order.purpose === 'seat_increase'">
            {{ $t("billing.proratedSeatIncrease") }}
          </p>
          <p v-else>{{ $t("billing.singlePeriod") }}</p>
          <form
            v-if="order.status === 'pending' && !submitted"
            @submit.prevent="pay"
          >
            <label
              >{{ $t("billing.cardName")
              }}<input
                v-model="card.name"
                autocomplete="cc-name"
                required
                class="input"
            /></label>
            <label
              >{{ $t("billing.cardNumber")
              }}<input
                v-model="card.number"
                autocomplete="cc-number"
                inputmode="numeric"
                pattern="[0-9 ]{12,23}"
                dir="ltr"
                required
                class="input"
            /></label>
            <label
              >{{ $t("billing.cardMonth")
              }}<input
                v-model.number="card.month"
                autocomplete="cc-exp-month"
                inputmode="numeric"
                pattern="0?[1-9]|1[0-2]"
                dir="ltr"
                required
                class="input"
            /></label>
            <label
              >{{ $t("billing.cardYear")
              }}<input
                v-model.number="card.year"
                autocomplete="cc-exp-year"
                inputmode="numeric"
                pattern="[0-9]{4}"
                dir="ltr"
                required
                class="input"
            /></label>
            <label
              >{{ $t("billing.cardCvc")
              }}<input
                v-model="card.cvc"
                type="password"
                autocomplete="cc-csc"
                inputmode="numeric"
                pattern="[0-9]{3,4}"
                dir="ltr"
                required
                class="input"
            /></label>
            <label>
              <input v-model="saveCard" type="checkbox" />
              {{ $t("billing.saveCard") }}
            </label>
            <Button button-type="submit" :disabled="busy">{{
              $t("billing.pay")
            }}</Button>
          </form>
          <Button
            v-if="order.status === 'pending' && order.provider_payment_id"
            type="secondary"
            :disabled="busy"
            @click="verify()"
            >{{ $t("billing.verifyPayment") }}</Button
          >
          <Button
            v-if="
              order.status === 'pending' &&
              submitted &&
              !order.provider_payment_id
            "
            type="secondary"
            :disabled="busy"
            @click="startOver"
            >{{ $t("billing.retryPayment") }}</Button
          >
          <Button
            v-if="order.status === 'failed'"
            type="secondary"
            @click="startOver"
            >{{ $t("billing.retryPayment") }}</Button
          >
        </section>
      </template>
      <h2>{{ $t("billing.paymentHistory") }}</h2>
      <ul>
        <li v-for="item in history" :key="item.id">
          <bdi>{{ item.id }}</bdi> — {{ money(item.amount) }} —
          {{ $t("billing.paymentStatus." + item.status) }}
          <Button
            v-if="item.status === 'pending'"
            type="secondary"
            @click="resume(item)"
            >{{ $t("billing.verifyPayment") }}</Button
          >
        </li>
      </ul>
    </main>
  </div>
</template>

<script>
import { submitPayment } from "../payment";

export default {
  name: "CustomerBilling",
  layout: "app",
  middleware: "authenticated",
  data() {
    return {
      options: null,
      account: "",
      accountState: null,
      paymentMethods: [],
      price: "",
      order: null,
      history: [],
      seats: 1,
      saveCard: false,
      busy: false,
      loading: true,
      error: false,
      submitted: false,
      card: { name: "", number: "", month: "", year: "", cvc: "" },
      subscriptionChange: { price: null, seats: 1 },
      seatIncrease: { seats: 2 },
    };
  },
  computed: {
    selectedAccountKind() {
      return (
        this.options?.accounts.find((item) => item.id === this.account)?.kind ||
        "INDIVIDUAL"
      );
    },
    availablePrices() {
      return (this.options?.prices || []).filter(
        (item) => item.kind === this.selectedAccountKind,
      );
    },
  },
  async mounted() {
    try {
      const [options, history] = await Promise.all([
        this.$client.get("/billing/checkout/"),
        this.$client.get("/billing/orders/"),
      ]);
      this.options = options.data;
      this.history = history.data;
      this.account =
        this.$route.query.account || this.options.accounts[0]?.id || "";
      this.price = this.options.prices[0]?.id || "";
      await this.loadAccount();
      const returnedOrder = this.$route.query.order;
      if (returnedOrder) {
        this.order =
          this.history.find((item) => item.id === returnedOrder) || null;
        this.submitted = true;
        if (this.order) {
          await this.verify(
            this.$route.query.provider_payment_id || this.$route.query.id,
          );
        }
      }
    } catch {
      this.error = true;
    } finally {
      this.loading = false;
    }
  },
  beforeUnmount() {
    this.clearCard();
  },
  methods: {
    money(amount) {
      return new Intl.NumberFormat(this.$i18n.locale, {
        style: "currency",
        currency: "SAR",
      }).format(amount / 100);
    },
    clearCard() {
      this.card = { name: "", number: "", month: "", year: "", cvc: "" };
    },
    formatDate(value) {
      return value ? new Date(value).toLocaleString(this.$i18n.locale) : "";
    },
    async loadAccount() {
      if (!this.account) return;
      const [account, methods] = await Promise.all([
        this.$client.get("/billing/accounts/" + this.account + "/"),
        this.$client.get(
          "/billing/accounts/" + this.account + "/payment-methods/",
        ),
      ]);
      this.accountState = account.data;
      this.paymentMethods = methods.data;
      if (this.accountState.subscription) {
        this.subscriptionChange = {
          price: this.accountState.subscription.price,
          seats: this.accountState.subscription.seats,
        };
        this.seatIncrease = {
          seats: this.accountState.subscription.seats + 1,
        };
      }
    },
    async toggleCancellation() {
      await this.runAccountAction(() =>
        this.$client.post(
          "/billing/accounts/" + this.account + "/subscription/cancellation/",
          { cancel: !this.accountState.subscription.cancel_at_period_end },
        ),
      );
    },
    async scheduleChange() {
      await this.runAccountAction(() =>
        this.$client.post(
          "/billing/accounts/" + this.account + "/subscription/change/",
          this.subscriptionChange,
        ),
      );
    },
    async increaseSeatsNow() {
      if (this.busy) return;
      this.busy = true;
      this.error = false;
      try {
        const { data } = await this.$client.post(
          "/billing/accounts/" + this.account + "/subscription/seat-increase/",
          this.seatIncrease,
        );
        this.order = data;
        this.submitted = false;
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async revokePaymentMethod(method) {
      await this.runAccountAction(() =>
        this.$client.delete(
          "/billing/accounts/" +
            this.account +
            "/payment-methods/" +
            method.id +
            "/",
        ),
      );
    },
    async runAccountAction(action) {
      if (this.busy) return;
      this.busy = true;
      this.error = false;
      try {
        await action();
        await this.loadAccount();
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async prepare() {
      this.busy = true;
      this.error = false;
      try {
        const { data } = await this.$client.post("/billing/orders/", {
          account: this.account,
          price: this.price,
          seats: this.selectedAccountKind === "TEAM" ? this.seats : 1,
        });
        this.order = data;
        this.submitted = false;
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async pay() {
      if (this.busy) return;
      this.busy = true;
      this.error = false;
      this.submitted = true;
      try {
        const callback = new URL("/billing", window.location.origin);
        callback.searchParams.set("order", this.order.id);
        const payment = await submitPayment(
          this.order,
          this.options.publishable_key,
          { ...this.card, number: this.card.number.replaceAll(" ", "") },
          callback.toString(),
        );
        this.clearCard();
        if (payment.source?.transaction_url) {
          const redirect = new URL(payment.source.transaction_url);
          if (
            redirect.protocol !== "https:" ||
            redirect.hostname !== "api.moyasar.com"
          )
            throw new Error("invalid_redirect");
          window.location.assign(redirect.toString());
          return;
        }
        const verifiedOrder = await this.verify(payment.id);
        if (
          this.saveCard &&
          payment.source?.token &&
          verifiedOrder?.status === "paid"
        ) {
          await this.$client.post(
            "/billing/accounts/" + this.account + "/payment-methods/",
            {
              provider_token: payment.source.token,
              provider_payment_id: payment.id,
              consent: true,
              brand: payment.source.brand || "",
              last4: payment.source.last4 || "",
              exp_month: payment.source.month,
              exp_year: payment.source.year,
            },
          );
        }
      } catch {
        this.error = true;
      } finally {
        this.clearCard();
        this.busy = false;
      }
    },
    async verify(providerPaymentId = null) {
      this.busy = true;
      this.error = false;
      try {
        const { data } = await this.$client.post(
          "/billing/orders/" + this.order.id + "/verify/",
          providerPaymentId ? { provider_payment_id: providerPaymentId } : {},
        );
        this.order = data;
        this.history = (await this.$client.get("/billing/orders/")).data;
        await this.loadAccount();
        return data;
      } catch {
        this.error = true;
      } finally {
        this.busy = false;
      }
    },
    async resume(order) {
      this.order = order;
      this.submitted = true;
      await this.verify(order.provider_payment_id);
    },
    startOver() {
      this.order = null;
      this.submitted = false;
      this.error = false;
    },
  },
};
</script>

<style scoped>
.customer-billing {
  max-inline-size: 720px;
  margin-inline: auto;
  padding: 32px;
  background: var(--jadawel-content-background, #fcfdfc);
}
.customer-billing section {
  margin-block: 32px;
  border: 1px solid var(--jadawel-border-color, #e0f1e7);
  border-radius: 8px;
  padding: 20px;
  background: var(--jadawel-raised-background, #fbfdfb);
}
.customer-billing form {
  display: grid;
  gap: 16px;
  max-inline-size: 480px;
  margin-block: 24px;
}
.customer-billing label {
  display: grid;
  gap: 8px;
}
.customer-billing input:not([type="checkbox"]),
.customer-billing select,
.customer-billing textarea {
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
.customer-billing input:focus,
.customer-billing select:focus,
.customer-billing textarea:focus {
  border-color: var(--jadawel-primary-500, #278053);
  outline: 2px solid
    color-mix(in srgb, var(--jadawel-primary-500, #278053) 28%, transparent);
  outline-offset: 1px;
}
.customer-billing li {
  margin-block: 16px;
  overflow-wrap: anywhere;
}
</style>
