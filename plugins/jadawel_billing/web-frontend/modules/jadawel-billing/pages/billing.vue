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
        <form v-if="!order" @submit.prevent="prepare">
          <label
            >{{ $t("billing.accounts")
            }}<select v-model="account" required class="input">
              <option
                v-for="item in options.accounts"
                :key="item.id"
                :value="item.id"
              >
                {{ $t("billing.individual") }} — {{ item.id }}
              </option>
            </select></label
          >
          <label
            >{{ $t("billing.plans")
            }}<select v-model="price" required class="input">
              <option
                v-for="item in options.prices"
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
          <p>{{ $t("billing.singlePeriod") }}</p>
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
            <Button button-type="submit" :disabled="busy">{{
              $t("billing.pay")
            }}</Button>
          </form>
          <Button
            v-if="order.status === 'pending' && order.provider_payment_id"
            type="secondary"
            :disabled="busy"
            @click="verify"
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
      price: "",
      order: null,
      history: [],
      busy: false,
      loading: true,
      error: false,
      submitted: false,
      card: { name: "", number: "", month: "", year: "", cvc: "" },
    };
  },
  async mounted() {
    try {
      const [options, history] = await Promise.all([
        this.$client.get("/billing/checkout/"),
        this.$client.get("/billing/orders/"),
      ]);
      this.options = options.data;
      this.history = history.data;
      this.account = this.options.accounts[0]?.id || "";
      this.price = this.options.prices[0]?.id || "";
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
    async prepare() {
      this.busy = true;
      this.error = false;
      try {
        const { data } = await this.$client.post("/billing/orders/", {
          account: this.account,
          price: this.price,
          seats: 1,
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
        await this.verify(payment.id);
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
.customer-billing li {
  margin-block: 16px;
  overflow-wrap: anywhere;
}
</style>
