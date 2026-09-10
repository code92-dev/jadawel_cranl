import { defineNuxtPlugin } from "#app";
import { BillingAdminType } from "./adminTypes";

export default defineNuxtPlugin({
  name: "jadawel-billing",
  dependsOn: ["core"],
  setup(app) {
    app.$registry.register("admin", new BillingAdminType({ app }));
  },
});
