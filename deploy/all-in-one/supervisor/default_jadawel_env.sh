#!/usr/bin/env bash

# Sets up all of the environment variables used by Jadawel all in one with defaults
# or what the user has provided.

set -euo pipefail

# Accept the legacy BASEROW_* names. Deployments still set them, so copy each
# one to its JADAWEL_* spelling before anything below reads it. The new name
# always wins. Mirrors backend/src/jadawel/config/legacy_env.py; remove all
# three once every deployment sets JADAWEL_*.
while IFS='=' read -r legacy _; do
  [[ $legacy == BASEROW_* ]] || continue
  current="JADAWEL_${legacy#BASEROW_}"
  if [[ -z ${!current:-} ]]; then export "$current=${!legacy}"; fi
done < <(env)

export DOCKER_USER=${DOCKER_USER:-jadawel_docker_user}
export DATA_DIR=${DATA_DIR:-/jadawel/data}
export JADAWEL_PLUGIN_DIR=${JADAWEL_PLUGIN_DIR:-$DATA_DIR/plugins}

export JADAWEL_AMOUNT_OF_WORKERS=${JADAWEL_AMOUNT_OF_WORKERS:-1}
export JADAWEL_AMOUNT_OF_GUNICORN_WORKERS=${JADAWEL_AMOUNT_OF_GUNICORN_WORKERS:-3}

export JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER=${JADAWEL_ENABLE_SECURE_PROXY_SSL_HEADER:-}

export PYTHONUNBUFFERED=1
export PYTHONPATH="${PYTHONPATH:-}:/jadawel/backend/src"
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export TMPDIR=${TMPDIR:-/dev/shm}

export DATABASE_PASSWORD="${DATABASE_PASSWORD:-}"
export DATABASE_NAME="${DATABASE_NAME:-jadawel}"
export DATABASE_USER="${DATABASE_USER:-jadawel}"
export DATABASE_HOST="${DATABASE_HOST:-embed}"
export DATABASE_PORT="${DATABASE_PORT:-5432}"
export PGDATA="$DATA_DIR/postgres/"
export EXTRA_POSTGRES_ARGS="${EXTRA_POSTGRES_ARGS:-}"
export DISABLE_EMBEDDED_PSQL="${DISABLE_EMBEDDED_PSQL:-}"
export JADAWEL_RUN_MINIMAL="${JADAWEL_RUN_MINIMAL:-}"

export REDIS_HOST="${REDIS_HOST:-embed}"

export JADAWEL_PUBLIC_URL="${JADAWEL_PUBLIC_URL:-http://localhost}"
export JADAWEL_CADDY_ADDRESSES="${JADAWEL_CADDY_ADDRESSES:-":80"}"
export JADAWEL_CADDY_GLOBAL_CONF="${JADAWEL_CADDY_GLOBAL_CONF:-}"

export PRIVATE_BACKEND_URL='http://localhost:8000'
export JADAWEL_INBOUND_EMAIL_RECEIVER_URL="${JADAWEL_INBOUND_EMAIL_RECEIVER_URL:-http://localhost:${JADAWEL_INBOUND_EMAIL_WEBAPI_PORT:-8880}}"
# The backend runs in this container, so the receiver's web API only needs to
# listen on loopback.
export JADAWEL_INBOUND_EMAIL_WEBAPI_BIND_IP="${JADAWEL_INBOUND_EMAIL_WEBAPI_BIND_IP:-127.0.0.1}"
export PRIVATE_WEB_FRONTEND_URL='http://localhost:3000'
export JADAWEL_BACKEND_BIND_ADDRESS=127.0.0.1
export JADAWEL_WEBFRONTEND_BIND_ADDRESS=127.0.0.1
export JADAWEL_EXTRA_ALLOWED_HOSTS="${JADAWEL_EXTRA_ALLOWED_HOSTS:-}"

