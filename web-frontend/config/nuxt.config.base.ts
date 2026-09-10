import path from 'node:path'
import { defineNuxtConfig } from 'nuxt/config'
import svgLoader from 'vite-svg-loader'
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import { locales } from './locales.js'
import pkg from '../package.json'

function jadawelModuleConfig() {
  const additionalModulesCsv = process.env.ADDITIONAL_MODULES
  const additionalModules = additionalModulesCsv
    ? additionalModulesCsv
        .split(',')
        .map((m) => m.trim())
        .filter((m) => m !== '')
    : []

  if (additionalModules.length > 0) {
    console.log(`Loading extra plugin modules: ${additionalModules}`)
  }

  const baseModules = [
    `./modules/core/module.js`,
    `./modules/database/module.js`,
    `./modules/dashboard/module.js`,
    `./modules/builder/module.js`,
    `./modules/automation/module.js`,
    `./modules/integrations/module.js`,
    // Jadawel fork: our additive frontend module (RTL, `ar` locale, custom UI).
    `./modules/arabase/module.js`,
  ]

  const modules = baseModules.concat(additionalModules)

  const zipPkgDir = path.dirname(require.resolve('@zip.js/zip.js/package.json'))
  const zipUmdPath = path.join(zipPkgDir, 'dist/zip.min.js')

  return {
    modules,
    zipUmdPath,
  }
}

const jadawel = jadawelModuleConfig()

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  // Routes are contributed by the core and optional plugin modules. There is
  // intentionally no root pages/ directory, so keep Nuxt's pages subsystem
  // enabled for module-provided routes.
  pages: true,
  alias: {
    '@jadawel': '',
  },
  css: [],
  runtimeConfig: {
    public: {
      version: pkg.version,
    },
  },
  modules: [...jadawel.modules, '@nuxtjs/i18n', '@sentry/nuxt/module'],
  i18n: {
    strategy: 'no_prefix',
    // Jadawel fork: Arabic is the primary locale (RTL). Env-overridable so a deploy
    // can bring the frontend up in English/LTR (set NUXT_DEFAULT_LOCALE=en) to match
    // the backend JADAWEL_DEFAULT_LOCALE during the RTL audit.
    defaultLocale: process.env.NUXT_DEFAULT_LOCALE || 'ar',
    // Jadawel fork: upstream bridges @nuxtjs/i18n's default restructureDir ('i18n')
    // to the real web-frontend/locales/ dir via a filesystem symlink (i18n/locales ->
    // ../locales). That symlink breaks on Windows checkouts (core.symlinks=false),
    // which also breaks the bind-mounted dev server. Point langDir straight at the
    // real dir instead so no symlink is needed on any platform. See PATCHES.md.
    langDir: '../locales',
    locales,
    trailingSlash: true,
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n-language',
      redirectOn: 'root',
    },
    vueI18n: './i18n.config.ts',
  },
  nitro: {
    externals: {
      external: ['vuejs3-datepicker'],
    },
  },
  vite: {
    css: {
      preprocessorOptions: {
        scss: {
          // TODO: Migrate all @import rules to @use/@forward (Dart Sass 3.0 will remove @import).
          //  Also fix global-builtin (unquote → string.unquote in colors.module.scss)
          //  and if-function (old if() syntax in abstracts/_helpers.scss).
          //  See https://sass-lang.com/d/import for the migration guide and automated migrator.
          silenceDeprecations: [
            'import',
            'global-builtin',
            'if-function',
            'color-functions',
          ],
        },
      },
    },
    plugins: [
      nodePolyfills({
        include: ['util'],
        // ✅ prevent "process already declared" in Nitro/Node
        globals: {
          process: false,
          Buffer: false,
          global: false,
        },
      }),
      svgLoader(),
    ],
    ssr: {
      noExternal: ['vue-chartjs', 'chart.js'],
    },
    server: {
      sourcemapIgnoreList: (sourcePath) => sourcePath.includes('node_modules'),
      watch: {
        ignored: [
          '**/node_modules/**',
          '**/.git/**',
          '**/.nuxt/**',
          '**/.claude/**',
        ],
      },
    },
    optimizeDeps: {
      // Pre-bundle moment-guess to avoid missing source map warning
      include: ['moment-guess'],
    },
  },
  buildDir: process.env.NUXT_BUILD_DIR || '.nuxt',
  build: {
    transpile: ['vue-chartjs', 'chart.js'],
    cache: true,
    cacheDirectory: process.env.NUXT_CACHE_DIR || 'node_modules/.cache',
  },
  experimental: {
    appManifest: process.env.NODE_ENV !== 'development',
  },
  vue: {
    compilerOptions: {
      comments: false,
    },
  },
})
