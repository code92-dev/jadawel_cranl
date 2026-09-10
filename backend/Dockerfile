# syntax=docker/dockerfile:1.4
ARG PYTHON_BASE_IMAGE="python:3.14.3-slim-trixie"
ARG UID="9999"
ARG GID="9999"

# =============================================================================
# Builder for su-exec (replaces gosu, safer with smaller footprint)
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
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ca-certificates curl build-essential dos2unix tini && \
    curl -fsSL -o /usr/local/bin/su-exec.c "https://github.com/ncopa/su-exec/raw/${SU_EXEC_VERSION}/su-exec.c" && \
    echo "${SU_EXEC_SHA256}  /usr/local/bin/su-exec.c" | sha256sum -c - && \
    gcc -Wall -Werror -static -o /usr/local/bin/su-exec /usr/local/bin/su-exec.c && \
    chmod 0755 /usr/local/bin/su-exec


# =============================================================================
# Production base builder stage: builds runtime dependencies only
# =============================================================================
FROM ${PYTHON_BASE_IMAGE} AS builder-prod-base
ARG UID
ARG GID

# Runtime dependencies only - this layer is always cached
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev

ENV UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/jadawel/venv \
    UV_CACHE_DIR=/tmp/jadawel_uv_cache \
    UV_VERBOSE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/jadawel/venv/bin:$PATH" \
    PYTHONPATH="/jadawel/backend/src"

# hadolint ignore=DL3022
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# Create jadawel directory structure (including subdirs for COPY targets)
RUN mkdir -p /jadawel/ && chown -R $UID:$GID /jadawel/
    
USER $UID:$GID
WORKDIR /jadawel/backend

RUN --mount=type=cache,target=$UV_CACHE_DIR,sharing=locked,uid=$UID,gid=$GID \
    --mount=type=bind,source=LICENSE,target=/jadawel/LICENSE \
    --mount=type=bind,source=backend/uv.lock,target=/jadawel/backend/uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=/jadawel/backend/pyproject.toml \
    uv sync --frozen --no-dev --no-install-workspace --no-install-project \
    && find /jadawel/venv -type f \( -name "*.c" -o -name "*.h" \) -not -path "*/autobahn/*" -delete \
    # Strip test/doc directories from site-packages (keep django/drf tests - used at runtime)
    # Keep botocore/docs and boto3/docs - they're imported at runtime
    && (find /jadawel/venv/lib -type d \( -name "test" -o -name "tests" \) \
        -not -path "*/django/*" -not -path "*/rest_framework/*" -prune -exec rm -rf {} \; || true) \
    && (find /jadawel/venv/lib -type d \( -name "doc" -o -name "docs" -o -name "example" -o -name "examples" \) \
        -not -path "*/botocore/*" -not -path "*/boto3/*" -prune -exec rm -rf {} \; || true)


# =============================================================================
# CI Builder - includes dev dependencies for testing
# =============================================================================
FROM builder-prod-base AS builder-ci
ARG UID
ARG GID

USER $UID:$GID
WORKDIR /jadawel/backend

COPY --chown=$UID:$GID LICENSE /jadawel/LICENSE

# Install dev dependencies before copying source code to leverage caching
RUN --mount=type=cache,target=$UV_CACHE_DIR,sharing=locked,uid=$UID,gid=$GID \
    --mount=type=bind,source=backend/uv.lock,target=/jadawel/backend/uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=/jadawel/backend/pyproject.toml \
    uv sync --frozen --no-install-workspace --no-install-project \
    && find /jadawel/venv -type f \( -name "*.c" -o -name "*.h" \) -not -path "*/autobahn/*" -delete \
    # Strip test/doc directories from site-packages (keep django/drf tests - used at runtime)
    # Keep botocore/docs and boto3/docs - they're imported at runtime
    && (find /jadawel/venv/lib -type d \( -name "test" -o -name "tests" \) \
        -not -path "*/django/*" -not -path "*/rest_framework/*" -prune -exec rm -rf {} \; || true) \
    && (find /jadawel/venv/lib -type d \( -name "doc" -o -name "docs" -o -name "example" -o -name "examples" \) \
        -not -path "*/botocore/*" -not -path "*/boto3/*" -prune -exec rm -rf {} \; || true)

