/**
 * Environment variable remapping for Nuxt 4 runtime config.
 * Remaps legacy env vars to NUXT_ prefixed vars for runtime config support.
 *
 * This allows existing environment variable names (e.g., PUBLIC_BACKEND_URL)
 * to work with Nuxt 4's runtime config system, which expects NUXT_PUBLIC_*
 * prefixed variables for runtime overrides.
 *
 * Import this file before starting Nuxt (dev or prod).
 */

// The production Nitro build uses its node-cluster preset. Never accept the
// preset's unbounded CPU-count default in containers, where the visible host
// CPU count can be much larger than the app's memory allocation. Keep the
// portable image at one worker; resource-aware deployments such as CranL and
// the production load gate opt into two explicitly.
process.env.NITRO_CLUSTER_WORKERS ||= '1'

// Accept the legacy BASEROW_* names. Deployments still set them, so copy each
// one to its JADAWEL_* spelling before anything below reads it. The new name
// always wins. Mirrors backend/src/jadawel/config/legacy_env.py; remove both
// once every deployment sets JADAWEL_*.
for (const [legacy, value] of Object.entries(process.env)) {
  if (!legacy.startsWith('BASEROW_')) continue
  const current = `JADAWEL_${legacy.slice('BASEROW_'.length)}`
  if (process.env[current] === undefined) process.env[current] = value
}

// Mapping: legacy env var -> NUXT runtime config env var
const envMapping = {
  // Private config (server-only)
  PRIVATE_BACKEND_URL: 'NUXT_PRIVATE_BACKEND_URL',

  // Public config (available on client via SSR)
  PUBLIC_BACKEND_URL: 'NUXT_PUBLIC_PUBLIC_BACKEND_URL',
  PUBLIC_WEB_FRONTEND_URL: 'NUXT_PUBLIC_PUBLIC_WEB_FRONTEND_URL',
  DOWNLOAD_FILE_VIA_XHR: 'NUXT_PUBLIC_DOWNLOAD_FILE_VIA_XHR',
  JADAWEL_DISABLE_PUBLIC_URL_CHECK:
    'NUXT_PUBLIC_JADAWEL_DISABLE_PUBLIC_URL_CHECK',
  INITIAL_TABLE_DATA_LIMIT: 'NUXT_PUBLIC_INITIAL_TABLE_DATA_LIMIT',
  HOURS_UNTIL_TRASH_PERMANENTLY_DELETED:
    'NUXT_PUBLIC_HOURS_UNTIL_TRASH_PERMANENTLY_DELETED',
  DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS:
    'NUXT_PUBLIC_DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS',
  JADAWEL_MAX_IMPORT_FILE_SIZE_MB:
    'NUXT_PUBLIC_JADAWEL_MAX_IMPORT_FILE_SIZE_MB',
  FEATURE_FLAGS: 'NUXT_PUBLIC_FEATURE_FLAGS',
  JADAWEL_DISABLE_GOOGLE_DOCS_FILE_PREVIEW:
    'NUXT_PUBLIC_JADAWEL_DISABLE_GOOGLE_DOCS_FILE_PREVIEW',
  JADAWEL_MAX_SNAPSHOTS_PER_GROUP:
    'NUXT_PUBLIC_JADAWEL_MAX_SNAPSHOTS_PER_GROUP',
  JADAWEL_FRONTEND_SAME_SITE_COOKIE:
    'NUXT_PUBLIC_JADAWEL_FRONTEND_SAME_SITE_COOKIE',
  JADAWEL_FRONTEND_JOBS_POLLING_TIMEOUT_MS:
    'NUXT_PUBLIC_JADAWEL_FRONTEND_JOBS_POLLING_TIMEOUT_MS',
  POSTHOG_PROJECT_API_KEY: 'NUXT_PUBLIC_POSTHOG_PROJECT_API_KEY',
  POSTHOG_HOST: 'NUXT_PUBLIC_POSTHOG_HOST',
  JADAWEL_USE_PG_FULLTEXT_SEARCH: 'NUXT_PUBLIC_JADAWEL_USE_PG_FULLTEXT_SEARCH',
  JADAWEL_INTEGRATION_LOCAL_JADAWEL_PAGE_SIZE_LIMIT:
    'NUXT_PUBLIC_INTEGRATION_LOCAL_JADAWEL_PAGE_SIZE_LIMIT',
  JADAWEL_FORMULA_RANGE_MAX_ITEMS:
    'NUXT_PUBLIC_JADAWEL_FORMULA_RANGE_MAX_ITEMS',
  JADAWEL_ROW_PAGE_SIZE_LIMIT: 'NUXT_PUBLIC_JADAWEL_ROW_PAGE_SIZE_LIMIT',
  JADAWEL_UNIQUE_ROW_VALUES_SIZE_LIMIT:
    'NUXT_PUBLIC_JADAWEL_UNIQUE_ROW_VALUES_SIZE_LIMIT',
  JADAWEL_DISABLE_SUPPORT: 'NUXT_PUBLIC_JADAWEL_DISABLE_SUPPORT',
  JADAWEL_INTEGRATIONS_PERIODIC_MINUTE_MIN:
    'NUXT_PUBLIC_JADAWEL_INTEGRATIONS_PERIODIC_MINUTE_MIN',
  // TODO find a way to load these vars from private folders
  JADAWEL_PREMIUM_GROUPED_AGGREGATE_SERVICE_MAX_SERIES:
    'NUXT_PUBLIC_JADAWEL_PREMIUM_GROUPED_AGGREGATE_SERVICE_MAX_SERIES',
  JADAWEL_PRICING_URL: 'NUXT_PUBLIC_JADAWEL_PRICING_URL',
  JADAWEL_ENTERPRISE_ASSISTANT_LLM_MODEL:
    'NUXT_PUBLIC_JADAWEL_ENTERPRISE_ASSISTANT_LLM_MODEL',
  SENTRY_DSN: 'NUXT_PUBLIC_SENTRY_DSN',
  SENTRY_ENVIRONMENT: 'NUXT_PUBLIC_SENTRY_ENVIRONMENT',
  MEDIA_URL: 'NUXT_PUBLIC_MEDIA_URL',
  JADAWEL_EXTRA_CLIENT_SCRIPT_URLS:
    'NUXT_PUBLIC_JADAWEL_EXTRA_CLIENT_SCRIPT_URLS',
}

