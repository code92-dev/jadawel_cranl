import importlib
import json
import os
import re
from datetime import timedelta
from decimal import Decimal
from ipaddress import ip_network
from pathlib import Path
from urllib.parse import urljoin, urlparse

from django.core.exceptions import ImproperlyConfigured

import dj_database_url
from corsheaders.defaults import default_headers

from jadawel.config.legacy_env import apply as _apply_legacy_env
from jadawel.config.settings.utils import (
    Setting,
    crontab,
    get_crontab_from_env,
    read_file,
    set_settings_from_env_if_present,
    str_to_bool,
    try_float,
    try_int,
)
from jadawel.core.telemetry.utils import otel_is_enabled
from jadawel.throttling.types import RateLimit
from jadawel.version import VERSION

# Must run before the first os.getenv below: deployments still set JADAWEL_*.
LEGACY_ENV_NAMES_IN_USE = _apply_legacy_env()

# A comma separated list of feature flags used to enable in-progress or not ready
# features for developers. See docs/development/feature-flags.md for more info.
FEATURE_FLAGS = [
    flag.strip().lower() for flag in os.getenv("FEATURE_FLAGS", "").split(",")
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JADAWEL_PLUGIN_DIR_PATH = Path(os.environ.get("JADAWEL_PLUGIN_DIR", "/jadawel/plugins"))

if JADAWEL_PLUGIN_DIR_PATH.exists():
    JADAWEL_PLUGIN_FOLDERS = [
        file
        for file in JADAWEL_PLUGIN_DIR_PATH.iterdir()
        if file.is_dir() and Path(file, "backend").exists()
    ]
else:
    JADAWEL_PLUGIN_FOLDERS = []

JADAWEL_BACKEND_PLUGIN_NAMES = [d.name for d in JADAWEL_PLUGIN_FOLDERS]
# Jadawel fork: the proprietary premium/ and enterprise/ directories have been
# stripped (see PATCHES.md). There are no built-in plugins; enterprise-equivalent
# features (SSO, audit log, RBAC) are rebuilt from scratch under backend/src/arabase/.
JADAWEL_OSS_ONLY = True
JADAWEL_BUILT_IN_PLUGINS = []

# Previously injected by the (now stripped) enterprise plugin's settings. Core
# jadawel.core.user_sources.handler references it, so it must exist. Value must be
# a divisor of 60 (used as `60 // interval` to batch the user-count update task).
JADAWEL_ENTERPRISE_USER_SOURCE_COUNTING_TASK_INTERVAL_MINUTES = int(
    os.getenv("JADAWEL_ENTERPRISE_USER_SOURCE_COUNTING_TASK_INTERVAL_MINUTES", "10")
)

# SECURITY WARNING: keep the secret key used in production secret!
if "SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("JADAWEL_BACKEND_DEBUG", "off") == "on"

# `localhost` and `127.0.0.1` stay: the container healthcheck calls the app on
# the loopback interface, so dropping them breaks the probe rather than
# tightening anything.
#
# `testserver` is Django's test-client host. It used to be listed for an MCP
# helper that no longer exists (nothing in `src/` references it now), and in
# production it only widens the set of Host headers the app will answer to.
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
if DEBUG or os.getenv("DJANGO_SETTINGS_MODULE", "").endswith((".test", ".dev")):
    ALLOWED_HOSTS.append("testserver")
ALLOWED_HOSTS += os.getenv("JADAWEL_EXTRA_ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    "djcelery_email",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.contrib.migrations",
    "health_check.contrib.redis",
    "health_check.contrib.celery_ping",
    "health_check.contrib.psutil",
    "health_check.contrib.s3boto3_storage",
    "jadawel.core",
    "jadawel.api",
    "jadawel.ws",
    "jadawel.contrib.database",
    "jadawel.contrib.integrations",
    "jadawel.contrib.builder",
    "jadawel.contrib.dashboard",
    "jadawel.contrib.automation",
    *JADAWEL_BUILT_IN_PLUGINS,
    # Jadawel fork: our additive backend code. Sub-apps (arabase.sso, arabase.audit,
    # arabase.rbac, ...) are added here as each phase implements them.
    "arabase",
]


ADDITIONAL_APPS = os.getenv("ADDITIONAL_APPS", "").split(",")
if ADDITIONAL_APPS is not None:
    INSTALLED_APPS += [app.strip() for app in ADDITIONAL_APPS if app.strip() != ""]

if JADAWEL_BACKEND_PLUGIN_NAMES:
    print(f"Loaded backend plugins: {','.join(JADAWEL_BACKEND_PLUGIN_NAMES)}")
    INSTALLED_APPS.extend(JADAWEL_BACKEND_PLUGIN_NAMES)

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "jadawel.core.cache.LocalCacheMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "jadawel.api.user_sources.middleware.AddUserSourceUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "jadawel.middleware.JadawelCustomHttp404Middleware",
    "jadawel.middleware.ClearContextMiddleware",
    "jadawel.middleware.ClearDBStateMiddleware",
]

if otel_is_enabled():
    MIDDLEWARE += ["jadawel.core.telemetry.middleware.JadawelOTELMiddleware"]

ROOT_URLCONF = "jadawel.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "jadawel.config.wsgi.application"
ASGI_APPLICATION = "jadawel.config.asgi.application"


# `ASGI_HTTP_MAX_CONCURRENCY` sets max concurrent asgi requests to be processed by
# the asgi application. It's configurable with `JADAWEL_ASGI_HTTP_MAX_CONCURRENCY`
# env variable.
# The default is None - no concurrency limit
ASGI_HTTP_MAX_CONCURRENCY = (
    int(os.getenv("JADAWEL_ASGI_HTTP_MAX_CONCURRENCY") or 0) or None
)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_USERNAME = os.getenv("REDIS_USER", "")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_PROTOCOL = os.getenv("REDIS_PROTOCOL", "redis")
REDIS_SSL_CERT_REQS = os.getenv("REDIS_SSL_CERT_REQS", "required")
REDIS_SSL_CA_CERTS = os.getenv("REDIS_SSL_CA_CERTS", "")

redis_auth = f"{REDIS_USERNAME}:{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
redis_url_suffix = ""
if REDIS_PROTOCOL == "rediss":
    redis_url_suffix = f"?ssl_cert_reqs={REDIS_SSL_CERT_REQS}"
    if REDIS_SSL_CA_CERTS:
        redis_url_suffix += f"&ssl_ca_certs={REDIS_SSL_CA_CERTS}"

REDIS_URL = os.getenv(
    "REDIS_URL",
    f"{REDIS_PROTOCOL}://{redis_auth}{REDIS_HOST}:{REDIS_PORT}/0{redis_url_suffix}",
)

# Private MCP protected-field storage. A dedicated Redis URL is required in
# production; shared Redis is an explicit development/test-only opt-in.
MCP_PROTECTION_REDIS_URL = os.getenv("JADAWEL_MCP_PROTECTION_REDIS_URL", "")
MCP_PROTECTION_ALLOW_SHARED_REDIS = str_to_bool(
    os.getenv("JADAWEL_MCP_PROTECTION_ALLOW_SHARED_REDIS", "false")
)
MCP_PROTECTION_FINGERPRINT_KEYS = json.loads(
    os.getenv("JADAWEL_MCP_PROTECTION_FINGERPRINT_KEYS", "{}")
)
MCP_PROTECTION_ACTIVE_KEY_ID = os.getenv("JADAWEL_MCP_PROTECTION_ACTIVE_KEY_ID", "")

JADAWEL_GROUP_STORAGE_USAGE_QUEUE = os.getenv(
    "JADAWEL_GROUP_STORAGE_USAGE_QUEUE", "export"
)
JADAWEL_ROLE_USAGE_QUEUE = os.getenv("JADAWEL_GROUP_STORAGE_USAGE_QUEUE", "export")

CELERY_BROKER_URL = REDIS_URL
CELERY_TASK_ROUTES = {
    "jadawel.contrib.database.export.tasks.run_export_job": {"queue": "export"},
    "jadawel.contrib.database.export.tasks.clean_up_old_jobs": {"queue": "export"},
    "jadawel.core.trash.tasks.mark_old_trash_for_permanent_deletion": {
        "queue": "export"
    },
    "jadawel.core.trash.tasks.permanently_delete_marked_trash": {"queue": "export"},
    "jadawel.core.usage.tasks": {"queue": JADAWEL_GROUP_STORAGE_USAGE_QUEUE},
    "jadawel.contrib.database.table.tasks.run_row_count_job": {"queue": "export"},
    "jadawel.core.jobs.tasks.clean_up_jobs": {"queue": "export"},
}
CELERY_TASK_SOFT_TIME_LIMIT = int(
    os.getenv("CELERY_TASK_SOFT_TIME_LIMIT") or 60 * 5
)  # default 5 minutes
CELERY_TASK_TIME_LIMIT = CELERY_TASK_SOFT_TIME_LIMIT + 60  # default 6 minutes