COPY --from=tool-builder /usr/bin/dos2unix /usr/local/bin/dos2unix

# Copy source code and tests

COPY --chown=$UID:$GID backend /jadawel/backend

COPY --chown=$UID:$GID tests /jadawel/tests

USER $UID:$GID
WORKDIR /jadawel/backend

RUN dos2unix /jadawel/backend/docker/docker-entrypoint.sh \
    && chmod a+x /jadawel/backend/docker/docker-entrypoint.sh

# Install the project
RUN --mount=type=cache,target=$UV_CACHE_DIR,sharing=locked,uid=$UID,gid=$GID \
    uv sync --frozen \
    && find /jadawel/venv -type f \( -name "*.c" -o -name "*.h" \) -not -path "*/autobahn/*" -delete \
    # Strip test/doc directories from site-packages (keep django/drf tests - used at runtime)
    # Keep botocore/docs and boto3/docs - they're imported at runtime
    && (find /jadawel/venv/lib -type d \( -name "test" -o -name "tests" \) \
        -not -path "*/django/*" -not -path "*/rest_framework/*" -prune -exec rm -rf {} \; || true) \
    && (find /jadawel/venv/lib -type d \( -name "doc" -o -name "docs" -o -name "example" -o -name "examples" \) \
        -not -path "*/botocore/*" -not -path "*/boto3/*" -prune -exec rm -rf {} \; || true)

# =============================================================================
# Production builder stage - creates runtime packages only
# =============================================================================
FROM builder-prod-base AS builder-prod
ARG UID
ARG GID

COPY --from=tool-builder /usr/bin/dos2unix /usr/local/bin/dos2unix

USER $UID:$GID
WORKDIR /jadawel/backend

# Copy source code
COPY --chown=$UID:$GID LICENSE /jadawel/LICENSE
COPY --chown=$UID:$GID backend /jadawel/backend

RUN dos2unix /jadawel/backend/docker/docker-entrypoint.sh \
    && chmod a+x /jadawel/backend/docker/docker-entrypoint.sh

# Install the project
RUN --mount=type=cache,target=$UV_CACHE_DIR,sharing=locked,uid=$UID,gid=$GID \
    uv sync --frozen --no-dev \
    && find /jadawel/venv -type f \( -name "*.c" -o -name "*.h" \) -not -path "*/autobahn/*" -delete \
    # Strip test/doc directories from site-packages (keep django/drf tests - used at runtime)
    # Keep botocore/docs and boto3/docs - they're imported at runtime
    && (find /jadawel/venv/lib -type d \( -name "test" -o -name "tests" \) \
        -not -path "*/django/*" -not -path "*/rest_framework/*" -prune -exec rm -rf {} \; || true) \
    && (find /jadawel/venv/lib -type d \( -name "doc" -o -name "docs" -o -name "example" -o -name "examples" \) \
        -not -path "*/botocore/*" -not -path "*/boto3/*" -prune -exec rm -rf {} \; || true)


# Install the standalone release plugins into the production virtual environment.
# Their folders are also carried into the all-in-one image for Django discovery.
COPY --chown=$UID:$GID plugins/jadawel_billing/backend /tmp/release-plugins/jadawel_billing/backend
COPY --chown=$UID:$GID plugins/jadawel_organizations/backend /tmp/release-plugins/jadawel_organizations/backend
RUN uv pip install --python /jadawel/venv/bin/python --no-deps \
    /tmp/release-plugins/jadawel_billing/backend \
    /tmp/release-plugins/jadawel_organizations/backend

