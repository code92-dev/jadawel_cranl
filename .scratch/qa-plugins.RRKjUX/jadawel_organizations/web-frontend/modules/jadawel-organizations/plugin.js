import { defineNuxtPlugin } from "#app";

import { OrganizationsAdminType } from "./adminTypes";

export default defineNuxtPlugin({
  name: "jadawel-organizations",
  dependsOn: ["core"],
  setup(app) {
    app.$registry.register("admin", new OrganizationsAdminType({ app }));
  },
});
