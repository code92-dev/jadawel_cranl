# Jadawel configuration

Environment variables introduced or changed by Jadawel. Variables inherited unchanged
from the upstream engine are documented inline in the `x-backend-variables` block of
`docker-compose.yml`.

Keep local overrides in `.env.local` — never commit secrets.

## Locale and direction

Jadawel is Arabic-first: the default locale drives both the UI language and the
`dir="rtl"` attribute on `<html>`. The backend and web-frontend each have their own
variable and the two should always be set together.

| Variable | Description | Default |
|---|---|---|
| `JADAWEL_DEFAULT_LOCALE` | The default locale assigned to newly created users and used as the fallback UI language. Must be one of the codes in `settings.LANGUAGES` (`ar`, `en`, `fr`, `nl`, `de`, `es`, `it`, `pl`, `ko`, `uk`). Set to `en` to bring the stack up in English/LTR. | `ar` |
| `NUXT_DEFAULT_LOCALE` | The web-frontend default UI locale, used before a user-specific language is known (for example on the login and signup screens). Drives `dir="rtl"` on `<html>`. Should mirror `JADAWEL_DEFAULT_LOCALE`; set both to `en` for English/LTR. | `ar` |

> The `BASEROW_` prefix is retained because the underlying engine reads these names
> directly. Renaming the prefix would require touching every deployment recipe and the
> container entrypoints, so it is deliberately left alone.

## Security and rate limiting

| Variable | Description | Default |
|---|---|---|
| `JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER` | Tells Django it sits behind a TLS-terminating proxy. Also switches on `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` and HSTS. Leave it on for any deployment reached over HTTPS; turn it off only for plain-HTTP local work. | `yes` |
| `JADAWEL_NUM_PROXIES` | How many reverse proxies rewrite `X-Forwarded-For` in front of the app. This is what makes per-client rate limiting countable: unset, DRF keys throttles on the whole forwarded header, which the caller controls, so a limit can be bypassed by varying it. | `1` |
| `JADAWEL_SECURE_HSTS_SECONDS` | `Strict-Transport-Security` max-age. Only applied when the proxy header above is enabled. | `31536000` |
| `JADAWEL_SECURE_HSTS_INCLUDE_SUBDOMAINS` | Adds `includeSubDomains` to HSTS. | `true` |
| `JADAWEL_SECURE_HSTS_PRELOAD` | Adds `preload` to HSTS. Do not enable until you intend to submit the domain. | off |
| `JADAWEL_CONTACT_FORM_RATE` | DRF rate for the public contact endpoint, e.g. `5/hour`. An unparseable value is ignored with a warning rather than failing every request. | `5/hour` |
| `JADAWEL_DASHBOARD_AUTH_RATE` | DRF rate for guessing a public dashboard's share password, keyed per link and caller. | `10/hour` |
| `JADAWEL_DASHBOARD_SHARE_TOKEN_HOURS` | How long the token issued after entering a share password stays valid. | `168` |
| `JADAWEL_PAGE_VIEW_EXTERNAL_HOSTS` | Comma-separated CDN origins a Page view may load scripts, styles and fonts from, and only when that view has `allow_external_resources` turned on. Never widens `connect-src`, so a page still cannot send its rows anywhere. See `docs/PAGE_VIEW.md`. | jsDelivr, unpkg, cdnjs, Google Fonts |

### MCP protected fields

These settings are backend-only. Never expose the Redis credential or fingerprint
keyring through Nuxt, API output, logs, or MCP model configuration.

| Variable | Description | Default |
|---|---|---|
| `JADAWEL_MCP_PROTECTION_REDIS_URL` | Dedicated Redis URL for the digest-only 24-hour mask-token vault. Required in production when protected fields are enabled. | — |
| `JADAWEL_MCP_PROTECTION_FINGERPRINT_KEYS` | JSON object mapping short key IDs to base64-encoded 32-byte HMAC keys. Retain previous verification keys for at least 24 hours during rotation. | `{}` |
| `JADAWEL_MCP_PROTECTION_ACTIVE_KEY_ID` | Key ID from the fingerprint keyring used for new mask tokens. | — |
| `JADAWEL_MCP_PROTECTION_ALLOW_SHARED_REDIS` | Allows the vault to fall back to `REDIS_URL`. Use only for tests or local development; keep disabled in production. | `false` |
| `JADAWEL_MCP_PROTECTION_REDIS_MEM_LIMIT` | Container memory limit for the dedicated protection Redis service in Compose. The service itself is capped at 128 MiB with `noeviction`. | `256m` |

## Database backups

Read by `arabase.backup` and the `arabase.tasks.backup_database` Celery task. All of
these must be present in the `x-backend-variables` block of the compose file, or the
backend and `celery-beat` containers never see them and the job silently does nothing.
See `docs/BACKUP_RESTORE.md` for the full procedure.