CELERY_REDBEAT_REDIS_URL = REDIS_URL
# Explicitly set the same value as the default loop interval here so we can use it
# later. CELERY_BEAT_MAX_LOOP_INTERVAL < CELERY_REDBEAT_LOCK_TIMEOUT must be kept true
# as otherwise a beat instance will acquire the lock, do scheduling, go to sleep for
# CELERY_BEAT_MAX_LOOP_INTERVAL before waking up where it assumes it still owns the lock
# however if the lock timeout is less than the interval the lock will have been released
# and the beat instance will crash as it attempts to extend the lock which it no longer
# owns.
CELERY_BEAT_MAX_LOOP_INTERVAL = os.getenv("CELERY_BEAT_MAX_LOOP_INTERVAL", 20)
# By default CELERY_REDBEAT_LOCK_TIMEOUT = 5 * CELERY_BEAT_MAX_LOOP_INTERVAL
# Only one beat instance can hold this lock and schedule tasks at any one time.
# This means if one celery-beat instance crashes any other replicas waiting to take over
# will by default wait 25 minutes until the lock times out and they can acquire
# the lock to start scheduling tasks again.
# Instead we just set it to be slightly longer than the loop interval that beat uses.
# This means beat wakes up, checks the schedule and extends the lock every
# CELERY_BEAT_MAX_LOOP_INTERVAL seconds. If it crashes or fails to wake up
# then 80 seconds after the lock was last extended it will be released and a new
# scheduler will acquire the lock and take over.
CELERY_REDBEAT_LOCK_TIMEOUT = os.getenv(
    "CELERY_REDBEAT_LOCK_TIMEOUT", CELERY_BEAT_MAX_LOOP_INTERVAL + 60
)

CELERY_RESULT_BACKEND = REDIS_URL
CELERY_RESULT_EXPIRES = int(
    # default 1 hour
    os.getenv("CELERY_RESULT_EXPIRES") or 3600
)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
if "DATABASE_URL" in os.environ:
    DATABASES = {"default": dj_database_url.parse(os.getenv("DATABASE_URL"))}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DATABASE_NAME", "jadawel"),
            "USER": os.getenv("DATABASE_USER", "jadawel"),
            "PASSWORD": os.getenv("DATABASE_PASSWORD", "jadawel"),
            "HOST": os.getenv("DATABASE_HOST", "db"),
            "PORT": os.getenv("DATABASE_PORT", "5432"),
        }
    }
    if "DATABASE_OPTIONS" in os.environ:
        DATABASES["default"]["OPTIONS"] = json.loads(
            os.getenv("DATABASE_OPTIONS", "{}")
        )

DATABASE_READ_REPLICAS = []

# Loop over all environment variables to extract read only replicas. Multiple nodes can
# be added providing `DATABASE_READ_{n}_URL`, or DATABASE_READ_{n}_NAME, where {n} is
# the key of the read-only instance.
for key, value in os.environ.items():
    if key.startswith("DATABASE_READ_REPLICA_") and key.endswith("_URL"):
        suffix = key[len("DATABASE_READ_REPLICA_") : -len("_URL")]
        db_key = f"read_{suffix}"
        DATABASES[db_key] = dj_database_url.parse(value)
        DATABASE_READ_REPLICAS.append(db_key)
    elif key.startswith("DATABASE_READ_") and key.endswith("_NAME"):
        suffix = key[len("DATABASE_READ_") : -len("_NAME")]
        db_key = f"read_{suffix}"

        DATABASES[db_key] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv(f"DATABASE_READ_{suffix}_NAME"),
            "USER": os.getenv(f"DATABASE_READ_{suffix}_USER"),
            "PASSWORD": os.getenv(f"DATABASE_READ_{suffix}_PASSWORD"),
            "HOST": os.getenv(f"DATABASE_READ_{suffix}_HOST"),
            "PORT": os.getenv(f"DATABASE_READ_{suffix}_PORT"),
        }

        options = os.getenv(f"DATABASE_READ_{suffix}_OPTIONS")
        if options:
            DATABASES[db_key]["OPTIONS"] = json.loads(options)

        DATABASE_READ_REPLICAS.append(db_key)

# Default 0 = new connection per request; each runs a locale-setting query.
# Increase in WSGI to save those round-trips. In ASGI be careful: async tasks
# open their own connections and persistent ones can exhaust the pool.
#
# Deliberately left at 0 here rather than defaulted up: the same settings module
# serves the WSGI backend and the ASGI/Celery processes, so a global default
# would apply it exactly where the warning above says not to. Set
# JADAWEL_CONN_MAX_AGE=60 in the deployment environment instead.
JADAWEL_CONN_MAX_AGE = int(os.getenv("JADAWEL_CONN_MAX_AGE", 0))

# Apply the configured connection reuse timeout consistently to every database.
# Also enable connection health checks by default so Django verifies that a
# connection is still usable before each request/task, which prevents
# "connection already closed" errors when connections are dropped by the server,
# a load balancer, or a connection pooler.
for _db_key in DATABASES:
    DATABASES[_db_key]["CONN_MAX_AGE"] = JADAWEL_CONN_MAX_AGE
    DATABASES[_db_key].setdefault("CONN_HEALTH_CHECKS", True)

DATABASE_ROUTERS = ["jadawel.config.db_routers.ReadReplicaRouter"]


GENERATED_MODEL_CACHE_NAME = "generated-models"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "jadawel-default-cache",
        "VERSION": VERSION,
    },
    GENERATED_MODEL_CACHE_NAME: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": f"jadawel-{GENERATED_MODEL_CACHE_NAME}-cache",
        "VERSION": None,
    },
}

BUILDER_PUBLICLY_USED_PROPERTIES_CACHE_TTL_SECONDS = int(
    # Default TTL is 2 hours
    os.getenv("JADAWEL_BUILDER_PUBLICLY_USED_PROPERTIES_CACHE_TTL_SECONDS")
    or 60 * 10 * 2
)
BUILDER_DISPATCH_ACTION_CACHE_TTL_SECONDS = int(
    # Default TTL is 5 minutes
    os.getenv("JADAWEL_BUILDER_DISPATCH_ACTION_CACHE_TTL_SECONDS") or 300
)


CELERY_SINGLETON_BACKEND_CLASS = (
    "jadawel.celery_singleton_backend.RedisBackendForSingleton"
)

# This flag enable automatic index creation for table views based on sortings.
AUTO_INDEX_VIEW_ENABLED = os.getenv("JADAWEL_AUTO_INDEX_VIEW_ENABLED", "true") == "true"
AUTO_INDEX_LOCK_EXPIRY = os.getenv("JADAWEL_AUTO_INDEX_LOCK_EXPIRY", 60 * 2)

# Should contain the database connection name of the database where the user tables
# are stored. This can be different than the default database because there are not
# going to be any relations between the application schema and the user schema.
USER_TABLE_DATABASE = "default"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "jadawel.core.user.password_validation.MaximumLengthValidator",
    },
]

# We need the `AllowAllUsersModelBackend` in order to respond with a proper error
# message when the user is not active. The only thing it does, is allowing non active
# users to authenticate, but the user still can't obtain or use a JWT token or database
# token because the user needs to be active to use that.
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

# Jadawel fork: Arabic is the primary locale. The default locale for new users
# is env-configurable (JADAWEL_DEFAULT_LOCALE) and defaults to Arabic. New user
# creation reads settings.LANGUAGE_CODE at runtime (see core.user.handler), so
# this is honoured live per deploy without a migration.
LANGUAGE_CODE = os.getenv("JADAWEL_DEFAULT_LOCALE", "ar")

# Jadawel ships Arabic and English only. The upstream project's other
# translations were removed deliberately: they were partial and unreviewed.
# `UserProfile.language` validates against this list (see
# api/user/validators.py) and takes its choices from it, so any change here
# needs a matching migration — and must stay in sync with
# `web-frontend/config/locales.js`.
LANGUAGES = [
    ("ar", "Arabic"),
    ("en", "English"),
]

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Collation that the backend database should
# support in order to make front end and back end
# collations as close as possible to match sorting and
# other operations.
EXPECTED_COLLATION = "en-x-icu"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# How many reverse proxies sit in front of the application. This is what makes
# every DRF throttle countable: with it unset, `BaseThrottle.get_ident` falls
# back to the whole `X-Forwarded-For` string, and because a proxy *appends* to a
# header the client supplied, a caller can mint a fresh bucket per request just
# by varying what they send. Set, DRF counts hops from the right instead, which
# a client cannot influence.
#
# The production stack is Traefik -> Caddy -> gunicorn, but only the hops that
# actually rewrite the header count, so this stays configurable per deployment.
JADAWEL_NUM_PROXIES = int(os.getenv("JADAWEL_NUM_PROXIES", "") or 1)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "jadawel.api.user_sources.authentication.UserSourceJSONWebTokenAuthentication",
        "jadawel.api.authentication.JSONWebTokenAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "jadawel.api.openapi.AutoSchema",
    "NUM_PROXIES": JADAWEL_NUM_PROXIES,
}

# Throttling / rate-limiting — see docs/installation/configuration.md
JADAWEL_MAX_CONCURRENT_USER_REQUESTS = int(
    os.getenv("JADAWEL_MAX_CONCURRENT_USER_REQUESTS", "") or -1
)
JADAWEL_CONCURRENT_USER_REQUESTS_THROTTLE_TIMEOUT = int(
    os.getenv("JADAWEL_CONCURRENT_USER_REQUESTS_THROTTLE_TIMEOUT", 180)
)
JADAWEL_THROTTLE_BLACKLIST_TTL_SECONDS = int(
    os.getenv("JADAWEL_THROTTLE_BLACKLIST_TTL_SECONDS", "") or -1
)
JADAWEL_THROTTLE_IP_ENABLED = str_to_bool(os.getenv("JADAWEL_THROTTLE_IP_ENABLED", ""))

if JADAWEL_MAX_CONCURRENT_USER_REQUESTS > 0:
    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
        "jadawel.throttling.handler.ConcurrentUserRequestsThrottle",
    ]

    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "concurrent_user_requests": JADAWEL_MAX_CONCURRENT_USER_REQUESTS
    }

    if JADAWEL_THROTTLE_BLACKLIST_TTL_SECONDS > 0:
        # Insert after SecurityMiddleware so 429s still get security/CORS headers.
        _security_idx = MIDDLEWARE.index(
            "django.middleware.security.SecurityMiddleware"
        )
        MIDDLEWARE.insert(
            _security_idx + 1,
            "jadawel.throttling.middleware.ThrottleBlacklistMiddleware",
        )

    MIDDLEWARE += [
        "jadawel.throttling.middleware.ConcurrentUserRequestsMiddleware",
    ]

