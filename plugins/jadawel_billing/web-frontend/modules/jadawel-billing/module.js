import {
  defineNuxtModule,
  addPlugin,
  createResolver,
  extendPages,
} from "nuxt/kit";

export default defineNuxtModule({
  meta: { name: "jadawel-billing" },
  dependsOn: ["core"],
  setup(options, nuxt) {
    const { resolve } = createResolver(import.meta.url);
    addPlugin({ src: resolve("./plugin.js") });
    extendPages((pages) =>
      pages.push(
        {
          name: "customer-billing",
          path: "/billing",
          file: resolve("./pages/billing.vue"),
        },
        {
          name: "admin-billing",
          path: "/admin/billing",
          file: resolve("./pages/admin.vue"),
        },
      ),
    );
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
