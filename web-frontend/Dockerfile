# syntax=docker/dockerfile:1.4
ARG NODE_BASE_IMAGE="node:24.14.0-trixie-slim"
ARG UID="9999"
ARG GID="9999"

# =============================================================================
# Builder for su-exec (replaces gosu, smaller footprint)
# Pinned to v0.2 (commit 212b75144bbc) with SHA256 verification
# =============================================================================
FROM debian:trixie-slim AS tool-builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV SU_EXEC_VERSION=212b75144bbc06722fbd7661f651390dc47a43d1 \
    SU_EXEC_SHA256=d6c40440609a23483f12eb6295b5191e94baf08298a856bab6e15b10c3b82891

# hadolint ignore=DL3008
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl build-essential dos2unix tini && \
    curl -fsSL -o /usr/local/bin/su-exec.c "https://github.com/ncopa/su-exec/raw/${SU_EXEC_VERSION}/su-exec.c" && \
    echo "${SU_EXEC_SHA256}  /usr/local/bin/su-exec.c" | sha256sum -c - && \
    gcc -Wall -Werror -static -o /usr/local/bin/su-exec /usr/local/bin/su-exec.c && \
    chmod 0755 /usr/local/bin/su-exec


# =============================================================================
# CI builder stage
# =============================================================================
FROM ${NODE_BASE_IMAGE} AS builder-ci
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV YARN_CACHE_FOLDER=/tmp/.yarn-cache

RUN mkdir -p /jadawel/web-frontend && \
    chown -R $UID:$GID /jadawel

USER $UID:$GID
WORKDIR /jadawel/web-frontend

# Install dependencies (including dev)
RUN --mount=type=cache,target=$YARN_CACHE_FOLDER,uid=$UID,gid=$GID,sharing=locked \
    --mount=type=bind,source=web-frontend/package.json,target=/jadawel/web-frontend/package.json \
    --mount=type=bind,source=web-frontend/yarn.lock,target=/jadawel/web-frontend/yarn.lock \
    --mount=type=bind,source=web-frontend/scripts/patch-datepicker-locale.mjs,target=/jadawel/web-frontend/scripts/patch-datepicker-locale.mjs \
    yarn install --pure-lockfile --cache-folder $YARN_CACHE_FOLDER


# =============================================================================
# Production builder stage
# =============================================================================
FROM ${NODE_BASE_IMAGE} AS builder-prod
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV YARN_CACHE_FOLDER=/tmp/.yarn-cache \
    NUXT_TELEMETRY_DISABLED=1 \
    NODE_OPTIONS="--max-old-space-size=4096" \
    NODE_ENV=production

RUN mkdir -p /jadawel/web-frontend && \
    chown -R $UID:$GID /jadawel/

# Copy source code
COPY --chown=$UID:$GID ./web-frontend /jadawel/web-frontend/
COPY --chown=$UID:$GID plugins/jadawel_billing/web-frontend /jadawel/web-frontend/bundled-plugins/jadawel_billing/
COPY --chown=$UID:$GID plugins/jadawel_organizations/web-frontend /jadawel/web-frontend/bundled-plugins/jadawel_organizations/
ENV ADDITIONAL_MODULES=/jadawel/web-frontend/bundled-plugins/jadawel_billing/modules/jadawel-billing/module.js,/jadawel/web-frontend/bundled-plugins/jadawel_organizations/modules/jadawel-organizations/module.js

# Copy all dependencies so we can build the production files
COPY --chown=$UID:$GID --from=builder-ci /jadawel/web-frontend/node_modules /jadawel/web-frontend/node_modules

COPY --from=tool-builder /usr/bin/dos2unix /usr/local/bin/dos2unix
RUN dos2unix /jadawel/web-frontend/docker/docker-entrypoint.sh \
    && chmod a+x /jadawel/web-frontend/docker/docker-entrypoint.sh \
    && chown $UID:$GID /jadawel/web-frontend/docker/docker-entrypoint.sh

USER $UID:$GID
WORKDIR /jadawel/web-frontend