JADAWEL_CACHE_TTL_SECONDS = int(os.getenv("JADAWEL_CACHE_TTL_SECONDS", 0))

PUBLIC_VIEW_AUTHORIZATION_HEADER = "Jadawel-View-Authorization"

CORS_ORIGIN_ALLOW_ALL = True
CLIENT_SESSION_ID_HEADER = "ClientSessionId"
MAX_CLIENT_SESSION_ID_LENGTH = 256

CLIENT_UNDO_REDO_ACTION_GROUP_ID_HEADER = "ClientUndoRedoActionGroupId"
MAX_UNDOABLE_ACTIONS_PER_ACTION_GROUP = 20
WEBSOCKET_ID_HEADER = "WebsocketId"

USER_SOURCE_AUTHENTICATION_HEADER = "UserSourceAuthorization"
IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"

CORS_ALLOW_HEADERS = list(default_headers) + [
    WEBSOCKET_ID_HEADER,
    PUBLIC_VIEW_AUTHORIZATION_HEADER,
    CLIENT_SESSION_ID_HEADER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_HEADER,
    USER_SOURCE_AUTHENTICATION_HEADER,
    IDEMPOTENCY_KEY_HEADER,
]

ACCESS_TOKEN_LIFETIME = timedelta(
    minutes=int(os.getenv("JADAWEL_ACCESS_TOKEN_LIFETIME_MINUTES", 10))  # 10 minutes
)
REFRESH_TOKEN_LIFETIME = timedelta(
    hours=int(os.getenv("JADAWEL_REFRESH_TOKEN_LIFETIME_HOURS", 24 * 7))  # 7 days
)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": ACCESS_TOKEN_LIFETIME,
    "REFRESH_TOKEN_LIFETIME": REFRESH_TOKEN_LIFETIME,
    "AUTH_HEADER_TYPES": ("JWT",),
    # It is recommended that you set JADAWEL_JWT_SIGNING_KEY so it is independent
    # from the Django SECRET_KEY. This will make changing the signing key used for
    # tokens easier in the event that it is compromised.
    "SIGNING_KEY": os.getenv("JADAWEL_JWT_SIGNING_KEY") or os.getenv("SECRET_KEY"),
    "USER_AUTHENTICATION_RULE": lambda user: user is not None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Jadawel API spec",
    "DESCRIPTION": "REST API for Jadawel.",
    "LICENSE": {"name": "MIT"},
    "VERSION": "2.2.2",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Settings"},
        {"name": "User"},
        {"name": "User files"},
        {"name": "Workspaces"},
        {"name": "Workspace invitations"},
        {"name": "Templates"},
        {"name": "Trash"},
        {"name": "Applications"},
        {"name": "Snapshots"},
        {"name": "Jobs"},
        {"name": "Integrations"},
        {"name": "User sources"},
        {"name": "Database tables"},
        {"name": "Database table fields"},
        {"name": "Database table views"},
        {"name": "Database table view filters"},
        {"name": "Database table view sortings"},
        {"name": "Database table view decorations"},
        {"name": "Database table view groupings"},
        {"name": "Database table view export"},
        {"name": "Database table grid view"},
        {"name": "Database table gallery view"},
        {"name": "Database table form view"},
        {"name": "Database table kanban view"},
        {"name": "Database table calendar view"},
        {"name": "Database table rows"},
        {"name": "Database table export"},
        {"name": "Database table webhooks"},
        {"name": "Database tokens"},
        {"name": "Builder pages"},
        {"name": "Builder elements"},
        {"name": "Builder domains"},
        {"name": "Builder public"},
        {"name": "Builder data sources"},
        {"name": "Builder workflow actions"},
        {"name": "Builder theme"},
        {"name": "Admin"},
    ],
    "ENUM_NAME_OVERRIDES": {
        "NumberDecimalPlacesEnum": [
            (0, "1"),
            (1, "1.0"),
            (2, "1.00"),
            (3, "1.000"),
            (4, "1.0000"),
            (5, "1.00000"),
        ],
        "ViewTypesEnum": [
            "grid",
            "gallery",
            "form",
            "kanban",
            "calendar",
        ],
        "FieldTypesEnum": [
            "text",
            "long_text",
            "url",
            "email",
            "number",
            "rating",
            "boolean",
            "date",
            "last_modified",
            "created_on",
            "link_row",
            "file",
            "single_select",
            "multiple_select",
            "phone_number",
            "formula",
            "count",
            "lookup",
            "url",
        ],
        "ViewFilterTypesEnum": [
            "equal",
            "not_equal",
            "filename_contains",
            "has_file_type",
            "files_lower_than",
            "contains",
            "contains_not",
            "length_is_lower_than",
            "higher_than",
            "lower_than",
            "date_equal",
            "date_before",
            "date_after",
            "date_not_equal",
            "date_equals_today",
            "date_equals_days_ago",
            "date_equals_week",
            "date_equals_month",
            "date_equals_day_of_month",
            "date_equals_year",
            "single_select_equal",
            "single_select_not_equal",
            "link_row_has",
            "link_row_has_not",
            "boolean",
            "empty",
            "not_empty",
            "multiple_select_has",
            "multiple_select_has_not",
        ],
        "EventTypesEnum": ["rows.created", "rows.updated", "rows.deleted"],
    },
}

JADAWEL_FILE_UPLOAD_SIZE_LIMIT_MB = int(
    Decimal(os.getenv("JADAWEL_FILE_UPLOAD_SIZE_LIMIT_MB", 1024 * 1024)) * 1024 * 1024
)  # ~1TB by default

IMPORT_ARCHIVE_MAX_UNCOMPRESSED_SIZE_BYTES = int(
    Decimal(os.getenv("JADAWEL_IMPORT_ARCHIVE_MAX_UNCOMPRESSED_SIZE_MB", 1024))
    * 1024
    * 1024
)
IMPORT_ARCHIVE_MAX_JSON_SIZE_BYTES = int(
    Decimal(os.getenv("JADAWEL_IMPORT_ARCHIVE_MAX_JSON_SIZE_MB", 64)) * 1024 * 1024
)

FILE_UPLOAD_ACTIVE_CONTENT_POLICY = os.getenv(
    "JADAWEL_FILE_UPLOAD_ACTIVE_CONTENT_POLICY", "download"
).lower()
if FILE_UPLOAD_ACTIVE_CONTENT_POLICY not in ("download", "block"):
    raise ImproperlyConfigured(
        "JADAWEL_FILE_UPLOAD_ACTIVE_CONTENT_POLICY must be set to "
        "'download' or 'block'."
    )

JADAWEL_OPENAI_UPLOADED_FILE_SIZE_LIMIT_MB = int(
    os.getenv("JADAWEL_OPENAI_UPLOADED_FILE_SIZE_LIMIT_MB", 512)
)

# Allows accessing and setting values on a dictionary like an object. Using this
# we can pass plugin authors and other functions a `settings` object which can modify
# the settings like they expect (settings.SETTING = 'test') etc.


class AttrDict(dict):
    def __getattr__(self, item):
        return super().__getitem__(item)

    def __setattr__(self, item, value):
        globals()[item] = value

    def __setitem__(self, key, value):
        globals()[key] = value


BASE_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

AWS_STORAGE_ENABLED = os.getenv("AWS_STORAGE_BUCKET_NAME", "") != ""
GOOGLE_STORAGE_ENABLED = os.getenv("GS_BUCKET_NAME", "") != ""
AZURE_STORAGE_ENABLED = os.getenv("AZURE_ACCOUNT_NAME", "") != ""

ALL_STORAGE_ENABLED_VARS = [
    AZURE_STORAGE_ENABLED,
    GOOGLE_STORAGE_ENABLED,
    AWS_STORAGE_ENABLED,
]
if sum(ALL_STORAGE_ENABLED_VARS) > 1:
    raise ImproperlyConfigured(
        "You have enabled more than one user file storage backend, please make sure "
        "you set only one of AWS_ACCESS_KEY_ID, GS_BUCKET_NAME and AZURE_ACCOUNT_NAME."
    )

if AWS_STORAGE_ENABLED:
    BASE_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_FILE_OVERWRITE = False
    # This is needed to write the media file in a single call to `files_zip.writestr`
    # as described here: https://github.com/kobotoolbox/kobocat/issues/475
    AWS_S3_FILE_BUFFER_SIZE = JADAWEL_FILE_UPLOAD_SIZE_LIMIT_MB
    set_settings_from_env_if_present(
        AttrDict(vars()),
        [
            "AWS_S3_SESSION_PROFILE",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_STORAGE_BUCKET_NAME",
            Setting(
                "AWS_S3_OBJECT_PARAMETERS",
                parser=json.loads,
                default={
                    "CacheControl": "max-age=86400",
                },
            ),
            Setting("AWS_DEFAULT_ACL", default="public-read"),
            Setting("AWS_QUERYSTRING_AUTH", parser=str_to_bool),
            Setting("AWS_S3_MAX_MEMORY_SIZE", parser=int),
            Setting("AWS_QUERYSTRING_EXPIRE", parser=int),
            "AWS_S3_URL_PROTOCOL",
            "AWS_S3_REGION_NAME",
            "AWS_S3_ENDPOINT_URL",
            "AWS_S3_CUSTOM_DOMAIN",
            "AWS_LOCATION",
            Setting("AWS_IS_GZIPPED", parser=str_to_bool),
            "GZIP_CONTENT_TYPES",
            Setting("AWS_S3_USE_SSL", parser=str_to_bool),
            Setting("AWS_S3_VERIFY", parser=str_to_bool),
            Setting(
                "AWS_SECRET_ACCESS_KEY_FILE_PATH",
                setting_name="AWS_SECRET_ACCESS_KEY",
                parser=read_file,
            ),
            "AWS_S3_ADDRESSING_STYLE",
            Setting("AWS_S3_PROXIES", parser=json.loads),
            "AWS_S3_SIGNATURE_VERSION",
            Setting("AWS_CLOUDFRONT_KEY", parser=lambda s: s.encode("ascii")),
            "AWS_CLOUDFRONT_KEY_ID",
        ],
    )


