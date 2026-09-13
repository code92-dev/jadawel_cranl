ARG UID="9999"
ARG GID="9999"

ARG BACKEND_IMAGE=jadawel/backend
ARG WEBFRONTEND_IMAGE=jadawel/web-frontend
ARG CADDY_VERSION=2.11.1
# hadolint ignore=DL3006
FROM ${BACKEND_IMAGE} AS backend_image
# hadolint ignore=DL3006
FROM ${WEBFRONTEND_IMAGE} AS web_frontend_image
FROM caddy:${CADDY_VERSION} AS caddy_image

# =============================================================================
# Base - system dependencies (cached independently of source images)
# =============================================================================
FROM python:3.14.6-slim-trixie AS base
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# POSTGRES_VERSION is the *embedded server*. Leave it alone: raising it makes
# the image refuse to start on any existing PGDATA directory that an older
# major initialised, which is a data-loss trap for anyone running the embedded
# database.
#
# POSTGRES_CLIENT_VERSION is pg_dump and pg_restore, and it is deliberately
# separate. The client has to be at least as new as whatever server it talks
# to — pg_dump refuses outright to dump a newer server — and that server is not
# necessarily the embedded one. CranL provides Postgres 16 externally while the
# embedded server here is 15, so a single version cannot satisfy both.
#
# Newer is always safe for the client: pg_dump reads older servers happily, it
# only refuses newer ones. 18 therefore leaves room for the managed database to
# be upgraded without this breaking again.
ENV DOCKER_USER=jadawel_docker_user \
    POSTGRES_VERSION=15 \
    POSTGRES_CLIENT_VERSION=18 \
    JADAWEL_IMAGE_TYPE="all-in-one" \
    DATA_DIR=/jadawel/data \
    JADAWEL_PLUGIN_DIR=/jadawel/data/plugins

# Runtime dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install --no-install-recommends -y \
    curl gnupg2 ca-certificates && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --batch --dearmor -o /usr/share/keyrings/pgdg.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install --no-install-recommends -y \
    supervisor \
    psmisc \
    gawk \
    postgresql-client-"${POSTGRES_CLIENT_VERSION}" \
    xmlsec1 \
    gettext \
    tini \
    tzdata-legacy \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && \
    # Setup user and group with fixed UID/GID for volume permission consistency
    getent group "$GID" || groupadd --system --gid "$GID" "${DOCKER_USER}" && \
    useradd --shell /bin/bash -l -u "$UID" -g "$GID" -o -c "" -d /jadawel -m "${DOCKER_USER}" && \
    chmod 755 /jadawel && \
    # Setup supervisor
    ln -sf /dev/stdout /var/log/supervisor/supervisord.log && \
    # Create data and plugin directories with correct ownership
    mkdir -p "${DATA_DIR}" "${JADAWEL_PLUGIN_DIR}" && \
    chown -R "$UID:$GID" "${DATA_DIR}" "${JADAWEL_PLUGIN_DIR}"

COPY --from=caddy_image /usr/bin/caddy /usr/bin/caddy

# Copy Node.js, npm, and yarn from web-frontend image (avoids insecure curl|bash from NodeSource)
COPY --from=web_frontend_image /usr/local/bin/node /usr/local/bin/node
COPY --from=web_frontend_image /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=web_frontend_image /opt/yarn-v1.22.22 /opt/yarn-v1.22.22
RUN ln -s /opt/yarn-v1.22.22/bin/yarn /usr/local/bin/yarn

# Copy su-exec from backend image (already built with pinned version + SHA256 verification)
COPY --from=backend_image /usr/local/bin/su-exec /usr/local/bin/su-exec

ENV POSTGRES_LOCATION=/etc/postgresql/15/main \
    UV_PROJECT_ENVIRONMENT=/jadawel/venv \
    UV_CACHE_DIR=/tmp/jadawel_uv_cache \
    UV_VERBOSE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/jadawel/venv/bin:$PATH" \
    PYTHONPATH="/jadawel/backend/src" \
    DJANGO_SETTINGS_MODULE='jadawel.config.settings.base' \
    NODE_OPTIONS="--max-old-space-size=4096" \
    NODE_ENV=production


