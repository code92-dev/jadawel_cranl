# Sanad (سند) — the in-app AI assistant

Sanad is Jadawel's AI assistant: a chat panel inside the app that builds and works
with the user's databases, automations and application-builder apps on request. It is the fork's open-source counterpart to
Baserow's enterprise assistant (Kuma), which this fork cannot ship. Like the
application builder and automation, it is **limited to instance administrators
(staff)** while it is being introduced.

## What it can do

Sanad acts only inside the current workspace, with the signed-in user's own
permissions. Each capability is a tool the model calls:

| Area                | Tools                                                                                                                                                                        |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skills              | `load_skill` — expert guidance for one area, loaded on demand (below)                                                                                                        |
| Discover            | `list_applications`, `list_databases`, `list_tables`, `get_table_schema`, `list_views`                                                                                       |
| Build               | `create_database`, `create_table` (with initial fields), `update_table`                                                                                                      |
| Fields and formulas | `create_fields`, `update_fields` — formula fields are how it writes formulas from a description                                                                              |
| Rows                | `list_table_rows`, `create_rows`, `update_rows`                                                                                                                              |
| Views               | `create_view` (grid, gallery, kanban), `add_view_filter`, `add_view_sort`                                                                                                    |
| After `forms`       | `create_form`, `get_form`, `update_form`, `share_form`                                                                                                                       |
| Automations         | `create_automation`, `create_workflow`, `describe_automation_step`, `get_workflow`, `get_workflow_runs`, `add_automation_step`, `update_automation_step`                     |
| Application builder | `create_builder_application`, `list_pages`, `create_page`, `add_page_content`, `add_table_to_page`, `add_form_to_page`, `add_fields_to_form`                                 |
| After `app-builder` | `list_page_elements`, `describe_page_element`, `add_page_element`, `update_page_element`, `add_page_data_source`, `get_app_theme`, `update_app_theme`                        |
| After `dashboards`  | `create_dashboard`, `get_dashboard`, `add_dashboard_widget`, `update_dashboard_widget`                                                                                       |
| After `html-pages`  | `create_page_view`, `get_page_view`, `write_page_view`, `edit_page_view`, `list_page_view_revisions`, `restore_page_view_revision`                                           |
| Needs approval      | `delete_table`, `delete_fields`, `delete_rows`, `delete_view`, `delete_page`, `delete_automation_step`, `publish_workflow`, `delete_page_element`, `delete_dashboard_widget`, `share_form` |

### Skills

Six skills turn whichever model Sanad runs on into a specialist for one kind of
work. Each is `backend/src/arabase/sanad/skills/<name>/SKILL.md`: front matter
(`name`, `title`, `description`) and plain Markdown instructions, with no
provider-specific feature, so every model reads them the same way.

| Skill         | Covers                                                                                                                              |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `app-builder` | page plans, layout (columns, cards, repeats), header and menu, list → detail pages, data sources, theme, Arabic fonts and alignment |
| `automations` | when to automate, every trigger and action, data paths, bulk changes and loops, limits, routers, testing and debugging              |
| `dashboards`  | every widget and aggregation, layout, chart choice, and techniques (time buckets, rates, linked-record grouping)                    |
| `formulas`    | both formula languages, precision and rounding rules, NaN and division, dates, accounting and scientific recipes                    |
| `forms`       | Form views (نموذج): which fields a form can ask, questions, order, required answers, conditions, after-submit, sharing, prefills     |
| `html-pages`  | Page views (صفحة): the sandbox and data contract, a starter document, design craft, inline SVG charts, RTL and number formatting    |

**Loaded on demand.** The system prompt lists only each skill's one-line
description. When the model is about to do that kind of work it calls
`load_skill`; the instructions come back as the tool result and stay in the chat's
history, so a skill is loaded once per conversation, never on every message.
`skills.loaded_skills` reads the conversation to know what is loaded.

**Specialist tools follow their skill.** Tools that need a skill's guidance to be
used well (`SanadTool.skill`) are hidden from the model — through pydantic-ai's
tool `prepare` hook — until that skill is loaded. The everyday tools stay
available without any skill.

**The skills are tested.** `test_sanad_skill_formulas.py` asserts every number
the formulas skill states (rounding modes, precision, NaN, date boundaries, the
VAT, loan and age recipes) against the engine; `test_sanad_skills.py` runs the
patterns the other skills teach (a chart grouped by a lookup formula, an iterator
over a bulk insert, a router, a list → detail app with a menu and a themed header)
and fails if a skill names a tool or a theme property that does not exist.