# =============================================================================
# CI Target - lightweight image for pytest and E2E tests
# =============================================================================
FROM ${PYTHON_BASE_IMAGE} AS ci
ARG UID
ARG GID

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    gettext \
    xmlsec1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV DOCKER_USER=jadawel_docker_user \
    JADAWEL_IMAGE_TYPE="backend" \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/jadawel/venv \
    UV_CACHE_DIR=/tmp/jadawel_uv_cache \
    PATH="/jadawel/venv/bin:$PATH" \
    PYTHONPATH="/jadawel/backend/src:/jadawel/backend/tests" \
    DJANGO_SETTINGS_MODULE='jadawel.config.settings.test'

RUN groupadd --system --gid $GID ${DOCKER_USER} && \
      useradd --shell /bin/bash -l -u $UID -g $GID -o -c "" -d /jadawel -m ${DOCKER_USER} && \
      chmod 755 /jadawel

COPY --from=tool-builder /usr/local/bin/su-exec /usr/local/bin/su-exec
COPY --from=tool-builder /usr/bin/tini /usr/bin/tini
# hadolint ignore=DL3022
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# Create jadawel directory structure (including subdirs for COPY targets)
RUN mkdir -p /jadawel/backend/reports /jadawel/media && \
    chown -R $UID:$GID /jadawel/