if GOOGLE_STORAGE_ENABLED:
    from google.oauth2 import service_account

    # See https://django-storages.readthedocs.io/en/latest/backends/gcloud.html for
    # details on what these env variables do

    BASE_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    GS_FILE_OVERWRITE = False
    set_settings_from_env_if_present(
        AttrDict(vars()),
        [
            "GS_BUCKET_NAME",
            "GS_PROJECT_ID",
            Setting("GS_IS_GZIPPED", parser=str_to_bool),
            "GZIP_CONTENT_TYPES",
            Setting("GS_DEFAULT_ACL", default="publicRead"),
            Setting("GS_QUERYSTRING_AUTH", parser=str_to_bool),
            Setting("GS_MAX_MEMORY_SIZE", parser=int),
            Setting("GS_BLOB_CHUNK_SIZE", parser=int),
            Setting("GS_OBJECT_PARAMETERS", parser=json.loads),
            "GS_CUSTOM_ENDPOINT",
            "GS_LOCATION",
            Setting("GS_EXPIRATION", parser=int),
            Setting(
                "GS_CREDENTIALS_FILE_PATH",
                setting_name="GS_CREDENTIALS",
                parser=service_account.Credentials.from_service_account_file,
            ),
        ],
    )

if AZURE_STORAGE_ENABLED:
    BASE_FILE_STORAGE = "storages.backends.azure_storage.AzureStorage"
    AZURE_OVERWRITE_FILES = False
    set_settings_from_env_if_present(
        AttrDict(vars()),
        [
            "AZURE_ACCOUNT_NAME",
            "AZURE_ACCOUNT_KEY",
            Setting(
                "AZURE_ACCOUNT_KEY_FILE_PATH",
                setting_name="AZURE_ACCOUNT_KEY",
                parser=read_file,
            ),
            "AZURE_CONTAINER",
            Setting("AZURE_SSL", parser=str_to_bool),
            Setting("AZURE_UPLOAD_MAX_CONN", parser=int),
            Setting("AZURE_CONNECTION_TIMEOUT_SECS", parser=int),
            Setting("AZURE_URL_EXPIRATION_SECS", parser=int),
            "AZURE_LOCATION",
            "AZURE_ENDPOINT_SUFFIX",
            "AZURE_CUSTOM_DOMAIN",
            "AZURE_CONNECTION_STRING",
            "AZURE_TOKEN_CREDENTIAL",
            "AZURE_CACHE_CONTROL",
            Setting("AZURE_OBJECT_PARAMETERS", parser=json.loads),
            "AZURE_API_VERSION",
        ],
    )

STORAGES = {
    "default": {
        "BACKEND": BASE_FILE_STORAGE,
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

JADAWEL_PUBLIC_URL = os.getenv("JADAWEL_PUBLIC_URL", "")
if JADAWEL_PUBLIC_URL:
    PUBLIC_BACKEND_URL = JADAWEL_PUBLIC_URL
    PUBLIC_WEB_FRONTEND_URL = JADAWEL_PUBLIC_URL
else:
    PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")
    PUBLIC_WEB_FRONTEND_URL = os.getenv(
        "PUBLIC_WEB_FRONTEND_URL", "http://localhost:3000"
    )

JADAWEL_EMBEDDED_SHARE_URL = os.getenv("JADAWEL_EMBEDDED_SHARE_URL")
if not JADAWEL_EMBEDDED_SHARE_URL:
    JADAWEL_EMBEDDED_SHARE_URL = PUBLIC_WEB_FRONTEND_URL

MEDIA_URL_PATH = "/media/"
MEDIA_URL = os.getenv("MEDIA_URL", urljoin(PUBLIC_BACKEND_URL, MEDIA_URL_PATH))

PRIVATE_BACKEND_URL = os.getenv("PRIVATE_BACKEND_URL", "http://backend:8000")
PUBLIC_BACKEND_HOSTNAME = urlparse(PUBLIC_BACKEND_URL).hostname
PUBLIC_WEB_FRONTEND_HOSTNAME = urlparse(PUBLIC_WEB_FRONTEND_URL).hostname
JADAWEL_EMBEDDED_SHARE_HOSTNAME = urlparse(JADAWEL_EMBEDDED_SHARE_URL).hostname
MEDIA_URL_HOSTNAME = urlparse(MEDIA_URL).hostname
PRIVATE_BACKEND_HOSTNAME = urlparse(PRIVATE_BACKEND_URL).hostname

if PUBLIC_BACKEND_HOSTNAME:
    ALLOWED_HOSTS.append(PUBLIC_BACKEND_HOSTNAME)

if MEDIA_URL_HOSTNAME:
    ALLOWED_HOSTS.append(MEDIA_URL_HOSTNAME)

if PRIVATE_BACKEND_HOSTNAME:
    ALLOWED_HOSTS.append(PRIVATE_BACKEND_HOSTNAME)

# Parse JADAWEL_EXTRA_PUBLIC_URLS - comma-separated list of additional public URLs
# where Jadawel will be accessible. It's the same as the `JADAWEL_PUBLIC_URL`, the
# only difference is that the `JADAWEL_PUBLIC_URL` is used in emails.
JADAWEL_EXTRA_PUBLIC_URLS = os.getenv("JADAWEL_EXTRA_PUBLIC_URLS", "")
EXTRA_PUBLIC_BACKEND_HOSTNAMES = []
EXTRA_PUBLIC_WEB_FRONTEND_HOSTNAMES = []

if JADAWEL_EXTRA_PUBLIC_URLS:
    extra_urls = [
        url.strip() for url in JADAWEL_EXTRA_PUBLIC_URLS.split(",") if url.strip()
    ]

    for url in extra_urls:
        # Validate URL format - must start with http:// or https://
        if not url.startswith(("http://", "https://")):
            print(
                f"WARNING: JADAWEL_EXTRA_PUBLIC_URLS contains invalid URL '{url}'. "
                "URLs must start with http:// or https://. Skipping."
            )
            continue

        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if not hostname:
            print(f"WARNING: URL '{url}' has no hostname. Skipping.")
            continue

        if hostname not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(hostname)
        if hostname not in EXTRA_PUBLIC_BACKEND_HOSTNAMES:
            EXTRA_PUBLIC_BACKEND_HOSTNAMES.append(hostname)
        if hostname not in EXTRA_PUBLIC_WEB_FRONTEND_HOSTNAMES:
            EXTRA_PUBLIC_WEB_FRONTEND_HOSTNAMES.append(hostname)

FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@localhost")
RESET_PASSWORD_TOKEN_MAX_AGE = 60 * 60 * 2  # 2 hours
CHANGE_EMAIL_TOKEN_MAX_AGE = 60 * 60 * 12  # 12 hours

ROW_PAGE_SIZE_LIMIT = int(os.getenv("JADAWEL_ROW_PAGE_SIZE_LIMIT", 200))
BATCH_ROWS_SIZE_LIMIT = int(
    os.getenv("BATCH_ROWS_SIZE_LIMIT", 200)
)  # How many rows can be modified at once.

# Maximum count of records considered as a 'small table' during field rule operations.
FIELD_RULE_ROWS_LIMIT = int(os.getenv("FIELD_RULE_ROWS_LIMIT", BATCH_ROWS_SIZE_LIMIT))

# Maximum count of records returned by local jadawel data source
INTEGRATION_LOCAL_JADAWEL_PAGE_SIZE_LIMIT = int(
    os.getenv("JADAWEL_INTEGRATION_LOCAL_JADAWEL_PAGE_SIZE_LIMIT", 200)
)
INTEGRATION_ALLOW_SMTP_SERVICE_TO_USE_INSTANCE_SETTINGS = str_to_bool(
    os.getenv("JADAWEL_INTEGRATION_ALLOW_SMTP_SERVICE_TO_USE_INSTANCE_SETTINGS", "true")
)

AUTOMATION_HISTORY_PAGE_SIZE_LIMIT = int(
    os.getenv("JADAWEL_AUTOMATION_HISTORY_PAGE_SIZE_LIMIT", 100)
)
_legacy_workflow_rate_limit_max_runs = os.getenv(
    "JADAWEL_AUTOMATION_WORKFLOW_RATE_LIMIT_MAX_RUNS"
)
_legacy_workflow_rate_limit_window_seconds = os.getenv(
    "JADAWEL_AUTOMATION_WORKFLOW_RATE_LIMIT_CACHE_EXPIRY_SECONDS"
)
_automation_workflow_rate_limits_env = os.getenv(
    "JADAWEL_AUTOMATION_WORKFLOW_RATE_LIMITS"
)
_automation_workflow_error_limits_env = os.getenv(
    "JADAWEL_AUTOMATION_WORKFLOW_ERROR_LIMITS"
)

if _automation_workflow_rate_limits_env is not None:
    _automation_workflow_rate_limit_values = [
        int(value.strip())
        for value in _automation_workflow_rate_limits_env.split(",")
        if value.strip()
    ]
elif (
    _legacy_workflow_rate_limit_max_runs is not None
    or _legacy_workflow_rate_limit_window_seconds is not None
):
    _automation_workflow_rate_limit_values = [
        int(_legacy_workflow_rate_limit_max_runs or 10),
        int(_legacy_workflow_rate_limit_window_seconds or 5),
    ]
else:
    _automation_workflow_rate_limit_values = [10, 5, 30, 60 * 5, 100, 60 * 60]

if len(_automation_workflow_rate_limit_values) % 2 != 0:
    raise ImproperlyConfigured(
        "JADAWEL_AUTOMATION_WORKFLOW_RATE_LIMITS must contain an even number of "
        "comma-separated integers formatted as max_runs,window_seconds pairs."
    )

AUTOMATION_WORKFLOW_RATE_LIMITS = tuple(
    (
        _automation_workflow_rate_limit_values[index],
        _automation_workflow_rate_limit_values[index + 1],
    )
    for index in range(0, len(_automation_workflow_rate_limit_values), 2)
)
AUTOMATION_WORKFLOW_HISTORY_RATE_LIMIT_CACHE_EXPIRY_SECONDS = int(
    os.getenv(
        "JADAWEL_AUTOMATION_WORKFLOW_HISTORY_RATE_LIMIT_CACHE_EXPIRY_SECONDS",
        _legacy_workflow_rate_limit_window_seconds or 5,
    )
)
if _automation_workflow_error_limits_env is not None:
    _automation_workflow_error_limit_values = [
        int(value.strip())
        for value in _automation_workflow_error_limits_env.split(",")
        if value.strip()
    ]
else:
    _automation_workflow_error_limit_values = [20, 300]

if len(_automation_workflow_error_limit_values) % 2 != 0:
    raise ImproperlyConfigured(
        "JADAWEL_AUTOMATION_WORKFLOW_ERROR_LIMITS must contain an even number of "
        "comma-separated integers formatted as max_errors,window_seconds pairs."
    )

AUTOMATION_WORKFLOW_ERROR_LIMITS = tuple(
    (
        _automation_workflow_error_limit_values[index],
        _automation_workflow_error_limit_values[index + 1],
    )
    for index in range(0, len(_automation_workflow_error_limit_values), 2)
)
AUTOMATION_WORKFLOW_MAX_CONSECUTIVE_ERRORS = int(
    os.getenv("JADAWEL_AUTOMATION_WORKFLOW_MAX_CONSECUTIVE_ERRORS", 5)
)
AUTOMATION_WORKFLOW_TIMEOUT_HOURS = int(
    os.getenv("JADAWEL_AUTOMATION_WORKFLOW_TIMEOUT_HOURS", 24)
)
AUTOMATION_WORKFLOW_HISTORY_MAX_DAYS = int(
    os.getenv("JADAWEL_AUTOMATION_WORKFLOW_HISTORY_MAX_DAYS", 30)
)
AUTOMATION_WORKFLOW_HISTORY_MAX_ENTRIES = int(
    os.getenv("JADAWEL_AUTOMATION_WORKFLOW_HISTORY_MAX_ENTRIES", 200)
)
AUTOMATION_WORKFLOW_HISTORY_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("JADAWEL_AUTOMATION_WORKFLOW_HISTORY_CLEANUP_INTERVAL_MINUTES", 60)
)

TRASH_PAGE_SIZE_LIMIT = 200  # How many trash entries can be requested at once.

# How many unique row values can be requested at once.
JADAWEL_UNIQUE_ROW_VALUES_SIZE_LIMIT = int(
    os.getenv("JADAWEL_UNIQUE_ROW_VALUES_SIZE_LIMIT", 100)
)

# The amount of rows that can be imported when creating a table or data sync.
INITIAL_TABLE_DATA_LIMIT = None
if "INITIAL_TABLE_DATA_LIMIT" in os.environ:
    INITIAL_TABLE_DATA_LIMIT = int(os.getenv("INITIAL_TABLE_DATA_LIMIT"))

JADAWEL_INITIAL_CREATE_SYNC_TABLE_DATA_LIMIT = int(
    os.getenv("JADAWEL_INITIAL_CREATE_SYNC_TABLE_DATA_LIMIT", 5000)
)

MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/jadawel/media")

# Indicates the directory where the user files and user thumbnails are stored.
USER_FILES_DIRECTORY = "user_files"
USER_THUMBNAILS_DIRECTORY = "thumbnails"

EXPORT_FILES_DIRECTORY = "export_files"
EXPORT_CLEANUP_INTERVAL_MINUTES = 5
EXPORT_FILE_EXPIRE_MINUTES = 60

IMPORT_FILES_DIRECTORY = "import_files"

# The interval in minutes that the mentions cleanup job should run. This job will
# remove mentions that are no longer used.
STALE_MENTIONS_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("JADAWEL_STALE_MENTIONS_CLEANUP_INTERVAL_MINUTES", "") or 360
)