Facts the skills teach that surprise even experienced builders, all verified:
runtime formulas round half to even and fail on division by zero even inside
`if()`; `date_diff('mm')` counts month boundaries; row triggers deliver a bulk
change as one run; iterator items are addressed by field name; a chart grouped by
a linked field shows row IDs; builder text alignment is physical (Arabic apps need
'right'); the Inter font has no Arabic letters; schedules run in UTC; a live
workflow is disabled after more than five consecutive failed runs.

### Pages (صفحة)

A Page view (`docs/PAGE_VIEW.md`) was written only from an outside AI client over
MCP. Sanad writes one from inside Jadawel: the user gives the page's number (its
view ID, shown on the page's setup panel) or asks from the page itself, whose ID
travels with the message. Staff also see an **Ask Sanad** box on an empty page's
setup panel; it opens Sanad with "Design page <number>: " typed in a new chat.

- `get_page_view` returns the fields the page receives (with select options),
  the row count and five sample rows serialized with field names, exactly the
  shape of `row.values` in the page.
- `write_page_view` saves through the same route as the view's REST `PATCH`:
  `HtmlPageViewType.handle_view_update` first, so a page under MCP artifact
  protection turns the write into a draft awaiting approval; otherwise an
  undoable `UpdateViewActionType`. The previous document is kept as a revision
  first, as the MCP path does. `edit_page_view` applies exact find/replace edits
  (each must match once), so a small change does not cost a full rewrite.
- Every write returns `warnings` from `check_page_html`: `values['…']` names that
  are not fields of the page, no `onData`, network or storage calls, external
  files while external resources are off, navigation, left/right CSS, and
  `ar` number formatting (Arabic-Indic digits). They catch the mistakes that make
  a page render blank, whatever the model.
- The runtime the skill teaches is checked against `pageDocument.js` and
  `HtmlPageView.vue` by `test_sanad_page_views.py`, and the skill's starter
  document must pass `check_page_html`.

### Forms (نموذج)

A Form view made with `create_view` starts with every field disabled, so it asks
nothing; `create_view` now refuses `form` and points to `create_form`, which
builds the whole form in one call: settings (title, description, button text,
the message or redirect after submitting) and its questions — which fields, in
what order, their labels, help text, required flags, input style (radios for a
single select, checkboxes for a multiple select) and show-when conditions on
earlier answers. Without `questions` it asks every field a form can fill and
reports the rest (formulas, lookups, created on…) in `skipped_fields`.

Settings are validated by the serializer `PATCH /api/database/views/<id>/` uses
and saved with `UpdateViewActionType`; questions by the view's field-options
serializer and `UpdateViewFieldOptionsActionType`, so the editor's rules apply
and every change can be undone. Select conditions take the option's text and are
stored as its ID, like view filters. `update_form` changes the settings it is
given and, with `questions`, replaces them all. `share_form` turns the public
link on and returns it; it waits for approval like publishing a workflow, since
anyone with the link can then add rows. Survey mode is not offered: it was a
premium feature and this fork registers only the plain form mode.

Two facts the `forms` skill teaches, both pinned by `test_sanad_forms.py`: a
required question that has show-when conditions is only required in the browser
(`FormViewFieldOptions.is_required`), and the description and after-submit
message are plain text, not Markdown.

### Automations

`create_automation` sends the same `init_with_data` flag as the "add new" menu, so
the automation arrives with its first workflow and a connection to the workspace's
tables. Steps are added trigger first, then each action after the previous one.
A step's settings are validated by that step type's own request serializer — the
one `PATCH /api/automation/node/<id>/` uses — so Sanad cannot save a setting the
editor would reject. `describe_automation_step` reads the same serializer to tell
the model which settings each of the 17 step types takes (triggers on rows
created/updated/deleted, schedules and webhooks; actions on rows, HTTP, email,
Slack, AI, routers and iterators). Publishing puts a workflow live on real data,
so it waits for the user's approval like a delete.

### Application builder

