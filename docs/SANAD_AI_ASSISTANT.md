# Sanad (سند) — the in-app AI assistant

Sanad is Jadawel's AI assistant: a chat panel inside the app that builds and works
with the user's databases, automations and application-builder apps on request. It is the fork's open-source counterpart to
Baserow's enterprise assistant (Kuma), which this fork cannot ship. Like the
application builder and automation, it is **limited to instance administrators
(staff)** while it is being introduced.

## What it can do

Sanad acts only inside the current workspace, with the signed-in user's own
permissions. Each capability is a tool the model calls:

| Area                | Tools                                                                                                                               |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Discover            | `list_applications`, `list_databases`, `list_tables`, `get_table_schema`, `list_views`                                              |
| Build               | `create_database`, `create_table` (with initial fields), `update_table`                                                             |
| Fields and formulas | `create_fields`, `update_fields` — formula fields are how it writes formulas from a description                                     |
| Rows                | `list_table_rows`, `create_rows`, `update_rows`                                                                                     |
| Views               | `create_view` (grid, gallery, form, kanban), `add_view_filter`, `add_view_sort`                                                     |
| Automations         | `create_automation`, `create_workflow`, `describe_automation_step`, `get_workflow`, `add_automation_step`, `update_automation_step` |
| Application builder | `create_builder_application`, `list_pages`, `create_page`, `add_page_content`, `add_table_to_page`, `add_form_to_page`              |
| Needs approval      | `delete_table`, `delete_fields`, `delete_rows`, `delete_view`, `delete_page`, `delete_automation_step`, `publish_workflow`          |

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
gets content (headings, text, links, images from plain text), a table of a
database table's rows, or a form whose submissions create rows. Each builds the
data source, elements and workflow actions it needs through the permission-checked
builder services, following the builder's own sample-app initializer. Form inputs
match the field type (text, email, number, long text, checkbox, date, choice);
fields a form cannot set are reported back. Publishing an app to a domain stays a
manual step in the app's settings.

The user's open table and view are sent with each message, so "this table" works.
Answers are Markdown and follow the user's language (Arabic by default).

Compared with the Baserow AI features this was modelled on:

| Baserow                            | Sanad                                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| Kuma: build tables and fields      | Yes                                                                            |
| Kuma: formulas from a description  | Yes, as a chat request that creates or updates a formula field                 |
| Kuma: views, filters, sorts        | Yes (create view, add filter, add sort; not grouping yet)                      |
| Kuma: chat history                 | Yes, per user and workspace                                                    |
| Kuma: build applications           | Yes: pages with content, tables of rows and forms that save rows               |
| Kuma: build automations            | Yes: triggers, actions and publishing (with approval)                          |
| Kuma: search the documentation     | Not yet — answers come from the model's own knowledge                          |
| AI field                           | Not yet (a separate field type)                                                |
| "Generate using AI" formula button | Not yet (the chat covers the use case)                                         |
| Configure generative AI            | Reuses the instance-level provider settings; workspace-level keys stay removed |

## Configuration

Sanad has no credentials of its own. It uses the providers the instance already
configures for generative AI, and offers every enabled model in the panel:

| Provider   | Variables                                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------------------------- |
| OpenAI     | `JADAWEL_OPENAI_API_KEY`, `JADAWEL_OPENAI_MODELS`, optional `JADAWEL_OPENAI_BASE_URL`, `JADAWEL_OPENAI_ORGANIZATION` |
| Anthropic  | `JADAWEL_ANTHROPIC_API_KEY`, `JADAWEL_ANTHROPIC_MODELS`                                                              |
| Mistral    | `JADAWEL_MISTRAL_API_KEY`, `JADAWEL_MISTRAL_MODELS`                                                                  |
| OpenRouter | `JADAWEL_OPENROUTER_API_KEY`, `JADAWEL_OPENROUTER_MODELS`                                                            |
| Ollama     | `JADAWEL_OLLAMA_HOST`, `JADAWEL_OLLAMA_MODELS` — keeps all data on your own servers                                  |

`*_MODELS` is a comma-separated list. With nothing configured the panel explains
which variables to set, and the API answers `ERROR_SANAD_NO_MODEL_AVAILABLE`.
Use a model with reliable tool calling; small local models often call tools badly.

Workspace-level AI keys were removed on purpose (PATCHES.md, _Remove workspace AI
keys_), so there is deliberately no per-workspace setting.

## How it works

```
panel ──POST message──▶ API ──on commit──▶ Celery `arabase.sanad.run_turn`
  ▲                                                │ pydantic-ai agent + tools
  └──── polls GET chat every 1.5 s ◀──── message status / actions saved per tool
```

- **Backend** — `backend/src/arabase/sanad/`: `models.py` (`SanadChat`,
  `SanadMessage`), `tools.py`, `agent.py`, `handler.py`, `tasks.py`; API in
  `backend/src/arabase/api/sanad/` under `/api/arabase/sanad/`; migration
  `arabase/0019_sanad_chat`.
- **Model** — core's `generative_ai_model_type_registry` returns a pydantic-ai model
  for the chosen provider; pydantic-ai runs the tool loop.
- **Tools** — most are the fork's MCP tools, called with the chat user so their
  service layer applies that user's permissions and workspace scope. They are called
  directly, not through the MCP registry's interceptor, because protected-field
  policies belong to an MCP endpoint and a chat has none. View, filter and sort
  tools use the same action types as the UI, so undo works.
- **Turns run in Celery** (`celery` queue, 5-minute limit, at most 25 model
  requests per turn). A turn stuck `pending` for 10 minutes is marked failed so the
  chat is usable again.
- **Frontend** — `web-frontend/modules/arabase/sanad/`: a sidebar item and a panel
  rendered in core's right sidebar through `ArabasePlugin`'s
  `getSidebarWorkspaceComponents` / `getRightSidebarWorkspaceComponents` hooks. No
  core component was edited.

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

- `backend/tests/arabase/test_sanad_apps.py` — automation and builder tools, plus
  two whole turns whose results are then used for real: the published workflow
  fires on a new row, and the generated form's submit action creates a row.
- `backend/tests/arabase/test_sanad.py` — access rules, full turns against a
  scripted pydantic-ai `FunctionModel`, view tools, cross-workspace isolation, the
  approval pause, failure handling.
- `web-frontend/test/unit/arabase/sanad.spec.js` — staff-only visibility for Sanad,
  the builder and automation, plus the panel's send, poll and approve flow.
