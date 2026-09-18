import {
  defineNuxtModule,
  addPlugin,
  createResolver,
  extendPages,
} from 'nuxt/kit'
import { locales } from '../../config/locales.js'
import { routes } from './routes'

/**
 * Arabase (Jadawel) Nuxt module — the home for our additive frontend code.
 *
 * Kept as a separate module (rather than editing web-frontend/modules/core/*)
 * so upstream merges stay cheap. RTL/Arabic-first behaviour, the `ar` locale,
 * custom field-type components (Hijri date), and enterprise-equivalent UI
 * (SSO / audit / RBAC screens) are wired up here as each phase lands.
 *
 * Direct edits to core components that are unavoidable (e.g. deep RTL work in
 * the grid) are tracked in PATCHES.md, not hidden here.
 */
export default defineNuxtModule({
  meta: {
    name: 'arabase-module',
  },
  dependsOn: ['core'],
  setup(options, nuxt) {
    const { resolve } = createResolver(import.meta.url)

    addPlugin({
      src: resolve('./plugin.js'),
    })

    // Registry registrations (dashboard widgets, service types) live in their own
    // plugin because they must run after the modules whose namespaces they extend.
    addPlugin({
      src: resolve('./registryPlugin.js'),
    })

    // Global RTL / Arabic-first stylesheet. Pushed after core's default.scss
    // (core registers in its own module setup) so it can layer on top. See 1.2.
    nuxt.options.css.push(resolve('./assets/scss/arabase.scss'))
    nuxt.options.css.push(resolve('./assets/scss/dashboard_chart_widget.scss'))
    nuxt.options.css.push(resolve('./assets/scss/widget_board.scss'))
    nuxt.options.css.push(resolve('./assets/scss/admin_backup.scss'))
    nuxt.options.css.push(resolve('./assets/scss/html_page_view.scss'))
    nuxt.options.css.push(resolve('./assets/scss/mcp_protection.scss'))
    nuxt.options.css.push(resolve('./assets/scss/row_coloring.scss'))
    nuxt.options.css.push(resolve('./assets/scss/kanban.scss'))
    nuxt.options.css.push(resolve('./assets/scss/table_access.scss'))

    // Public dashboard share pages. Anonymous routes, so they must live
    // outside the authenticated `app` layout.
    extendPages((pages) => {
      pages.push(...routes)

      // The Table access tab is a child of core's `settings` route, so it
      // renders inside the same tab shell as Members and Invites. Injecting it
      // here keeps core/routes.js untouched.
      //
      // The search has to recurse: `settings` is not a top-level page, it is a
      // child of core's `root` route.
      const findPage = (candidates, name) => {
        for (const page of candidates) {
          if (page.name === name) {
            return page
          }
          const nested = page.children && findPage(page.children, name)
          if (nested) {
            return nested
          }
        }
        return null
      }

      const settings = findPage(pages, 'settings')
      if (settings) {
        settings.children = settings.children || []
        settings.children.push({
          name: 'settings-table-access',
          path: 'table-access',
          file: resolve('./pages/settings/tableAccess.vue'),
        })
      }
    })

    // The `ar` locale itself is activated via config/locales.js (shared list).
    // arabase keeps its own strings here rather than adding keys to an upstream
    // module's locale files, which would conflict on every upstream merge.
    nuxt.hook('i18n:registerModule', (register) => {
      register({
        langDir: resolve('./locales'),
        locales,
      })
    })
  },
})