# Indicates how frequently the workspace storage should be updated. Once every X number
# of hours.
JADAWEL_UPDATE_WORKSPACE_STORAGE_USAGE_HOURS = 24

ONE_AM_CRONTAB_STR = "0 1 * * *"
JADAWEL_SEAT_USAGE_JOB_CRONTAB = get_crontab_from_env(
    "JADAWEL_SEAT_USAGE_JOB_CRONTAB", default_crontab=ONE_AM_CRONTAB_STR
)

EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"

if os.getenv("EMAIL_SMTP", ""):
    CELERY_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    # EMAIL_SMTP_USE_TLS OR EMAIL_SMTP_USE_TLS for backwards compatibility after
    # fixing #448.
    EMAIL_USE_TLS = bool(os.getenv("EMAIL_SMTP_USE_TLS", "")) or bool(
        os.getenv("EMAIL_SMPT_USE_TLS", "")
    )
    EMAIL_HOST = os.getenv("EMAIL_SMTP_HOST", "localhost")
    EMAIL_PORT = os.getenv("EMAIL_SMTP_PORT", "25")
    EMAIL_HOST_USER = os.getenv("EMAIL_SMTP_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")

    EMAIL_USE_SSL = bool(os.getenv("EMAIL_SMTP_USE_SSL", ""))
    if EMAIL_USE_SSL and EMAIL_USE_TLS:
        raise ImproperlyConfigured(
            "EMAIL_SMTP_USE_SSL and EMAIL_SMTP_USE_TLS are "
            "mutually exclusive and both cannot be set at once."
        )

    EMAIL_SSL_CERTFILE = os.getenv("EMAIL_SMTP_SSL_CERTFILE_PATH", None)
    EMAIL_SSL_KEYFILE = os.getenv("EMAIL_SMTP_SSL_KEYFILE_PATH", None)
else:
    CELERY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Enable email notifications globally. If disabled, tasks will reset the
# email_scheduled field without sending any emails.
EMAIL_NOTIFICATIONS_ENABLED = str_to_bool(
    os.getenv("JADAWEL_EMAIL_NOTIFICATIONS_ENABLED", "true")
)
# The maximum amount of email notifications that can be sent per task. This
# equals the amount of users that will receive an email, since all the
# notifications for a user are sent in one email. If you want to limit the
# number of emails sent per minute, look at MAX_EMAILS_PER_MINUTE.
EMAIL_NOTIFICATIONS_LIMIT_PER_TASK = {
    "instant": int(os.getenv("JADAWEL_EMAIL_NOTIFICATIONS_LIMIT_INSTANT", 50)),
    "daily": int(os.getenv("JADAWEL_EMAIL_NOTIFICATIONS_LIMIT_DAILY", 1000)),
    "weekly": int(os.getenv("JADAWEL_EMAIL_NOTIFICATIONS_LIMIT_WEEKLY", 5000)),
}
# The crontab used to schedule the instant email notifications task.
EMAIL_NOTIFICATIONS_INSTANT_CRONTAB = get_crontab_from_env(
    "JADAWEL_EMAIL_NOTIFICATIONS_INSTANT_CRONTAB", default_crontab="* * * * *"
)
# The hour of the day (between 0 and 23) when the daily and weekly email
# notifications task is scheduled, according to the user timezone. Every hour a
# task is scheduled and only the users in the correct timezone will receive an
# email.
EMAIL_NOTIFICATIONS_DAILY_HOUR_OF_DAY = int(
    os.getenv("JADAWEL_EMAIL_NOTIFICATIONS_DAILY_HOUR_OF_DAY", 0)
)
# The day of the week when the weekly email notifications task is scheduled,
# according to the user timezone (0: Monday, ..., 6: Sunday).
EMAIL_NOTIFICATIONS_WEEKLY_DAY_OF_WEEK = int(
    os.getenv("JADAWEL_EMAIL_NOTIFICATIONS_WEEKLY_DAY_OF_WEEK", 0)
)
# 0 seconds means that the task will not be retried if the limit of users being
# notified is reached. Provide a positive number to enable retries after this many
# seconds.
EMAIL_NOTIFICATIONS_AUTO_RETRY_IF_LIMIT_REACHED_AFTER = (
    int(os.getenv("JADAWEL_EMAIL_NOTIFICATIONS_AUTO_RETRY_IF_LIMIT_REACHED_AFTER", 0))
    or None
)

# The maximum number of notifications that are going to be listed in a single email.
# All the additional notifications are going to be included in a single "and x more"
MAX_NOTIFICATIONS_LISTED_PER_EMAIL = int(
    os.getenv("JADAWEL_MAX_NOTIFICATIONS_LISTED_PER_EMAIL", 10)
)