Builder tools work at the level of intent rather than individual elements: a page
gets content (headings, text, links, images from plain text), a table of a database
table's rows, or a form whose submissions create rows. Each builds the data source,
elements and workflow actions it needs through the permission-checked builder
services, following the builder's own sample-app initializer. Form inputs match the
field type (text, email, number, long text, checkbox, date, choice). A link-to-table
field (a task's project or assignee) becomes a dropdown of the linked table's rows:
a list-rows data source on that table (up to the 200-row page limit) feeds the
choice element's formula options, the row ID is the value and the primary field the
label, so the create-row action links the chosen rows. Fields a form still cannot
set (for example files, multiple select, collaborators) are reported back.
`add_fields_to_form` asks for more fields in an existing form and adds them to its
create-row mapping, so a form can be extended instead of rebuilt. Publishing an app
to a domain stays a manual step in the app's settings.

The user's open table and view are sent with each message, so "this table" works.
Answers are Markdown and follow the user's language (Arabic by default).

Compared with the Baserow AI features this was modelled on:

| Baserow                            | Sanad                                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| Kuma: build tables and fields      | Yes                                                                            |
| Kuma: formulas from a description  | Yes, as a chat request that creates or updates a formula field                 |
| Kuma: views, filters, sorts        | Yes (create view, add filter, add sort; not grouping yet)                      |
| Kuma: chat history                 | Yes, per user and workspace                                                    |
| Kuma: build applications           | Yes: pages, layout, theme, menus, list → detail pages and forms that save rows |
| Kuma: build automations            | Yes: triggers, actions and publishing (with approval)                          |
| Kuma: search the documentation     | Not yet — answers come from the model's own knowledge                          |
| AI field                           | Not yet (a separate field type)                                                |
| "Generate using AI" formula button | Not yet (the chat covers the use case)                                         |
| Configure generative AI            | Reuses the instance-level provider settings; workspace-level keys stay removed |

## Configuration

Administrators manage the AI provider keys in **Admin → Settings → AI providers**
(`web-frontend/modules/arabase/generativeAI/`, API
`/api/arabase/admin/generative-ai/`, staff only). The same keys serve every AI
feature — Sanad, AI steps in automations and the builder — because core's provider
registry reads them. Four providers are offered:

| Provider           | Admin settings                                | Environment fallback                                              |
| ------------------ | --------------------------------------------- | ----------------------------------------------------------------- |
| OpenAI             | API key, models, organization, base URL       | `JADAWEL_OPENAI_API_KEY`, `_MODELS`, `_ORGANIZATION`, `_BASE_URL` |
| Claude (Anthropic) | API key, models                               | `JADAWEL_ANTHROPIC_API_KEY`, `_MODELS`                            |
| Ollama             | host, models — keeps all data on your servers | `JADAWEL_OLLAMA_HOST`, `_MODELS`                                  |
| OpenRouter         | API key, models, organization                 | `JADAWEL_OPENROUTER_API_KEY`, `_MODELS`, `_ORGANIZATION`          |

A provider's settings resolve in this order: an AI connection's own settings, the
workspace, the admin settings, then the environment variables. Keys are sealed with
a Fernet key derived from `SECRET_KEY` (`arabase.generative_ai.store`), shown back
only as their last four characters, and unreadable if `SECRET_KEY` changes — re-enter
them after rotating it.

**Mistral is disabled for now.** Its provider code is untouched and it stays
registered under its type, but it is never enabled, even if
`JADAWEL_MISTRAL_API_KEY` is set, and no picker offers it. Re-enabling it means
removing `"mistral"` from `DISABLED_PROVIDERS` in `arabase/generative_ai/store.py`
and the `unregister('generativeAIModel', 'mistral')` line in
`web-frontend/modules/arabase/registryPlugin.js`, then adding it to
`MANAGED_PROVIDERS` to manage it in the settings page.

With no provider set up, the panel links administrators to the settings, and the
API answers `ERROR_SANAD_NO_MODEL_AVAILABLE`. Use a model with reliable tool
calling; small local models often call tools badly.

Workspace-level AI keys were removed on purpose (PATCHES.md, _Remove workspace AI
keys_), so there is deliberately no per-workspace setting.

## How it works

```
panel ──POST message──▶ API ──on commit──▶ runner thread (web process)
  ▲                                                │ pydantic-ai agent + tools
  └──── polls GET chat every 1.5 s ◀──── message status / actions saved per tool
```

- **Backend** — `backend/src/arabase/sanad/`: `models.py` (`SanadChat`,
  `SanadMessage`, `SanadBudget`, `SanadUsage`), `tools/`, `agent.py`,
  `handler.py`, `runner.py`, `budget.py`; API in `backend/src/arabase/api/sanad/`
  under `/api/arabase/sanad/`; migrations `arabase/0019_sanad_chat` and
  `arabase/0021_sanad_budget`.
- **Tools, by domain** — `tools/` is one module per domain behind the
  `SanadTool` contract in `tools/base.py` (name, description, input schema, run
  function, optional skill). Each module exposes `get_tools()`, and
  `tools.get_sanad_tools()` gathers them in the order of `tools.DOMAINS`:

  | Module | Tools |
  |---|---|
  | `core` | `load_skill`, `list_applications` |
  | `database` | reused MCP tools (databases, tables, fields, rows), views, filters, sorts |
  | `form` | Form views (`forms` skill) |
  | `automation` | automations, workflows, steps, runs |
  | `builder` | builder apps at the level of intent: pages, content, tables, forms |
  | `builder_elements` | every element, data sources and the theme (`app-builder` skill) |
  | `dashboard` | dashboards and widgets (`dashboards` skill) |
  | `page` | Page views (`html-pages` skill) |

  Helpers more than one domain uses (`get_application`, `formula_literal`,
  `describe_serializer`, `select_option_ids`) live in `base.py`, so domains do not
  import each other; `builder_elements` extends `builder` and is the exception. A
  new tool goes into its domain's `get_tools()`; a new domain is a module plus an
  entry in `DOMAINS`.
- **Model** — core's `generative_ai_model_type_registry` returns a pydantic-ai model
  for the chosen provider; pydantic-ai runs the tool loop.
- **Tools** — most are the fork's MCP tools, called with the chat user so their
  service layer applies that user's permissions and workspace scope. They are called
  directly, not through the MCP registry's interceptor, because protected-field
  policies belong to an MCP endpoint and a chat has none. View, filter and sort
  tools use the same action types as the UI, so undo works.
- **Turns run on a background thread in the web process, not in Celery**
  (`runner.py`, at most 4 at once per web process). A turn is mostly waiting on
  the provider, often for a minute or more. The small-plan deployment runs one
  Celery worker with a concurrency of 1 (`JADAWEL_RUN_MINIMAL`), which also runs
  automation workflows, publish jobs and realtime updates. When turns were a
  Celery task they held that only slot, so the rows Sanad added could not trigger
  their automations, and its own publish job could not run, until the turn ended.
  Sanad then read an empty result and concluded the trigger was broken.
  A turn stops itself after 9 minutes (checked before each tool call; writing a
  Page view's document can take one request about 4 minutes), a model request
  fails after 2 minutes without data, and a turn is capped at 40 model requests.
  A turn still `pending` after 15 minutes (its process restarted) is marked
  failed so the chat is usable again.
- **A budget per workspace** — see [Budget](#budget).
- **Each tool call runs in its own database transaction**, as each editor API
  request does: tools that lock rows need one, and a failed call leaves nothing
  half done.
- **Checking automations** — `get_workflow_runs` returns a workflow's latest runs
  with each failed step's error, and every step result names the field behind
  each field mapping, so Sanad can see a wrong field or a select value that is not
  an option instead of guessing.
- **Frontend** — `web-frontend/modules/arabase/sanad/`: an item in the workspace
  tools window and a panel
  rendered in core's right sidebar through `ArabasePlugin`'s
  `getWorkspaceUtilityComponents` / `getRightSidebarWorkspaceComponents` hooks.
  The tools-window hook is a small core addition, logged in PATCHES.md.

### The panel

`SanadPanel.vue` with `modules/arabase/assets/scss/sanad.scss`: a rounded card in
core's right sidebar. Each message is its own block: the user's words in a solid
bubble at the end side, each answer in a tinted card with Sanad's avatar, its
steps (a foldable list, open while Sanad works and folded once a list of more than
four sits above the answer), the Markdown answer and any approval.

Every colour follows the interface theme the user picked (white, sage, gray, blue,
rose, amber). `applyInterfaceTheme` puts the palette on the document as
`--jadawel-primary-100…900` plus surface colours, and the stylesheet mixes its
tokens (`--sanad-accent`, `--sanad-tint`, `--sanad-line`…) from those with
`color-mix()`, so switching the theme recolours the panel at once with no script.
Tints come from the 300 step, the first genuinely coloured one on every palette.
`sanad.spec.js` fails if the stylesheet goes back to a fixed hue.

## Budget

Each workspace has a monthly allowance (calendar month, UTC) in two dimensions,
kept in `SanadUsage` (one row per workspace and month) and enforced by
`arabase.sanad.budget`:

- **Turns** — messages sent to Sanad, counted when the message is accepted,
  under a row lock, so a burst of messages cannot slip past the limit. Resuming
  after an approval is the same turn and is not counted again.
- **Tokens** — input plus output, as the provider reports them, added after
  every model run, failed runs included (they are billed too). A running turn is
  also capped at what is left of the month through pydantic-ai's
  `UsageLimits.total_tokens_limit`, so it overshoots by at most one response.
  Turns running at the same moment in one workspace each see the same remainder,
  so together they can overshoot by up to one turn's worth each.

A used-up allowance refuses a new message with `ERROR_SANAD_BUDGET_EXCEEDED`
(HTTP 429) and stops a running turn with `SANAD_ERROR_BUDGET_EXCEEDED`; the
panel shows both in the user's language.

Limits come from the workspace's `SanadBudget` row; a limit left empty there
falls back to `JADAWEL_SANAD_MONTHLY_TURN_LIMIT` /
`JADAWEL_SANAD_MONTHLY_TOKEN_LIMIT` (docs/CONFIGURATION.md), and a dimension with
neither is unlimited — today's behaviour, fine while only staff use Sanad. **Set
the defaults before opening Sanad to workspace admins.**

`GET /api/arabase/sanad/workspace/<id>/budget/` returns the limits in force and
this month's `turns` and `tokens` to anyone who may use Sanad there; `PUT` sets
the workspace's own limits (`null` falls back to the default) and is limited to
instance staff, which stays true once admins can chat.

## Security

- **Staff only**, enforced by the API (`ERROR_SANAD_NOT_ALLOWED`), not only hidden
  in the UI. The user must also be a member of the workspace.
- **A chat is private** to the user who started it.
- **No privilege of its own**: every tool runs as the chatting user.
- **Deletes and publishing need approval**: the model's call pauses the turn; the
  panel shows what would happen and nothing runs until the user approves.
  Declining tells the model not to retry.
- **Builder apps act as their builder**: the data connection Sanad creates is
  authorized as the chatting admin, exactly like one made by hand in the editor.
  Once an app is published, its tables show and its forms write with that admin's
  access, so review a generated app before publishing it to a public domain.
- **Data leaves the instance** for whichever provider is configured: table and
  field names, the rows Sanad reads, and the conversation. MCP field protection
  does not apply to Sanad. Use Ollama to keep everything on your own servers.
- **Provider errors are not shown** in the chat: the turn records a stable error
  code, and the details go to the server log.
- Chat history (including tool results) is stored in PostgreSQL in
  `arabase_sanadchat.history` until the user deletes the chat.

## Tests

- `backend/tests/arabase/test_generative_ai_settings.py` — admin-only access, keys
  sealed and never returned, admin settings ahead of the environment, Mistral
  disabled even when configured, invalid values rejected.
- `backend/tests/arabase/test_sanad_apps.py` — automation and builder tools, plus
  two whole turns whose results are then used for real: the published workflow
  fires on a new row, and the generated form's submit action creates a row.
- `backend/tests/arabase/test_sanad.py` — access rules, full turns against a
  scripted pydantic-ai `FunctionModel`, view tools, cross-workspace isolation, the
  approval pause, failure handling, and the budget: counting, refusing, the token
  cap stopping a turn, approvals not counted twice, defaults and staff-only edits.
- `backend/tests/arabase/test_sanad_forms.py` — Form view tools: questions,
  order, labels, conditions stored as the form renders them, refused mistakes,
  replacing questions, sharing, workspace isolation, and the skill's facts.
- `backend/tests/arabase/test_sanad_skills.py` — the skills, their on-demand loading
  and tool gating, the dashboard and page tools, and the patterns the skills teach.
- `backend/tests/arabase/test_sanad_skill_formulas.py` — every number the formulas
  skill states, for both formula languages.
- `backend/tests/arabase/test_sanad_page_views.py` — Page view tools: the data
  shape, revisions and restore, the approval boundary, find/replace edits, the
  write checks, workspace isolation, and the skill against the real runtime.
- `web-frontend/test/unit/arabase/sanad.spec.js` — staff-only visibility for Sanad,
  the builder and automation, plus the panel's send, poll and approve flow.
