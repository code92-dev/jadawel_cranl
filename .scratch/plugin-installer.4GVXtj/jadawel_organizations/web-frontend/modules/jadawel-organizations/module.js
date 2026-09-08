import {
  defineNuxtModule,
  addPlugin,
  createResolver,
  extendPages,
} from "nuxt/kit";

export default defineNuxtModule({
  meta: { name: "jadawel-organizations" },
  // Organization checkout and entitlement state are supplied by Billing.
  // Keep the standalone module's dependency contract explicit so an invalid
  // frontend installation fails during Nuxt setup instead of at runtime.
  dependsOn: ["core", "jadawel-billing"],
  setup(_, nuxt) {
    const { resolve } = createResolver(import.meta.url);
    addPlugin({ src: resolve("./plugin.js") });
    extendPages((pages) => {
      const routes = [
        {
          name: "accept-organization-invitation",
          path: "/organizations/invitations/accept",
          file: resolve("./pages/accept.vue"),
        },
        {
          name: "organizations",
          path: "/organizations",
          file: resolve("./pages/index.vue"),
        },
        {
          name: "organization",
          path: "/organizations/:id",
          file: resolve("./pages/organization.vue"),
        },
        {
          name: "admin-organizations",
          path: "/admin/organizations",
          file: resolve("./pages/admin.vue"),
        },
      ];
      pages.unshift(...routes);
      // The builder contributes a public catch-all. Keep it after optional
      // module routes so authenticated pages cannot be swallowed by it.
      const catchAll = pages.filter((page) => page.path === "/:pathMatch(.*)*");
      const concrete = pages.filter((page) => page.path !== "/:pathMatch(.*)*");
      pages.splice(0, pages.length, ...concrete, ...catchAll);
    });
    nuxt.hook("i18n:registerModule", (register) =>
      register({
        langDir: resolve("./locales"),
        locales: [
          { code: "ar", name: "العربية", file: "ar.json", dir: "rtl" },
          { code: "en", name: "English", file: "en.json", dir: "ltr" },
        ],
      }),
    );
  },
});