# Look into `CeleryEmailBackend` for more information about these settings.
CELERY_EMAIL_CHUNK_SIZE = int(os.getenv("CELERY_EMAIL_CHUNK_SIZE", 10))
# Use a multiple of CELERY_EMAIL_CHUNK_SIZE to have a sensible rate limit.
MAX_EMAILS_PER_MINUTE = int(os.getenv("JADAWEL_MAX_EMAILS_PER_MINUTE", 50))
CELERY_EMAIL_TASK_CONFIG = {
    "rate_limit": f"{int(MAX_EMAILS_PER_MINUTE / CELERY_EMAIL_CHUNK_SIZE)}/m",
}

JADAWEL_SEND_VERIFY_EMAIL_RATE_LIMIT = RateLimit.from_string(
    os.getenv("JADAWEL_SEND_VERIFY_EMAIL_RATE_LIMIT", "5/h")
)

login_action_limit_from_env = os.getenv("JADAWEL_LOGIN_ACTION_LOG_LIMIT")
JADAWEL_LOGIN_ACTION_LOG_LIMIT = (
    RateLimit.from_string(login_action_limit_from_env)
    if login_action_limit_from_env
    else RateLimit(period_in_seconds=60 * 5, number_of_calls=1)
)

# Configurable thumbnails that are going to be generated when a user uploads an image
# file.
USER_THUMBNAILS = {"tiny": [None, 21], "small": [48, 48], "card_cover": [300, 160]}

# The directory that contains the all the templates in JSON format. When for example
# the `sync_templates` management command is called, then the templates in the
# database will be synced with these files.
APPLICATION_TEMPLATES_DIR = os.path.join(BASE_DIR, "../../../templates")
# The template that must be selected when the user first opens the templates select
# modal.
# IF CHANGING KEEP IN SYNC WITH e2e-tests/wait-for-services.sh
DEFAULT_APPLICATION_TEMPLATES = ["project-management-en"]
JADAWEL_SYNC_TEMPLATES_PATTERN = os.getenv("JADAWEL_SYNC_TEMPLATES_PATTERN", None)

MAX_FIELD_LIMIT = int(os.getenv("JADAWEL_MAX_FIELD_LIMIT", 600))


# set max events to be returned by every ICal feed. Empty value means no limit.
JADAWEL_ICAL_VIEW_MAX_EVENTS = try_int(
    os.getenv("JADAWEL_ICAL_VIEW_MAX_EVENTS", None), None
)


# If you change this default please also update the default for the web-frontend found
# in web-frontend/modules/core/module.js:55
HOURS_UNTIL_TRASH_PERMANENTLY_DELETED = int(
    os.getenv("HOURS_UNTIL_TRASH_PERMANENTLY_DELETED", 24 * 3)
)
OLD_TRASH_CLEANUP_CHECK_INTERVAL_MINUTES = 5

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# For now force the old os dependant behaviour of file uploads as users might be relying
# on it. See
# https://docs.djangoproject.com/en/3.2/releases/3.0/#new-default-value-for-the-file-upload-permissions-setting
FILE_UPLOAD_PERMISSIONS = None

MAX_FORMULA_STRING_LENGTH = 10000
MAX_FIELD_REFERENCE_DEPTH = 1000
DONT_UPDATE_FORMULAS_AFTER_MIGRATION = bool(
    os.getenv("DONT_UPDATE_FORMULAS_AFTER_MIGRATION", "")
)
EVERY_TEN_MINUTES = "*/10 * * * *"
PERIODIC_FIELD_UPDATE_TIMEOUT_MINUTES = int(
    os.getenv("JADAWEL_PERIODIC_FIELD_UPDATE_TIMEOUT_MINUTES", 9)
)
PERIODIC_FIELD_UPDATE_CRONTAB = get_crontab_from_env(
    "JADAWEL_PERIODIC_FIELD_UPDATE_CRONTAB", default_crontab=EVERY_TEN_MINUTES
)
JADAWEL_PERIODIC_FIELD_UPDATE_UNUSED_WORKSPACE_INTERVAL_MIN = int(
    os.getenv("JADAWEL_PERIODIC_FIELD_UPDATE_UNUSED_WORKSPACE_INTERVAL_MIN", 60)
)
PERIODIC_FIELD_UPDATE_QUEUE_NAME = os.getenv(
    "JADAWEL_PERIODIC_FIELD_UPDATE_QUEUE_NAME", "export"
)

JADAWEL_WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES = int(
    os.getenv("JADAWEL_WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES", 8)
)
JADAWEL_WEBHOOKS_MAX_RETRIES_PER_CALL = int(
    os.getenv("JADAWEL_WEBHOOKS_MAX_RETRIES_PER_CALL", 8)
)
JADAWEL_WEBHOOKS_MAX_PER_TABLE = int(os.getenv("JADAWEL_WEBHOOKS_MAX_PER_TABLE", 20))
JADAWEL_WEBHOOKS_MAX_CALL_LOG_ENTRIES = int(
    os.getenv("JADAWEL_WEBHOOKS_MAX_CALL_LOG_ENTRIES", 10)
)
JADAWEL_WEBHOOKS_REQUEST_TIMEOUT_SECONDS = int(
    os.getenv("JADAWEL_WEBHOOKS_REQUEST_TIMEOUT_SECONDS", 5)
)
JADAWEL_WEBHOOKS_ALLOW_PRIVATE_ADDRESS = bool(
    os.getenv("JADAWEL_WEBHOOKS_ALLOW_PRIVATE_ADDRESS", False)
)
JADAWEL_WEBHOOKS_IP_BLACKLIST = [
    ip_network(ip.strip())
    for ip in os.getenv("JADAWEL_WEBHOOKS_IP_BLACKLIST", "").split(",")
    if ip.strip() != ""
]
JADAWEL_WEBHOOKS_IP_WHITELIST = [
    ip_network(ip.strip())
    for ip in os.getenv("JADAWEL_WEBHOOKS_IP_WHITELIST", "").split(",")
    if ip.strip() != ""
]
JADAWEL_WEBHOOKS_URL_REGEX_BLACKLIST = [
    re.compile(url_regex.strip())
    for url_regex in os.getenv("JADAWEL_WEBHOOKS_URL_REGEX_BLACKLIST", "").split(",")
    if url_regex.strip() != ""
]
JADAWEL_WEBHOOKS_URL_CHECK_TIMEOUT_SECS = int(
    os.getenv("JADAWEL_WEBHOOKS_URL_CHECK_TIMEOUT_SECS", "10")
)
JADAWEL_MAX_WEBHOOK_CALLS_IN_QUEUE_PER_WEBHOOK = (
    int(os.getenv("JADAWEL_MAX_WEBHOOK_CALLS_IN_QUEUE_PER_WEBHOOK", "0")) or None
)
JADAWEL_WEBHOOKS_BATCH_LIMIT = int(os.getenv("JADAWEL_WEBHOOKS_BATCH_LIMIT", 5))
JADAWEL_WEBHOOK_ROWS_ENTER_VIEW_BATCH_SIZE = int(
    os.getenv("JADAWEL_WEBHOOK_ROWS_ENTER_VIEW_BATCH_SIZE", BATCH_ROWS_SIZE_LIMIT)
)

OAUTH_BACKEND_URL = os.getenv("JADAWEL_OAUTH_BACKEND_URL") or PUBLIC_BACKEND_URL

INTEGRATIONS_ALLOW_PRIVATE_ADDRESS = str_to_bool(
    os.getenv("JADAWEL_INTEGRATIONS_ALLOW_PRIVATE_ADDRESS", "false")
)
INTEGRATIONS_PERIODIC_TASK_CRONTAB = crontab(minute="*")
# The minimum amount of minutes the periodic task's "minute" interval
# supports. Self-hosters can run every minute, if they choose to.
INTEGRATIONS_PERIODIC_MINUTE_MIN = int(
    os.getenv("JADAWEL_INTEGRATIONS_PERIODIC_MINUTE_MIN") or 1
)

TOTP_ISSUER_NAME = os.getenv("JADAWEL_TOTP_ISSUER_NAME", "Jadawel")

# ======== WARNING ========
# Please read and understand everything at:
# https://docs.djangoproject.com/en/3.2/ref/settings/#secure-proxy-ssl-header
# before enabling this setting otherwise you can compromise your site’s security.
# This setting will ensure the "next" urls provided by the various paginated API
# endpoints will be returned with https when appropriate.
# If using gunicorn also behind the proxy you might also need to set
# --forwarded-allow-ips='*'. See the following link for more information:
# https://stackoverflow.com/questions/62337379/how-to-append-nginx-ip-to-x-forwarded
# -for-in-kubernetes-nginx-ingress-controller

if bool(os.getenv("JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER", False)):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # Behind a TLS-terminating proxy the transport-security settings below can
    # be turned on, and none of them were set anywhere in the project — they sat
    # at Django's insecure defaults. Caddy's response headers and Traefik's
    # HTTPS redirect mitigate this but do not replace it: a cookie without
    # `Secure` is still sent over plain HTTP if anything ever reaches the app
    # that way.
    #
    # Gated on the same flag rather than on DEBUG, because that flag is the
    # deployment's own statement that it terminates TLS upstream. Turning HSTS
    # on without that is how a development machine locks itself out of http://.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("JADAWEL_SECURE_HSTS_SECONDS", 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = str_to_bool(
        os.getenv("JADAWEL_SECURE_HSTS_INCLUDE_SUBDOMAINS", "true")
    )
    SECURE_HSTS_PRELOAD = str_to_bool(os.getenv("JADAWEL_SECURE_HSTS_PRELOAD", ""))

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True

DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS = bool(
    os.getenv("DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS", "")
)