# Copy the virtual environment and source code with tests
COPY --chown=$UID:$GID --from=builder-ci /jadawel /jadawel
COPY --chown=$UID:$GID ./docs /jadawel/docs/
COPY --chown=$UID:$GID deploy/plugins/*.sh /jadawel/plugins/
# The fork-hygiene suite checks the upstream attribution carried by these
# repository-level sources. Keep the CI image layout faithful to the checkout
# so the full test gate does not fail for missing, rather than altered, notices.
COPY --chown=$UID:$GID deploy/helm/jadawel/values.yaml /jadawel/deploy/helm/jadawel/values.yaml
COPY --chown=$UID:$GID formula/JadawelFormulaLexer.g4 /jadawel/formula/JadawelFormulaLexer.g4

USER $UID:$GID
WORKDIR /jadawel/backend
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/jadawel/backend/docker/docker-entrypoint.sh"]


# =============================================================================
# Dev image: includes dev dependencies and tools for local development
# Only works mounting the source code as a bind mount. See docker-compose.dev.yml for usage.
# =============================================================================

FROM ${PYTHON_BASE_IMAGE} AS dev
ARG UID="9999"
ARG GID="9999"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Build dependencies - this layer is always cached
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --batch --dearmor -o /usr/share/keyrings/pgdg.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    ca-certificates \
    postgresql-client-15 \
    gettext \
    xmlsec1 \
    curl \
    graphviz \
    procps \
    tmux \
    vim \
    lsof \
    sudo

ENV DOCKER_USER=jadawel_docker_user \
    JADAWEL_IMAGE_TYPE="backend" \
    UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/jadawel/venv \
    UV_CACHE_DIR=/tmp/jadawel_uv_cache_dev \
    PYTHONUNBUFFERED=1 \
    PATH=/jadawel/venv/bin:$PATH \
    PYTHONPATH=/jadawel/backend/src:/jadawel/backend/tests \
    DJANGO_SETTINGS_MODULE=jadawel.config.settings.dev

RUN getent group $GID || groupadd --system --gid $GID ${DOCKER_USER} && \
    useradd --shell /bin/bash -l -u $UID -g $GID -o -c "" -d /jadawel -m ${DOCKER_USER} && \
    chmod 755 /jadawel && \
    echo "${DOCKER_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${DOCKER_USER} && \
    chmod 0440 /etc/sudoers.d/${DOCKER_USER}

COPY --from=tool-builder /usr/local/bin/su-exec /usr/local/bin/su-exec
COPY --from=tool-builder /usr/bin/tini /usr/bin/tini
COPY --from=tool-builder /usr/bin/dos2unix /usr/local/bin/dos2unix
# hadolint ignore=DL3022
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# Create directory structure to install dependencies
RUN mkdir -p /jadawel/backend/docker /jadawel/media && \
    chown -R $UID:$GID /jadawel/

USER $UID:$GID
WORKDIR /jadawel/backend

# Install all dependencies
COPY --chown=$UID:$GID LICENSE /jadawel/LICENSE

RUN --mount=type=cache,target=$UV_CACHE_DIR,sharing=locked,uid=$UID,gid=$GID \
    --mount=type=bind,source=backend/uv.lock,target=/jadawel/backend/uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=/jadawel/backend/pyproject.toml \
    uv sync --frozen --no-install-workspace --no-install-project

# Configure tmux and bashrc
RUN echo "set -g default-command \"\${SHELL}\"" > /jadawel/.tmux.conf && \
    printf '%s\n' \
    '# Aliases' \
    'alias j="just"' \
    'alias m="python /jadawel/backend/src/jadawel/manage.py"' \
    'alias pytest="python -m pytest"' \
    '' \
    '# Show a helpful message' \
    'echo "Jadawel backend dev container"' \
    'echo "  m <cmd>     - Django manage.py (e.g., m shell_plus)"' \
    'echo "  pytest      - Run tests"' \
    'echo "  j           - See available commands"' \
    > /jadawel/.bashrc

COPY --chown=$UID:$GID backend/docker/docker-entrypoint.sh /jadawel/backend/docker/docker-entrypoint.sh
RUN dos2unix /jadawel/backend/docker/docker-entrypoint.sh \
    && chmod a+x /jadawel/backend/docker/docker-entrypoint.sh

HEALTHCHECK --interval=60s CMD ["/bin/bash", "/jadawel/backend/docker/docker-entrypoint.sh", "backend-healthcheck"]
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/jadawel/backend/docker/docker-entrypoint.sh"]
CMD ["django-dev"]


# =============================================================================
# Production target
# =============================================================================
FROM ${PYTHON_BASE_IMAGE} AS local
ARG UID
ARG GID

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV POSTGRES_VERSION=15 \
    DOCKER_USER=jadawel_docker_user \
    JADAWEL_IMAGE_TYPE="backend" \
    UV_PROJECT_ENVIRONMENT=/jadawel/venv \
    PYTHONUNBUFFERED=1 \
    PATH="/jadawel/venv/bin:$PATH" \
    PYTHONPATH="/jadawel/backend/src" \
    DJANGO_SETTINGS_MODULE='jadawel.config.settings.base'

# Runtime dependencies only
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --batch --dearmor -o /usr/share/keyrings/pgdg.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    xmlsec1 \
    gettext \
    postgresql-client-${POSTGRES_VERSION} \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid $GID ${DOCKER_USER} && \
      useradd --shell /bin/bash -l -u $UID -g $GID -o -c "" -d /jadawel -m ${DOCKER_USER} && \
      chmod 755 /jadawel

# In slim docker images, mime.types is removed and we need it for mimetypes guessing
COPY ./backend/docker/mime.types /etc/
COPY --from=tool-builder /usr/local/bin/su-exec /usr/local/bin/su-exec
COPY --from=tool-builder /usr/bin/tini /usr/bin/tini

RUN mkdir -p /jadawel/media && chown -R $UID:$GID /jadawel/

# Copy the virtual environment with the production dependencies
COPY --chown=$UID:$GID --from=builder-prod /jadawel/venv /jadawel/venv/

COPY --chown=$UID:$GID LICENSE /jadawel/LICENSE
COPY --chown=$UID:$GID --from=builder-prod /jadawel/backend /jadawel/backend/
COPY --chown=$UID:$GID ./docs /jadawel/docs/

# Remove application tests and dev-only directories
RUN rm -rf /jadawel/backend/tests /jadawel/backend/email_compiler

COPY --chown=$UID:$GID deploy/plugins/*.sh /jadawel/plugins/

USER $UID:$GID
WORKDIR /jadawel/backend

HEALTHCHECK --interval=60s CMD ["/bin/bash", "/jadawel/backend/docker/docker-entrypoint.sh", "backend-healthcheck"]
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/jadawel/backend/docker/docker-entrypoint.sh"]
CMD ["gunicorn"]


FROM local AS prod

CMD ["gunicorn"]