// Remap env vars: only if legacy var exists AND NUXT_ var is not already set
for (const [legacyKey, nuxtKey] of Object.entries(envMapping)) {
  if (
    process.env[legacyKey] !== undefined &&
    process.env[nuxtKey] === undefined
  ) {
    process.env[nuxtKey] = process.env[legacyKey]
  }
}

// Handle JADAWEL_PUBLIC_URL convenience variable (sets both backend and frontend URLs)
if (process.env.JADAWEL_PUBLIC_URL) {
  if (!process.env.NUXT_PUBLIC_PUBLIC_BACKEND_URL) {
    process.env.NUXT_PUBLIC_PUBLIC_BACKEND_URL = process.env.JADAWEL_PUBLIC_URL
  }
  if (!process.env.NUXT_PUBLIC_PUBLIC_WEB_FRONTEND_URL) {
    process.env.NUXT_PUBLIC_PUBLIC_WEB_FRONTEND_URL =
      process.env.JADAWEL_PUBLIC_URL
  }
}

// Handle JADAWEL_EMBEDDED_SHARE_URL fallback to PUBLIC_WEB_FRONTEND_URL
if (!process.env.NUXT_PUBLIC_JADAWEL_EMBEDDED_SHARE_URL) {
  if (process.env.JADAWEL_EMBEDDED_SHARE_URL) {
    process.env.NUXT_PUBLIC_JADAWEL_EMBEDDED_SHARE_URL =
      process.env.JADAWEL_EMBEDDED_SHARE_URL
  } else if (process.env.NUXT_PUBLIC_PUBLIC_WEB_FRONTEND_URL) {
    // Use the already-remapped variable (PUBLIC_WEB_FRONTEND_URL -> NUXT_PUBLIC_PUBLIC_WEB_FRONTEND_URL)
    process.env.NUXT_PUBLIC_JADAWEL_EMBEDDED_SHARE_URL =
      process.env.NUXT_PUBLIC_PUBLIC_WEB_FRONTEND_URL
  }
}

// Handle JADAWEL_EXTRA_PUBLIC_URLS with hostname extraction transformation
if (
  process.env.JADAWEL_EXTRA_PUBLIC_URLS &&
  !process.env.NUXT_PUBLIC_EXTRA_PUBLIC_WEB_FRONTEND_HOSTNAMES
) {
  // Inline parseHostnamesFromUrls to avoid importing from source files
  // (source files are not copied to production Docker images)
  const hostnames = process.env.JADAWEL_EXTRA_PUBLIC_URLS.split(',')
    .map((url) => url.trim())
    .filter((url) => url !== '')
    .map((url) => {
      try {
        return new URL(url).hostname
      } catch (e) {
        console.warn(`Invalid URL in JADAWEL_EXTRA_PUBLIC_URLS: ${url}`)
        return null
      }
    })
    .filter((hostname) => hostname !== null)
  process.env.NUXT_PUBLIC_EXTRA_PUBLIC_WEB_FRONTEND_HOSTNAMES =
    JSON.stringify(hostnames)
}

// Handle JADAWEL_BUILDER_DOMAINS with comma-split transformation
if (
  process.env.JADAWEL_BUILDER_DOMAINS &&
  !process.env.NUXT_PUBLIC_JADAWEL_BUILDER_DOMAINS
) {
  const domains = process.env.JADAWEL_BUILDER_DOMAINS.split(',')
    .map((d) => d.trim())
    .filter((d) => d !== '')
  process.env.NUXT_PUBLIC_JADAWEL_BUILDER_DOMAINS = JSON.stringify(domains)
}