JADAWEL_BACKEND_LOG_LEVEL = os.getenv("JADAWEL_BACKEND_LOG_LEVEL", "INFO")
JADAWEL_BACKEND_DATABASE_LOG_LEVEL = os.getenv(
    "JADAWEL_BACKEND_DATABASE_LOG_LEVEL", "ERROR"
)

JADAWEL_JOB_EXPIRATION_TIME_LIMIT = int(
    os.getenv("JADAWEL_JOB_EXPIRATION_TIME_LIMIT", 30 * 24 * 60)  # 30 days
)
JADAWEL_JOB_SOFT_TIME_LIMIT = int(
    os.getenv("JADAWEL_JOB_SOFT_TIME_LIMIT", 60 * 30)  # 30 minutes
)
JADAWEL_JOB_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("JADAWEL_JOB_CLEANUP_INTERVAL_MINUTES", 5)  # 5 minutes
)
JADAWEL_ROW_HISTORY_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("JADAWEL_ROW_HISTORY_CLEANUP_INTERVAL_MINUTES", 30)  # 30 minutes
)
JADAWEL_ROW_HISTORY_RETENTION_DAYS = int(
    os.getenv("JADAWEL_ROW_HISTORY_RETENTION_DAYS", 180)
)
JADAWEL_MAX_ROW_REPORT_ERROR_COUNT = int(
    os.getenv("JADAWEL_MAX_ROW_REPORT_ERROR_COUNT", 30)
)
JADAWEL_MAX_SNAPSHOTS_PER_GROUP = int(os.getenv("JADAWEL_MAX_SNAPSHOTS_PER_GROUP", 50))
JADAWEL_SNAPSHOT_EXPIRATION_TIME_DAYS = int(
    os.getenv("JADAWEL_SNAPSHOT_EXPIRATION_TIME_DAYS", 360)  # 360 days
)
JADAWEL_USER_LOG_ENTRY_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("JADAWEL_USER_LOG_ENTRY_CLEANUP_INTERVAL_MINUTES", 60)  # 60 minutes
)
# 61 days to accommodate timezone changes in admin dashboard
JADAWEL_USER_LOG_ENTRY_RETENTION_DAYS = int(
    os.getenv("JADAWEL_USER_LOG_ENTRY_RETENTION_DAYS", 61)
)
JADAWEL_IMPORT_EXPORT_RESOURCE_CLEANUP_INTERVAL_MINUTES = int(
    os.getenv("JADAWEL_IMPORT_EXPORT_RESOURCE_CLEANUP_INTERVAL_MINUTES", 5)
)
JADAWEL_IMPORT_EXPORT_RESOURCE_REMOVAL_AFTER_DAYS = int(
    os.getenv("JADAWEL_IMPORT_EXPORT_RESOURCE_REMOVAL_AFTER_DAYS", 5)
)

# The maximum number of rows that will be exported when exporting a table.
# If `0` then all rows will be exported.
JADAWEL_IMPORT_EXPORT_TABLE_ROWS_COUNT_LIMIT = int(
    os.getenv("JADAWEL_IMPORT_EXPORT_TABLE_ROWS_COUNT_LIMIT", 0)
)

PERMISSION_MANAGERS = [
    "view_ownership",
    "core",
    "setting_operation",
    "staff",
    "allow_if_template",
    "allow_public_builder",
    "element_visibility",
    "member",
    "token",
    "write_field_values",
    "role",
    "basic",
    "automation_workflow",
    "automation_node",
]

if "baserow_enterprise" not in INSTALLED_APPS:
    PERMISSION_MANAGERS.remove("write_field_values")
    PERMISSION_MANAGERS.remove("role")
if "baserow_premium" not in INSTALLED_APPS:
    PERMISSION_MANAGERS.remove("view_ownership")


OLD_ACTION_CLEANUP_INTERVAL_MINUTES = os.getenv(
    "OLD_ACTION_CLEANUP_INTERVAL_MINUTES", 5
)
MINUTES_UNTIL_ACTION_CLEANED_UP = os.getenv("MINUTES_UNTIL_ACTION_CLEANED_UP", "120")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(levelname)s %(asctime)s %(name)s.%(funcName)s:%(lineno)s- %("
            "message)s "
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": JADAWEL_BACKEND_DATABASE_LOG_LEVEL,
            "propagate": True,
        },
        # Default to ERROR to suppress 429 spam under heavy throttling.
        "django.request": {
            "handlers": ["console"],
            "level": os.getenv("JADAWEL_DJANGO_REQUEST_LOG_LEVEL", "ERROR"),
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": JADAWEL_BACKEND_LOG_LEVEL,
    },
}


# Now incorrectly named old variable, previously we would run `sync_templates` prior
# to starting the gunicorn server in Docker. This variable would prevent that from
# happening. Now we sync_templates in an async job triggered after migration.
# This variable if not true will now stop the async job from being triggered.
SYNC_TEMPLATES_ON_STARTUP = os.getenv("SYNC_TEMPLATES_ON_STARTUP", "true") == "true"
JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION = os.getenv(
    "JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION", None
)

if JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION is None:
    # If the new correctly named environment variable is not set, default to using
    # the old now incorrectly named SYNC_TEMPLATES_ON_STARTUP.
    JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION = SYNC_TEMPLATES_ON_STARTUP
else:
    # The new correctly named environment variable is set, so use that instead of
    # the old.
    JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION = (
        JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION == "true"
    )

JADAWEL_SYNC_TEMPLATES_TIME_LIMIT = int(
    os.getenv("JADAWEL_SYNC_TEMPLATES_TIME_LIMIT", 60 * 30)
)

APPEND_SLASH = False

JADAWEL_DISABLE_MODEL_CACHE = bool(os.getenv("JADAWEL_DISABLE_MODEL_CACHE", ""))
JADAWEL_NOWAIT_FOR_LOCKS = not bool(
    os.getenv("JADAWEL_WAIT_INSTEAD_OF_409_CONFLICT_ERROR", False)
)

JADAWEL_PERSONAL_VIEW_LOWEST_ROLE_ALLOWED = (
    os.getenv("JADAWEL_PERSONAL_VIEW_LOWEST_ROLE_ALLOWED", "viewer").strip().upper()
)

LICENSE_AUTHORITY_CHECK_TIMEOUT_SECONDS = 10

MAX_NUMBER_CALENDAR_DAYS = 45

MIGRATION_LOCK_ID = os.getenv("JADAWEL_MIGRATION_LOCK_ID", 123456)
DEFAULT_SEARCH_MODE = os.getenv("JADAWEL_DEFAULT_SEARCH_MODE", "compat")


# Search specific configuration settings.
CELERY_SEARCH_UPDATE_HARD_TIME_LIMIT = int(
    os.getenv("JADAWEL_CELERY_SEARCH_UPDATE_HARD_TIME_LIMIT", 60 * 60)  # 1 hour
)
# By default, Jadawel will use Postgres full-text as its
# search backend. If the product is installed on a system
# with limited disk space, and less accurate results / degraded
# search performance is acceptable, then switch this setting off.
PG_FULLTEXT_SEARCH_ENABLED = str_to_bool(
    (os.getenv("JADAWEL_USE_PG_FULLTEXT_SEARCH", "true"))
)
PG_FULLTEXT_SEARCH_CONFIG = os.getenv("JADAWEL_PG_SEARCH_CONFIG", "simple")
PG_FULLTEXT_SEARCH_UPDATE_DATA_THROTTLE_SECONDS = float(
    os.getenv("JADAWEL_PG_FULLTEXT_SEARCH_UPDATE_DATA_THROTTLE_SECONDS", 2)  # seconds
)

POSTHOG_PROJECT_API_KEY = os.getenv("POSTHOG_PROJECT_API_KEY", "")
POSTHOG_HOST = os.getenv("POSTHOG_HOST") or None
POSTHOG_ENABLED = bool(POSTHOG_PROJECT_API_KEY)

JADAWEL_BUILDER_DOMAINS = os.getenv("JADAWEL_BUILDER_DOMAINS", None)
JADAWEL_BUILDER_DOMAINS = (
    JADAWEL_BUILDER_DOMAINS.split(",") if JADAWEL_BUILDER_DOMAINS is not None else []
)

# Indicates whether we are running the tests or not. Set to True in the test.py settings
# file used by pytest.ini
TESTS = False


for plugin in [*JADAWEL_BUILT_IN_PLUGINS, *JADAWEL_BACKEND_PLUGIN_NAMES]:
    try:
        mod = importlib.import_module(plugin + ".config.settings.settings")
        # The plugin should have a setup function which accepts a 'settings' object.
        # This settings object is an AttrDict shadowing our local variables so the
        # plugin can access the Django settings and modify them prior to startup.
        result = mod.setup(AttrDict(vars()))
    except ImportError as e:
        print("Could not import %s", plugin)
        print(e)


# Libraries that should be lazy-loaded (imported inside functions/methods) to reduce
# memory footprint at startup. If any of these are found in sys.modules during startup,
# a warning will be shown suggesting to either lazy-load them or remove them from this
# list if they're legitimately needed at startup.
JADAWEL_LAZY_LOADED_LIBRARIES = [
    "openai",
    "anthropic",
    "mistralai",
    "ollama",
    "jira2markdown",
    "openpyxl",
    "numpy",
]