# =============================================================================
# Production Lite - no embedded database/cache (use external services)
# =============================================================================
FROM base AS prod-lite
ARG UID
ARG GID

# Web-frontend
COPY --chown=$UID:$GID --from=web_frontend_image /jadawel/web-frontend /jadawel/web-frontend

# Backend
COPY --chown=$UID:$GID --from=backend_image /jadawel/backend /jadawel/backend
COPY --chown=$UID:$GID --from=backend_image /jadawel/venv /jadawel/venv

# Configuration and startup scripts
COPY ./backend/docker/mime.types /etc/
COPY --chown=$UID:$GID Caddyfile /jadawel/caddy/Caddyfile
COPY --chown=$UID:$GID deploy/all-in-one/supervisor/ /jadawel/supervisor
COPY --chown=$UID:$GID deploy/all-in-one/jadawel.sh /jadawel.sh
COPY --chown=$UID:$GID deploy/plugins/*.sh /jadawel/plugins/

# Backend discovery needs plugin folders as well as the installed Python packages.
# Frontend modules are compiled in the frontend image on the GitHub build runner.
COPY --chown=$UID:$GID plugins/jadawel_billing/backend /jadawel/data/plugins/jadawel_billing/backend
COPY --chown=$UID:$GID plugins/jadawel_organizations/backend /jadawel/data/plugins/jadawel_organizations/backend
RUN mkdir -p /jadawel/container_markers && \
    touch /jadawel/container_markers/jadawel_billing.backend-built \
          /jadawel/container_markers/jadawel_organizations.backend-built && \
    chown -R $UID:$GID /jadawel/container_markers

HEALTHCHECK --interval=60s CMD ["/bin/bash", "/jadawel/backend/docker/docker-entrypoint.sh", "backend-healthcheck"]
ENTRYPOINT ["/jadawel.sh"]
CMD ["start"]
EXPOSE 80


# =============================================================================
# Production - adds embedded PostgreSQL + Redis
# =============================================================================
FROM base AS prod
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install postgres + redis (PGDG repo already added in base stage)
RUN curl -fsSL https://packages.redis.io/gpg | gpg --batch --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb trixie main" > /etc/apt/sources.list.d/redis.list && \
    apt-get update && \
    apt-get install --no-install-recommends -y \
    "postgresql-${POSTGRES_VERSION}" \
    "postgresql-${POSTGRES_VERSION}-pgvector" \
    redis \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && \
    # Setup redis
    usermod -a -G tty redis && \
    sed -i 's/daemonize yes/daemonize no/g' /etc/redis/redis.conf && \
    sed -i 's/daemonize no/daemonize no\nbind 127.0.0.1/g' /etc/redis/redis.conf && \
    sed -i '/^logfile/d' /etc/redis/redis.conf && \
    chown redis:redis /etc/redis/redis.conf

# Web-frontend
COPY --chown=$UID:$GID --from=web_frontend_image /jadawel/web-frontend /jadawel/web-frontend

# Backend
COPY --chown=$UID:$GID --from=backend_image /jadawel/backend /jadawel/backend
COPY --chown=$UID:$GID --from=backend_image /jadawel/venv /jadawel/venv

# Configuration and startup scripts
COPY ./backend/docker/mime.types /etc/
COPY --chown=$UID:$GID Caddyfile /jadawel/caddy/Caddyfile
COPY --chown=$UID:$GID deploy/all-in-one/supervisor/ /jadawel/supervisor
COPY --chown=$UID:$GID deploy/all-in-one/jadawel.sh /jadawel.sh
COPY --chown=$UID:$GID deploy/plugins/*.sh /jadawel/plugins/

HEALTHCHECK --interval=60s CMD ["/bin/bash", "/jadawel/backend/docker/docker-entrypoint.sh", "backend-healthcheck"]
ENTRYPOINT ["/jadawel.sh"]
CMD ["start"]
EXPOSE 80