| Variable | Description | Default |
|---|---|---|
| `JADAWEL_BACKUP_ENABLED` | Master switch. Off means the scheduled task is never registered. | off |
| `JADAWEL_BACKUP_S3_BUCKET` | Destination bucket. Required. | — |
| `JADAWEL_BACKUP_S3_PREFIX` | Key prefix. **Must not be empty**: retention lists and deletes under this prefix, so an empty one means the whole bucket. Validation rejects it. | `postgres/` |
| `JADAWEL_BACKUP_S3_ENDPOINT_URL` | For S3-compatible providers. | AWS |
| `JADAWEL_BACKUP_S3_REGION` | Bucket region. | — |
| `JADAWEL_BACKUP_S3_ACCESS_KEY_ID` | Required. Keep separate from the `AWS_*` user-file credentials — the media bucket is public-read. | — |
| `JADAWEL_BACKUP_S3_SECRET_ACCESS_KEY` | Required. | — |
| `JADAWEL_BACKUP_S3_SSE` | Server-side encryption header, e.g. `AES256`. Empty disables it. | off |
| `JADAWEL_BACKUP_S3_ACL` | Canned ACL sent with each upload. Leave empty: R2 has no object ACLs, and an AWS bucket created since April 2023 rejects the header. An object is private without it. | off |
| `JADAWEL_BACKUP_RETENTION_DAYS` | Age after which a backup is deleted. Only objects named `jadawel-<timestamp>.dump` are ever removed. | `14` |
| `JADAWEL_BACKUP_CRONTAB` | Schedule. Default is 23:00 UTC = 02:00 Riyadh. | `0 23 * * *` |
| `JADAWEL_BACKUP_TIMEOUT_SECONDS` | pg_dump timeout. The Celery soft limit is derived from this. | `3600` |
| `JADAWEL_BACKUP_INCLUDE_MEDIA` | Archive user-uploaded files alongside the dump, stamped with the same timestamp so the two restore together. Defaults on unless `AWS_STORAGE_BUCKET_NAME` is set, in which case the files are already in object storage. | on |

## Resource limits

Every compose service takes a `mem_limit` from an env var so caps can be matched to the
host without editing the compose file: `JADAWEL_BACKEND_MEM_LIMIT` (`1g`),
`JADAWEL_WEB_FRONTEND_MEM_LIMIT` (`768m`), `JADAWEL_CELERY_MEM_LIMIT` (`768m`),
`JADAWEL_CELERY_EXPORT_MEM_LIMIT` (`768m`), `JADAWEL_CELERY_BEAT_MEM_LIMIT` (`384m`),
`JADAWEL_DB_MEM_LIMIT` (`1g`), `JADAWEL_REDIS_MEM_LIMIT` (`256m`),
`JADAWEL_CADDY_MEM_LIMIT` (`192m`), `JADAWEL_FIXER_MEM_LIMIT` (`64m`).

Production frontend images use Nitro's Node cluster preset with
`NITRO_CLUSTER_WORKERS=1` by default. Keep the worker count explicitly bounded in
containers: raising it can improve SSR throughput, but each worker loads a complete
copy of the Nuxt server bundle. The CranL deployment copy explicitly uses `2`; raise it
only after measuring both steady-state memory and p95 document latency.

| Variable | Description | Default |
|---|---|---|
| `JADAWEL_IMPORT_ARCHIVE_MAX_UNCOMPRESSED_SIZE_MB` | Maximum combined expanded size of every entry in a workspace import ZIP. Archives over this limit are rejected before any entry is parsed or extracted. Raise it only when the storage and worker limits can safely handle larger exports. | `1024` |
| `JADAWEL_IMPORT_ARCHIVE_MAX_JSON_SIZE_MB` | Maximum expanded size of an application-data JSON entry. The manifest has a stricter built-in 8 MiB ceiling. | `64` |
| `JADAWEL_FORMULA_RANGE_MAX_ITEMS` | Maximum number of items the `range()` formula function may generate. The same value is exposed to the browser as `NUXT_PUBLIC_JADAWEL_FORMULA_RANGE_MAX_ITEMS`; both sides must stay in sync or the backend rejects a range the frontend accepted (or vice versa). | `10000` |

### General object cache

`JADAWEL_CACHE_TTL_SECONDS` bounds the Redis-backed cache of `Settings`, `User` and
database-token objects. It defaults to `120`, matching upstream 2.3, so a default
deployment answers repeated reads without a query. Mutation paths — saving settings,
changing a user or its profile, and rotating or deleting a token — invalidate the
entry through the receiving signals, so the next read repopulates it.

Set it to `0` to disable the cache entirely; the accessors short-circuit before
touching Redis, which is the behaviour every test run uses. Set a negative value only
to disable and make the intent explicit. If several backend processes share one Redis
the entries are invalidated for all of them; a local-memory cache backend would not
give that guarantee, which is why the invalidation paths are signal-driven rather than
in-process.

| Variable | Description | Default |
|---|---|---|
| `JADAWEL_CACHE_TTL_SECONDS` | Lifetime in seconds of cached `Settings`, `User` and database-token objects. `0` disables the cache. | `120` |

### Development profiling

`JADAWEL_ENABLE_SILK` defaults to `false`, including in the development
compose stack. Set it to `true` only while profiling an isolated request and
turn it off before functional, E2E, or concurrency testing. Silk records each
request and query in the application database and is not a production load
testing tool. `JADAWEL_DANGEROUS_SILKY_ANALYZE_QUERIES` remains a separate,
more dangerous opt-in and must never be enabled during functional testing.

The development compose stack publishes its media-only Caddy service on
`WEB_FRONTEND_PORT` (`4000` by default). Keep `MEDIA_URL` on that same port so
uploaded previews and downloads are exercised in local browser tests.

## Notes

- Anonymous visitors may still be served English if their browser sends
  `Accept-Language: en`, because Nuxt's `detectBrowserLanguage` writes an
  `i18n-language` cookie. Setting `NUXT_DEFAULT_LOCALE` alone does not override that.
- When adding a new backend setting backed by an env var, follow the
  `add-django-config-env-var` skill in `.agents/skills/` and add a row here.