SENTRY_BACKEND_DSN = os.getenv("SENTRY_BACKEND_DSN")
SENTRY_DSN = SENTRY_BACKEND_DSN or os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    import sentry_sdk
    import sentry_sdk.integrations as _sentry_integrations
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber

    # Exclude integrations whose module-level imports are incompatible:
    # - pydantic_ai: sentry-sdk patches ToolManager._call_tool which was
    #   removed in pydantic-ai >= 1.x (now execute_tool_call)

    _sentry_integrations._AUTO_ENABLING_INTEGRATIONS[:] = [
        entry
        for entry in _sentry_integrations._AUTO_ENABLING_INTEGRATIONS
        if "pydantic_ai" not in entry
    ]

    SENTRY_DENYLIST = DEFAULT_DENYLIST + ["username", "email", "name"]

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(signals_spans=False, middleware_spans=False)],
        send_default_pii=False,
        event_scrubber=EventScrubber(recursive=True, denylist=SENTRY_DENYLIST),
        environment=os.getenv("SENTRY_ENVIRONMENT", ""),
    )
else:
    JADAWEL_LAZY_LOADED_LIBRARIES.append("sentry_sdk")

JADAWEL_OPENAI_API_KEY = os.getenv("JADAWEL_OPENAI_API_KEY", None)
JADAWEL_OPENAI_ORGANIZATION = os.getenv("JADAWEL_OPENAI_ORGANIZATION", "") or None
JADAWEL_OPENAI_BASE_URL = os.getenv("JADAWEL_OPENAI_BASE_URL", None) or None
JADAWEL_OPENAI_MODELS = os.getenv("JADAWEL_OPENAI_MODELS", "")
JADAWEL_OPENAI_MODELS = (
    JADAWEL_OPENAI_MODELS.split(",") if JADAWEL_OPENAI_MODELS else []
)

JADAWEL_OPENROUTER_API_KEY = os.getenv("JADAWEL_OPENROUTER_API_KEY", None)
JADAWEL_OPENROUTER_ORGANIZATION = (
    os.getenv("JADAWEL_OPENROUTER_ORGANIZATION", "") or None
)
JADAWEL_OPENROUTER_MODELS = os.getenv("JADAWEL_OPENROUTER_MODELS", "")
JADAWEL_OPENROUTER_MODELS = (
    JADAWEL_OPENROUTER_MODELS.split(",") if JADAWEL_OPENROUTER_MODELS else []
)

JADAWEL_ANTHROPIC_API_KEY = os.getenv("JADAWEL_ANTHROPIC_API_KEY", None)
JADAWEL_ANTHROPIC_MODELS = os.getenv("JADAWEL_ANTHROPIC_MODELS", "")
JADAWEL_ANTHROPIC_MODELS = (
    JADAWEL_ANTHROPIC_MODELS.split(",") if JADAWEL_ANTHROPIC_MODELS else []
)

JADAWEL_MISTRAL_API_KEY = os.getenv("JADAWEL_MISTRAL_API_KEY", None)
JADAWEL_MISTRAL_MODELS = os.getenv("JADAWEL_MISTRAL_MODELS", "")
JADAWEL_MISTRAL_MODELS = (
    JADAWEL_MISTRAL_MODELS.split(",") if JADAWEL_MISTRAL_MODELS else []
)

JADAWEL_OLLAMA_HOST = os.getenv("JADAWEL_OLLAMA_HOST", None)
JADAWEL_OLLAMA_MODELS = os.getenv("JADAWEL_OLLAMA_MODELS", "")
JADAWEL_OLLAMA_MODELS = (
    JADAWEL_OLLAMA_MODELS.split(",") if JADAWEL_OLLAMA_MODELS else []
)

JADAWEL_TWO_WAY_SYNC_MAX_CONSECUTIVE_FAILURES = int(
    os.getenv("JADAWEL_TWO_WAY_SYNC_MAX_CONSECUTIVE_FAILURES", "") or 8
)
JADAWEL_TWO_WAY_SYNC_MAX_RETRIES = int(
    os.getenv("JADAWEL_TWO_WAY_SYNC_MAX_RETRIES", "") or 3
)

JADAWEL_PREVENT_POSTGRESQL_DATA_SYNC_CONNECTION_TO_DATABASE = str_to_bool(
    os.getenv("JADAWEL_PREVENT_POSTGRESQL_DATA_SYNC_CONNECTION_TO_DATABASE", "true")
)
JADAWEL_POSTGRESQL_DATA_SYNC_BLACKLIST = os.getenv(
    "JADAWEL_POSTGRESQL_DATA_SYNC_BLACKLIST", ""
)
JADAWEL_POSTGRESQL_DATA_SYNC_BLACKLIST = (
    JADAWEL_POSTGRESQL_DATA_SYNC_BLACKLIST.split(",")
    if JADAWEL_POSTGRESQL_DATA_SYNC_BLACKLIST
    else []
)

# Default compression level for creating zip files. This setting balances the need to
# save resources when compressing media files with the need to save space when
# compressing text files.
JADAWEL_DEFAULT_ZIP_COMPRESS_LEVEL = 5

JADAWEL_MAX_HEALTHY_CELERY_QUEUE_SIZE = int(
    os.getenv("JADAWEL_MAX_HEALTHY_CELERY_QUEUE_SIZE", "") or 10
)

JADAWEL_USE_LOCAL_CACHE = str_to_bool(os.getenv("JADAWEL_USE_LOCAL_CACHE", "true"))

JADAWEL_EMBEDDINGS_API_URL = os.getenv("JADAWEL_EMBEDDINGS_API_URL", "")

# -- CACHALOT SETTINGS --

CACHALOT_TIMEOUT = int(os.getenv("JADAWEL_CACHALOT_TIMEOUT", 60 * 60 * 24 * 7))
JADAWEL_CACHALOT_ONLY_CACHABLE_TABLES = os.getenv(
    "JADAWEL_CACHALOT_ONLY_CACHABLE_TABLES", None
)
JADAWEL_CACHALOT_MODE = os.getenv("JADAWEL_CACHALOT_MODE", "default")
if JADAWEL_CACHALOT_MODE == "full":
    CACHALOT_ONLY_CACHABLE_TABLES = []

elif JADAWEL_CACHALOT_ONLY_CACHABLE_TABLES:
    # Please avoid to add tables with more than 50 modifications per minute to this
    # list, as described here:
    # https://django-cachalot.readthedocs.io/en/latest/limits.html
    CACHALOT_ONLY_CACHABLE_TABLES = JADAWEL_CACHALOT_ONLY_CACHABLE_TABLES.split(",")
else:
    CACHALOT_ONLY_CACHABLE_TABLES = [
        "auth_user",
        "django_content_type",
        "core_settings",
        "core_userprofile",
        "core_application",
        "core_operation",
        "core_template",
        "core_trashentry",
        "core_workspace",
        "core_workspaceuser",
        "core_workspaceuserinvitation",
        "core_authprovidermodel",
        "core_passwordauthprovidermodel",
        "database_database",
        "database_table",
        "database_field",
        "database_fieldependency",
        "database_linkrowfield",
        "database_selectoption",
    ]

# This list will have priority over CACHALOT_ONLY_CACHABLE_TABLES.
JADAWEL_CACHALOT_UNCACHABLE_TABLES = os.getenv(
    "JADAWEL_CACHALOT_UNCACHABLE_TABLES", None
)

if JADAWEL_CACHALOT_UNCACHABLE_TABLES:
    CACHALOT_UNCACHABLE_TABLES = list(
        filter(bool, JADAWEL_CACHALOT_UNCACHABLE_TABLES.split(","))
    )

CACHALOT_ENABLED = str_to_bool(os.getenv("JADAWEL_CACHALOT_ENABLED", ""))
CACHALOT_CACHE = "cachalot"
CACHALOT_UNCACHABLE_TABLES = [
    "django_migrations",
    "core_action",
    "database_token",
]


def install_cachalot():
    from jadawel.cachalot_patch import patch_cachalot_for_jadawel

    global INSTALLED_APPS

    INSTALLED_APPS.append("cachalot")

    patch_cachalot_for_jadawel()


if CACHALOT_ENABLED:
    install_cachalot()

    CACHES[CACHALOT_CACHE] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": f"jadawel-{CACHALOT_CACHE}-cache",
        "VERSION": VERSION,
    }
# -- END CACHALOT SETTINGS --


JADAWEL_DEADLOCK_MAX_RETRIES = max(
    try_int(os.getenv("JADAWEL_DEADLOCK_MAX_RETRIES"), 1),
    1,
)
JADAWEL_DEADLOCK_INITIAL_BACKOFF = max(
    try_float(os.getenv("JADAWEL_DEADLOCK_INITIAL_BACKOFF"), 0.2),
    0.1,
)

# Set to "all" to enable captcha everywhere, or comma-separated contexts like
# "signup,invitations" to enable only in specific places.
JADAWEL_ENABLE_CAPTCHA = os.getenv("JADAWEL_ENABLE_CAPTCHA", "")
JADAWEL_CAPTCHA_PROVIDER = os.getenv("JADAWEL_CAPTCHA_PROVIDER", "cloudflare_turnstile")
JADAWEL_CLOUDFLARE_TURNSTILE_SITE_KEY = os.getenv(
    "JADAWEL_CLOUDFLARE_TURNSTILE_SITE_KEY", ""
)
JADAWEL_CLOUDFLARE_TURNSTILE_SECRET_KEY = os.getenv(
    "JADAWEL_CLOUDFLARE_TURNSTILE_SECRET_KEY", ""
)


# -- JADAWEL FORK SETTINGS --
# The most buckets a dashboard chart will draw. A group by on a high-cardinality
# field (an email or a name) would otherwise ask the browser to render a category
# per row. Buckets past the cap are dropped after sorting, and the dispatch
# result flags that it happened so the widget can say so.
ARABASE_CHART_MAX_BUCKETS = max(
    try_int(os.getenv("ARABASE_CHART_MAX_BUCKETS"), 100),
    1,
)