export SYNC_TEMPLATES_ON_STARTUP=${SYNC_TEMPLATES_ON_STARTUP:-true}
export JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION=${JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION:-$SYNC_TEMPLATES_ON_STARTUP}
export MIGRATE_ON_STARTUP=${MIGRATE_ON_STARTUP:-true}
export MEDIA_ROOT="$DATA_DIR/media"
export JADAWEL_ICAL_VIEW_MAX_EVENTS=${JADAWEL_ICAL_VIEW_MAX_EVENTS:-}

export JADAWEL_GROUP_STORAGE_USAGE_QUEUE="${JADAWEL_GROUP_STORAGE_USAGE_QUEUE:-}"

if [[ "${JADAWEL_ALL_IN_ONE_DEV_MODE:-}" == "true"  ]]; then
  export JADAWEL_BACKEND_DEBUG="${JADAWEL_BACKEND_DEBUG:-on}"
  DEFAULT_DJANGO_SETTINGS_MODULE='jadawel.config.settings.dev'
  DEFAULT_WEB_FRONTEND_STARTUP_COMMAND='nuxt-dev-no-attach'
  DEFAULT_BACKEND_STARTUP_COMMAND='django-dev-no-attach'
  DEFAULT_CELERY_WORKER_STARTUP_COMMAND='watch-py celery-worker'
  DEFAULT_CELERY_EXPORT_WORKER_STARTUP_COMMAND='watch-py celery-exportworker'
  DEFAULT_CELERY_BEAT_STARTUP_COMMAND='celery-beat'
else
  DEFAULT_DJANGO_SETTINGS_MODULE='jadawel.config.settings.base'
  DEFAULT_WEB_FRONTEND_STARTUP_COMMAND='nuxt-prod'
  DEFAULT_BACKEND_STARTUP_COMMAND='gunicorn'
  DEFAULT_CELERY_WORKER_STARTUP_COMMAND='celery-worker'
  DEFAULT_CELERY_EXPORT_WORKER_STARTUP_COMMAND='celery-exportworker'
  DEFAULT_CELERY_BEAT_STARTUP_COMMAND='celery-beat'
fi

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-$DEFAULT_DJANGO_SETTINGS_MODULE}
export JADAWEL_WEB_FRONTEND_STARTUP_COMMAND="${JADAWEL_WEB_FRONTEND_STARTUP_COMMAND:-$DEFAULT_WEB_FRONTEND_STARTUP_COMMAND}"
export JADAWEL_BACKEND_STARTUP_COMMAND="${JADAWEL_BACKEND_STARTUP_COMMAND:-$DEFAULT_BACKEND_STARTUP_COMMAND}"
export JADAWEL_CELERY_WORKER_STARTUP_COMMAND="${JADAWEL_CELERY_WORKER_STARTUP_COMMAND:-$DEFAULT_CELERY_WORKER_STARTUP_COMMAND}"
export JADAWEL_CELERY_EXPORT_WORKER_STARTUP_COMMAND="${JADAWEL_CELERY_EXPORT_WORKER_STARTUP_COMMAND:-$DEFAULT_CELERY_EXPORT_WORKER_STARTUP_COMMAND}"
export JADAWEL_CELERY_BEAT_STARTUP_COMMAND="${JADAWEL_CELERY_BEAT_STARTUP_COMMAND:-$DEFAULT_CELERY_BEAT_STARTUP_COMMAND}"
export JADAWEL_EMAIL_RECEIVER_STARTUP_COMMAND="${JADAWEL_EMAIL_RECEIVER_STARTUP_COMMAND:-email-receiver}"
export XDG_CONFIG_HOME=/home/$DOCKER_USER/
export HOME=/home/$DOCKER_USER/

# By default we run all other sub-supervisor processes as a non root user. However for
# now we want to default just Caddy to a root user so it can bind to the privileged
# port of 80.
#
# Until the latest version of Docker engine is more available if we want
# Caddy to be able to bind to the privileged port of 80 it must be root. It was fixed
# in 2020 (https://github.com/moby/moby/pull/41030) but we have many users who are
# running older versions (often packaged by other software) who hit this error.
# Even the official Caddy image runs as root currently to get around this problem:
# (https://github.com/caddyserver/caddy-docker/issues/104)
export JADAWEL_CADDY_USER="${JADAWEL_CADDY_USER:-root}"