# Build, then clean reinstall production only
RUN --mount=type=cache,target=$YARN_CACHE_FOLDER,uid=$UID,gid=$GID,sharing=locked \
    yarn run build


# =============================================================================
# Busybox helper stage for wget binary
# =============================================================================
FROM busybox:musl AS busybox-helper

# =============================================================================
# CI target - used in CI pipelines
# =============================================================================
FROM ${NODE_BASE_IMAGE} AS ci
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Upgrade OS packages to patch CVEs in base image
RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV DOCKER_USER=jadawel_docker_user \
    APP_ENV=test \
    JADAWEL_IMAGE_TYPE="web-frontend"

RUN groupadd --system --gid $GID ${DOCKER_USER} && \
    useradd --shell /bin/bash -l -u $UID -g $GID -o -c "" -d /jadawel -m ${DOCKER_USER} && \
    chmod 755 /jadawel

COPY --from=tool-builder /usr/local/bin/su-exec /usr/local/bin/su-exec
COPY --from=tool-builder /usr/bin/tini /usr/bin/tini
COPY --from=busybox-helper /bin/wget /usr/local/bin/wget

RUN mkdir -p /jadawel/reports /jadawel/.cache /jadawel/.yarn && \
    chown -R $UID:$GID /jadawel

# Copy dependencies and source code
COPY --chown=$UID:$GID ./eslint.config.mjs /jadawel/eslint.config.mjs
COPY --chown=$UID:$GID web-frontend /jadawel/web-frontend

COPY --chown=$UID:$GID --from=builder-ci /jadawel/web-frontend/node_modules /jadawel/web-frontend/node_modules
COPY --chown=$UID:$GID --from=builder-prod /jadawel/web-frontend/.nuxt /jadawel/web-frontend/.nuxt
COPY --chown=$UID:$GID --from=builder-prod /jadawel/web-frontend/.output /jadawel/web-frontend/.output

# Create cache directories (after COPY so they don't get overwritten)
RUN mkdir -p /jadawel/web-frontend/.cache /jadawel/web-frontend/reports/coverage \
    && chown -R $UID:$GID /jadawel/web-frontend/.cache /jadawel/web-frontend/reports

