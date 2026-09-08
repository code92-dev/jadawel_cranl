# Standalone packaging and installation

This guide is based on this checkout's `deploy/plugins/{install_plugin,list_plugins,utils}.sh`,
`backend/src/jadawel/config/settings/base.py`,
`web-frontend/docker/docker-entrypoint.sh`, and
`web-frontend/config/nuxt.config.base.ts`, checked on 2026-09-07.
Re-read them for the target image/revision. The upstream
[installation guide](https://baserow.io/docs/plugins%2Finstallation) supplies context;
the local scripts define the executable contract.

## Folder and names

Use a unique Python-safe underscore name for the plugin folder and import package.
The frontend entrypoint converts underscores to hyphens for its module directory.
For example:

```text
plugins/example_plugin/
  jadawel_plugin_info.json
  backend/
    pyproject.toml
    src/example_plugin/
      __init__.py
      apps.py
      plugins.py
      config/
        __init__.py
        settings/
          __init__.py
          settings.py
      api/
        __init__.py
        urls.py
  web-frontend/
    package.json
    modules/example-plugin/
      module.js
      plugin.js
      locales/
        en.json
        ar.json
```

Include only the backend/frontend halves needed. Add models, migrations, tests, and
feature files as required. The backend must be pip-installable with package discovery
configured for `src/`; use a build backend compatible with the actual image. Do not
install a second Jadawel distribution as a plugin dependency. The frontend must be
a valid Node package with the necessary files and dependencies included; avoid
bundling another Vue/Nuxt runtime. Inspect current versions before declaring ranges.

Use `jadawel_plugin_info.json`, not upstream's `baserow_plugin_info.json`.
Include factual name, plugin version, description, author, license, and available
contact/source URLs. Record tested Jadawel revisions in the plugin's installation
documentation. The local listing script reads `description`; the installer does
**not** validate a supported-version or plugin-API-version field. Do not invent a
`supported_jadawel_versions` compatibility guarantee or describe metadata as
enforced. Upstream's `0.0.1-alpha` is not evidence of current fork compatibility.

## Backend discovery

The settings loader finds child folders with `backend/` under `JADAWEL_PLUGIN_DIR`
(default `/jadawel/plugins`) and appends each folder name to `INSTALLED_APPS`.
The matching Python package must already be installed. Provide a discoverable
`AppConfig`; do not also add the same app through `ADDITIONAL_APPS`.

For discovered plugins the loader attempts to import
`example_plugin.config.settings.settings` and call `setup(settings)`.
A no-op implementation is sufficient when no custom settings are needed:

```python
def setup(settings):
    pass
```

Although failed imports are caught, inspect startup logs so an internal dependency
error is not mistaken for successful loading. This is the actual import path, not
the duplicated `src` path printed in the old upstream tutorial.

For development outside the image, explicitly configure the plugin directory and
install the backend into the app's environment. `ADDITIONAL_APPS` alone does not
add the plugin to the loader's settings-setup loop.

## Frontend discovery

The Docker entrypoint checks for
`/jadawel/container_markers/example_plugin.web-frontend-built`, then adds
`<plugin-dir>/web-frontend/modules/example-plugin/module.js` to `ADDITIONAL_MODULES`.
Nuxt reads that comma-separated list in `config/nuxt.config.base.ts`.
Outside the Docker entrypoint, configure `ADDITIONAL_MODULES` explicitly with a
resolvable module entry path. A successful `yarn add` alone does not load the module.

## Installer behavior and distribution

Run the installer inside a disposable compatible Jadawel container first; it assumes
`/jadawel`, the image virtualenv, Docker user, and helper utilities. It is not a
host-development bootstrap script. With the plugin copied or mounted at the shown
path inside that container:

```bash
/jadawel/plugins/install_plugin.sh --folder /tmp/plugins/example_plugin
/jadawel/plugins/list_plugins.sh
```

The first command installs Python/Node dependencies and builds the frontend when
present. For development `--dev` uses editable Python installation and skips the
production frontend build. For runtime setup, the installer accepts `--runtime`;
never use that flag during Docker image builds. Inspect `--help` for the target
version before adding options. Do not add `--overwrite` routinely: it replaces an
existing plugin and forces rebuild/setup.

Source layout requirements differ:

- `--folder`: points directly to `example_plugin/`.
- `--git`: repository root must contain exactly one directory under `plugins/`.
- `--url`: the current extraction glob expects an outer directory containing
  `plugins/example_plugin/`, for example `release/plugins/example_plugin/` in a
  `.tar.gz`. Inspect archive members before distributing it.

Startup can install sources from `JADAWEL_PLUGIN_URLS` and
`JADAWEL_PLUGIN_GIT_REPOS`; `JADAWEL_DISABLE_PLUGIN_INSTALL_ON_STARTUP` disables
startup installation. Prefer a reproducible image containing reviewed plugin code
over an unpinned moving Git branch. The legacy `--hash` implementation uses SHA-1
and path-sensitive file output; do not present it as a modern signature or substitute
for artifact provenance. Do not download or install untrusted plugins as a test.

## Lifecycle caveats that require verification

Optional `build.sh`, `runtime_setup.sh`, and `uninstall.sh` run with application/image
privileges. Create them only when needed. Build steps must not require a live DB;
runtime setup must tolerate retries and external PostgreSQL. Keep database changes
in normal migrations where possible, and verify migrations run before serving the
new behavior. Do not assume an embedded database exists on CranL.

Two current installer details prevent blindly copying upstream lifecycle examples:

1. The frontend production build occurs **before** frontend `build.sh`. Assets
   needed by Nuxt must be ready before that build or use a verified alternative.
2. The frontend runtime condition checks for an **existing** runtime marker (or
   overwrite), unlike the backend's missing-marker condition. Do not rely on a new
   frontend `runtime_setup.sh` running on first startup. Verify the target behavior
   and use a working lifecycle path; report any necessary installer fix separately.

Test a fresh install and restart, not just a container with existing markers.
Uninstall can invoke scripts and remove package files. Document how to remove the
original image/env installation source to prevent reinstallation, and preserve
user data by default. Test removal only on a disposable instance unless explicitly
authorized against the real instance.
