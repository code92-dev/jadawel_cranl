# Extension points in Jadawel

Read only the rows relevant to the requested behavior. Paths are repository-relative.
Recheck class signatures and required methods in the target revision before coding.

| Extension | Backend source of truth | Frontend starting point |
| --- | --- | --- |
| Plugin/API mount or application | `backend/src/jadawel/core/registries.py`: `Plugin`, `plugin_registry`, `application_type_registry` | `web-frontend/modules/core/` plugin and application types |
| Field or field conversion | `backend/src/jadawel/contrib/database/fields/registries.py`: `field_type_registry`, `field_converter_registry`; nearby `field_types.py`, `field_converters.py` | `web-frontend/modules/database/fieldTypes.js` and field components |
| View, filter, aggregation, decoration | `backend/src/jadawel/contrib/database/views/registries.py`: `view_type_registry`, `view_filter_type_registry`, `view_aggregation_type_registry`, `decorator_type_registry`, `decorator_value_provider_type_registry` | `web-frontend/modules/database/`; additive examples under `modules/arabase/kanban/`, `views/`, `decorators/` |
| Formula function | `backend/src/jadawel/contrib/database/formula/registries.py`: `formula_function_registry`; neighboring implementations | Inspect formula editor/function definitions under `web-frontend/modules/database/`; implement UI counterpart only where required |
| Integration/service | `backend/src/jadawel/core/services/registries.py` and `backend/src/jadawel/contrib/integrations/` | `web-frontend/modules/integrations/`; `modules/arabase/integrations/serviceTypes.js` |
| Dashboard widget | `backend/src/jadawel/contrib/dashboard/widgets/registries.py`; `backend/src/arabase/dashboard/widgets/widget_types.py` | `web-frontend/modules/arabase/dashboard/widgetTypes.js` |
| Custom page, styling, UI-only feature | No backend required unless data/API behavior needs it | `web-frontend/modules/arabase/module.js`, `routes.js`, `plugin.js`, `registryPlugin.js` |

## Backend registration

Read `backend/src/arabase/apps.py` and `plugins.py` together. The current pattern is:

```python
from django.apps import AppConfig


class ExamplePluginConfig(AppConfig):
    name = "example_plugin"

    def ready(self):
        from jadawel.core.registries import plugin_registry
        from example_plugin.plugins import ExamplePlugin

        plugin_registry.register(ExamplePlugin())
```

The corresponding plugin class can mount its own URL namespace:

```python
from django.urls import include, path
from jadawel.core.registries import Plugin


class ExamplePlugin(Plugin):
    type = "example_plugin"

    def get_api_urls(self):
        return [
            path("example-plugin/", include("example_plugin.api.urls", namespace=self.type)),
        ]
```

Create the included URLconf with `app_name = "example_plugin"` and actual routes,
and test `/api/example-plugin/...`. These snippets demonstrate standalone wiring,
not a complete feature. An in-tree feature extends the existing `ArabaseConfig`
and `ArabasePlugin` instead. Types with their own URL hooks may already supply
their routes; inspect the core URL assembly before adding another mount.

## Nuxt 3 registration

Use `web-frontend/modules/arabase/module.js` for build-time setup and
`registryPlugin.js` for runtime registry ordering. A standalone module starts with:

```javascript
import { defineNuxtModule, addPlugin, createResolver } from 'nuxt/kit'

export default defineNuxtModule({
  meta: { name: 'example-plugin-module' },
  setup() {
    const { resolve } = createResolver(import.meta.url)
    addPlugin({ src: resolve('./plugin.js') })
  },
})
```

Its runtime plugin uses `defineNuxtPlugin` (explicit import from `#app` is available),
declares `dependsOn` for the actual owning plugins, and obtains `$registry` from
`nuxtApp`. Existing Arabase registrations construct type instances with
`{ app: nuxtApp }`, for example `$registry.register('view', new ViewType(context))`.
Confirm the real base class and namespace rather than pasting a generic `ViewType`.
Use `createResolver` for packaged files; never point a distributed plugin at an
author's checkout. Browser APIs belong behind client lifecycle guards.

For translations, follow the module's `i18n:registerModule` hook and register its
locale directory; creating JSON files alone does not load them. Confirm the locale
checker includes the plugin files. If it only scans built-in modules, add a focused
parity check for the standalone package as well.