COPY --chown=$UID:$GID tests /jadawel/tests
COPY --chown=$UID:$GID deploy/plugins/*.sh /jadawel/plugins/

USER $UID:$GID
WORKDIR /jadawel/web-frontend

ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/jadawel/web-frontend/docker/docker-entrypoint.sh"]
HEALTHCHECK --interval=60s CMD wget -q -O /dev/null http://localhost:3000/_health/ || exit 1

CMD ["nuxt-prod"]


# =============================================================================
# Development target - used for local development with live reload
# =============================================================================
FROM ${NODE_BASE_IMAGE} AS dev
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-pip \
    build-essential \
    curl \
    wget \
    tmux \
    vim \
    lsof \
    procps \
    sudo

ENV DOCKER_USER=jadawel_docker_user \
    JADAWEL_IMAGE_TYPE="web-frontend" \
    PATH="/jadawel/web-frontend/node_modules/.bin:$PATH" \
    YARN_CACHE_FOLDER=/tmp/.yarn-dev-cache

# Install rust-just for running justfiles
RUN pip3 install --break-system-packages --no-cache-dir rust-just==1.43.1

COPY --from=tool-builder /usr/local/bin/su-exec /usr/local/bin/su-exec
COPY --from=tool-builder /usr/bin/tini /usr/bin/tini
COPY --from=tool-builder /usr/bin/dos2unix /usr/local/bin/dos2unix

RUN getent group $GID || groupadd --system --gid $GID ${DOCKER_USER} && \
    useradd --shell /bin/bash -l -u $UID -g $GID -o -c "" -d /jadawel -m ${DOCKER_USER} && \
    chmod 755 /jadawel && \
    echo "${DOCKER_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${DOCKER_USER} && \
    chmod 0440 /etc/sudoers.d/${DOCKER_USER}

RUN mkdir -p /jadawel/web-frontend && \
    chown -R $UID:$GID /jadawel

USER $UID:$GID
WORKDIR /jadawel/web-frontend

# Configure tmux to preserve environment variables (don't start login shell)
RUN echo "set -g default-command \"\${SHELL}\"" > /jadawel/.tmux.conf && \
    printf '%s\n' \
    '# Aliases' \
    'alias j="just"' \
    'alias y="yarn"' \
    '' \
    '# Show a helpful message' \
    'echo "Jadawel frontend dev container"' \
    'echo "  y <cmd>  - Run yarn commands"' \
    'echo "  j        - See available commands"' \
    > /jadawel/.bashrc

COPY ./eslint.config.mjs /jadawel/eslint.config.mjs
COPY --chown=$UID:$GID web-frontend/docker/docker-entrypoint.sh /jadawel/web-frontend/docker/docker-entrypoint.sh

RUN dos2unix /jadawel/web-frontend/docker/docker-entrypoint.sh \
    && chmod a+x /jadawel/web-frontend/docker/docker-entrypoint.sh

COPY --chown=$UID:$GID web-frontend/package.json /jadawel/web-frontend/package.json
COPY --chown=$UID:$GID web-frontend/scripts/patch-datepicker-locale.mjs /jadawel/web-frontend/scripts/patch-datepicker-locale.mjs

# Make sure these directories exist and are owned by the non-root user
RUN mkdir -p /jadawel/web-frontend/.nuxt /jadawel/web-frontend/.cache /jadawel/web-frontend/.nuxt-storybook /jadawel/web-frontend/.output

# Install dependencies (including dev)
RUN --mount=type=cache,target=$YARN_CACHE_FOLDER,uid=$UID,gid=$GID,sharing=locked \
    yarn install --pure-lockfile --cache-folder $YARN_CACHE_FOLDER

ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/jadawel/web-frontend/docker/docker-entrypoint.sh"]
HEALTHCHECK --interval=60s CMD wget -q -O /dev/null http://localhost:3000/_health/ || exit 1
CMD ["nuxt-dev"]


# =============================================================================
# Production target - minimal image with only runtime requirements
# =============================================================================
FROM ${NODE_BASE_IMAGE} AS local
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DOCKER_USER=jadawel_docker_user \
    JADAWEL_IMAGE_TYPE="web-frontend" \
    NODE_ENV=production \
    YARN_CACHE_FOLDER=/tmp/.yarn-cache

COPY --from=tool-builder /usr/bin/dos2unix /usr/local/bin/dos2unix
COPY --from=tool-builder /usr/local/bin/su-exec /usr/local/bin/su-exec
COPY --from=tool-builder /usr/bin/tini /usr/bin/tini
COPY --from=busybox-helper /bin/wget /usr/local/bin/wget

# Upgrade OS packages to patch CVEs in base image
RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Remove npm (not needed at runtime) to eliminate CVEs in its bundled deps (minimatch, glob, etc.)
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

RUN groupadd --system --gid $GID ${DOCKER_USER} && \
    useradd --shell /bin/bash -l -u $UID -g $GID -o -c "" -d /jadawel -m ${DOCKER_USER} && \
    chmod 755 /jadawel

USER $UID:$GID
RUN mkdir -p /jadawel/web-frontend/docker

COPY --chown=$UID:$GID --from=builder-prod /jadawel/web-frontend/.output /jadawel/web-frontend/.output
COPY --chown=$UID:$GID ./web-frontend/env-remap.mjs /jadawel/web-frontend/env-remap.mjs
COPY --chown=$UID:$GID ./web-frontend/docker/docker-entrypoint-prod.sh /jadawel/web-frontend/docker/docker-entrypoint.sh
RUN chmod a+x /jadawel/web-frontend/docker/docker-entrypoint.sh

HEALTHCHECK --interval=10s CMD wget -q -O /dev/null http://localhost:3000/_health/ || exit 1

WORKDIR /jadawel/web-frontend
ENTRYPOINT ["/jadawel/web-frontend/docker/docker-entrypoint.sh"]


FROM local AS prod
