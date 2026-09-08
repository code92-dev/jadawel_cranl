---
name: jadawel-plugin-creator
description: Create, extend, or port Jadawel application plugins using Django registries and Nuxt 3 modules. Use for standalone installable plugins or additive Jadawel features such as field types, views, filters, formulas, integrations, widgets, and custom pages, including adapting Baserow plugin examples. Covers packaging, Arabic/English UI, permissions, migrations, and verification. Not for creating Codex plugin manifests or MCP-only connectors.
---

# Jadawel Plugin Creator

Build a working Jadawel extension with a verified registration path, focused tests,
and installation instructions appropriate to the requested delivery mode.

## Source of truth

Follow the [Baserow plugin introduction](https://baserow.io/docs/plugins%2Fintroduction)
for the extension model: plugins can extend backend, frontend, or both, and execute
with application privileges in self-hosted installations. Use trusted code and back
up persistent data before installing against an existing instance.

The [upstream creation guide](https://baserow.io/docs/plugins%2Fcreation) is explicitly
outdated; its boilerplate supports Baserow 2.0.6 and earlier and describes Nuxt 2.
Do not run its scaffolder or copy its APIs unchanged into Jadawel. The target
checkout's code and `AGENTS.md` determine imports, runtime versions, registration,
and packaging. These references were checked on 2026-09-07; recheck relevant
sources when porting to another revision.

Paths below are relative to the target Jadawel repository, not this skill folder.
If the checkout is unavailable, obtain its path or revision before inventing APIs.

## 1. Establish the contract

1. Read `AGENTS.md`, relevant nested guidance, and `git status --short`. Preserve
   unrelated changes. Inspect package manifests and the closest existing extension.
2. Identify the requested behavior, extension type, backend/frontend needs,
   persistent data, permissions, external calls, and observable acceptance criteria.
   Resolve ordinary choices from the request; ask only for missing information that
   materially changes the implementation.
3. Choose and state the delivery mode:
   - **Standalone:** default for a reusable, installable plugin. Use its own package
     under `plugins/<plugin_name>/`; read [Standalone packaging](references/standalone-packaging.md).
   - **In-tree:** for a feature in this fork. Add backend code under
     `backend/src/arabase/` and frontend code under `web-frontend/modules/arabase/`.
     Extend the existing Arabase registration points; do not create a second
     Arabase app or call an in-tree feature an independently installable package.
4. Pick a stable unique type identifier and API prefix. Search for collisions.
   Treat persisted type strings as compatibility contracts, not display labels.

## 2. Map the extension before editing

Read [Extension points](references/extension-points.md). Locate the actual registry,
base class, representative implementation, corresponding frontend type, and tests.
Record the intended files and registration path in a short implementation update.

Use `jadawel.*`, `@jadawel`, and `JADAWEL_*` where the checkout defines them.
Preserve upstream copyright, provenance URLs, historical migrations, and intentional
proprietary-package absence checks. Never apply a global Baserow string replacement.
Do not add dependencies on removed premium or enterprise packages.

Prefer existing registries and hooks. If a core backend edit is unavoidable, explain
why the hook cannot satisfy the requirement and record the edit in `PATCHES.md`.

## 3. Implement a complete vertical slice

1. **Backend, when needed:** define the type and its models/serializers/handlers;
   register from `AppConfig.ready()` with imports inside that method. Add namespaced
   API URLs through `Plugin.get_api_urls()` or the selected type's supported hook.
   Keep startup registration free of database queries and network calls.
2. **Data and permissions:** add migrations for schema changes, preserving existing
   migration history. Reuse current permission and operation checks at the handler
   boundary. Validate object/workspace ownership and public-share access; hiding a
   frontend control is not authorization. Use transactions for related mutations.
3. **Frontend, when needed:** use `defineNuxtModule`, `addPlugin`, and Nuxt 3 runtime
   plugins. Register types after their owning registry namespaces exist. Match
   backend type strings exactly. Follow current store, routing, SSR, and component
   patterns; use Vue 3 `h`, and `.jsx`/`.tsx` for JSX.
4. **Arabic UI:** ship every user-facing key in both `en.json` and `ar.json`; use
   `docs/GLOSSARY_AR.md` and add recurring terms there before reuse. Preserve
   placeholders and technical tokens. Use CSS logical properties and verify both
   Arabic RTL and English LTR, including mixed-direction values and controls.
5. **External services and content:** reuse existing HTTP clients and network
   restrictions, keep secrets server-side, apply timeouts, validate inputs, and use
   the existing sanitization boundary for untrusted HTML. Do not weaken global
   security settings to make a plugin work.
6. **Lifecycle:** keep durable data in the database or configured Django storage.
   Make setup repeatable. Document migration and data-retention behavior for
   upgrades/removal; do not automatically reverse migrations or delete user data.

Consult the repository's `create-update-service`, `create-in-app-notification`, or
`add-django-config-env-var` skill when that specific work is needed. Read through
`.agents/skills/`, which is canonical. For tests consult `write-backend-unit-test`
or `write-frontend-unit-test`. If these helpers are absent in another checkout,
use its current code and tests rather than relying on unavailable instructions.

## 4. Verify behavior and loading

Read the target `justfile`, backend/frontend justfiles, and package scripts before
choosing commands. Current entry points are `just b ...` and `just f ...`.

- Run focused backend/frontend tests for the behavior changed, plus relevant lint.
  Assert actual registry lookup and endpoint/component behavior, not only imports.
- For permissions, test an allowed user, unauthenticated access, a denied role, and
  another workspace's object. Test invalid inputs and public links when applicable.
- For persistent types, exercise creation, edit/read, migration, and applicable
  conversion/import/export or undo behavior. Check upgrade compatibility.
- For UI, run locale parity and inspect Arabic/English rendering, keyboard controls,
  and browser errors. Exercise SSR and the production build if module loading changed.
- For standalone delivery, install into a disposable compatible Jadawel image and
  verify backend discovery, frontend loading, migrations, restart, and a real user
  flow. Check the first-start caveats in the packaging reference.
- Before a requested push, run the repo-required Arabic locale parity and fork
  hygiene gates as well as checks appropriate to the change.

Do not report an unrun check as passing. Separate environment blockers from code
failures and state exactly what remains unverified.

## 5. Deliver

Provide the implemented behavior, changed paths, type identifiers, tested revision,
verification results, and any dependency/schema/environment changes. For standalone
plugins include usable installation and upgrade instructions with pinned artifacts
and data-retention guidance. For in-tree features explain the existing app/module
registration. Clearly identify incomplete acceptance criteria.

Deployment is separate from skill or plugin creation. If deployment is requested,
read `docs/DEPLOY_CRANL.md`: this fork's root Dockerfile consumes a published image,
so a git push alone does not deploy plugin code. Follow the current image publish,
pin, deploy, and live verification workflow within the user's authorized scope.
