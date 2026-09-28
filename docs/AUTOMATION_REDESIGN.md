# Automation redesign — recipes, step gallery, readiness (2026-09-28)

The automation editor ("أتمتة") worked but asked a lot of its user: an empty
workflow showed "Choose an event…" and five service names; every step was the
same grey card with a small icon (a bare "+" for "rows are created"); adding a
step meant reading a flat list of seventeen service names; nothing said which
steps were still unfinished except a yellow "Configure" on each; the settings
panel did not say which step it was editing; and "Last published" was
near-white on the light header. The Arabic had literal slips — the periodic
trigger read "الزناد الدوري", a gun's trigger.

This redesign gives automations the design of the redesigned dashboards and
applications (`docs/DASHBOARD_REDESIGN.md`, `docs/APPLICATION_REDESIGN.md`),
built the same way — fork stylesheets and components, a few logged core
patches — and goes further on ease: a workflow can be built whole from a
recipe, every step speaks plainly, and the editor always says what is left to
do.

## The step catalogue

`modules/arabase/automation/stepCatalog.js` places every step type in a
category that says what it is for, with one colour per job and an icon that
shows it. The locales give each a plain-language name and a line on when to
use it; the service's own name stays the default label on the canvas.

| Category              | Colour  | Steps (plain name)                                                                |
| --------------------- | ------- | --------------------------------------------------------------------------------- |
| Table events (starts) | sage    | When a row is added · When a row changes · When a row is deleted                  |
| Schedule (starts)     | amber   | On a schedule                                                                     |
| Web (starts)          | cyan    | When a web request arrives                                                        |
| Records               | sage    | Add a row · Update a row · Find a row · Find rows · Summarise rows · Delete a row |
| Messages              | blue    | Send an email · Post to Slack (Slack's logo)                                      |
| Logic                 | purple  | Split into branches · Repeat for each item                                        |
| AI                    | magenta | Ask AI                                                                            |
| Web                   | cyan    | Call a web address                                                                |

Colour is never the only signal: every chip carries its icon and every place
that shows one also names the step. A step type added upstream later still
appears, in a fallback category with its own icon and name.

## Starting a workflow

An empty workflow opens on a **start screen** over the canvas:

**Recipes** — whole workflows for the jobs people automate most, built in one
click: the trigger and every step, in order, each named for what it does
("Every morning" → "Find the rows" → "Email the digest"). What is left is
choosing the tables and writing the message, which the canvas marks. Each card
draws its flow as step chips, a loop's steps framed inside it. They are grouped
by purpose:

| Group                | Recipe                          | Steps                                                      |
| -------------------- | ------------------------------- | ---------------------------------------------------------- |
| Tell people          | Email me when a row is added    | row added → send an email                                  |
|                      | Post new rows to Slack          | row added → post to Slack                                  |
|                      | Email when a row changes        | row changed → send an email                                |
|                      | Email the person in charge      | row added → find a row (the linked person) → send an email |
| Keep tables in order | Create a follow-up task         | row added → add a row                                      |
|                      | Archive finished rows           | row changed → add a row (archive) → delete a row           |
|                      | Keep a log of deleted rows      | row deleted → add a row                                    |
| On a schedule        | Daily digest                    | daily 08:00 → find rows → send an email                    |
|                      | Remind about overdue rows       | daily 08:00 → find rows → for each row: send an email      |
|                      | Weekly totals                   | Sunday 08:00 → summarise rows → send an email              |
|                      | Weekly summary in Slack         | Sunday 08:00 → summarise rows → post to Slack              |
| Connect and decide   | Save web requests as rows       | web request → add a row                                    |
|                      | Send new rows to another system | row added → call a web address                             |
|                      | Different steps for each status | row changed → split into branches                          |
|                      | Let AI fill in new rows         | row added → ask AI → update a row                          |

**Every event and every step is used by at least one recipe**, so each can be
met in a working flow. Two tests keep it so: `recipes.spec.js` checks the
registered step types against the recipes, and
`test_automation_step_catalog.py` checks the backend's node types against the
editor's catalogue and recipes — a type added later fails both until it is
described and has a recipe.

The scheduled recipes also set their schedule — daily at 08:00, or weekly on
Sunday (the start of the Saudi working week) at 08:00 — in the local time of
whoever builds them; the periodic trigger stores UTC, so the hour is converted
as its own form does.

A recipe is only offered when all its step types are installed. It is built
with the editor's own store actions, one step after another — a loop's steps
inside it, the next step after the loop — then named; a failure stops where it
is and leaves what was built, like steps added by hand. The trigger is selected
at the end, so its settings open first.

**Events** — every trigger as a card, grouped as Table events, Schedule and
Web, with its plain name and when it fires.

## The canvas

- **Step cards.** An icon chip in the step's category colour, the step's
  number on its corner (in reading order: a container's steps before what
  follows it, a router's branches in turn), the label and under it the step's
  plain name and category ("Add a row · Records"). A step that still needs
  setting up has an amber edge and a "Needs setup" pill whose tooltip gives the
  reason, taken from the step's own validation. The selected step has an accent
  outline and halo.
- **The readiness bar**, floating at the bottom of the canvas: a ring that
  fills as steps are set up, "2 of 4 steps set up" (or "All 4 steps are set
  up"), the workflow as a row of step chips — a dot marks each unfinished one,
  and any chip opens its step — and **Set up next**, which opens the first
  unfinished step.
- **Branch labels and connectors** in the page's quiet greys.

## Adding and replacing steps

The "+" between steps and "Replace" both open the **step gallery**: a search
field, a chip per category that jumps to it (so Messages — email and Slack —
is one click away however long the list), and the steps grouped by category,
each with its chip, plain name and one line. Search matches the plain name, the service name and both
descriptions; Enter picks the first match.

## The step panel

The settings panel opens with a header: the step's chip, "Step 2 of 4 ·
Records" (or "Starts the workflow · Table events"), its plain name and what it
does, and a status — "Set up" or the reason it is not.

## Fixes on the way

- "Last published" is readable (it was near-white on the light header).
- "Automation workflow not found." is translated.
- Arabic: "الزناد الدوري" → "جدول زمني"; "حدث الاختبار" (the test's event) →
  "اختبار الحدث"; "بدء تشغيل الاختبار" → "بدء تشغيل تجريبي"; "أثار في" →
  "وقت التشغيل".

## Where the code is

| Piece                                                   | Path                                                                                                  |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Catalogue, reading order, readiness                     | `web-frontend/modules/arabase/automation/stepCatalog.js`                                              |
| Recipes and their builder                               | `web-frontend/modules/arabase/automation/recipes.js`                                                  |
| Start screen, step gallery, readiness bar, panel header | `web-frontend/modules/arabase/automation/components/`                                                 |
| Styles                                                  | `web-frontend/modules/arabase/assets/scss/automation_canvas.scss`                                     |
| Core components patched                                 | see `PATCHES.md`, "Automation redesign"                                                               |
| Tests                                                   | `web-frontend/test/unit/arabase/automation/`; `backend/tests/arabase/test_automation_step_catalog.py` |

## Not done

- **Recipes that pick the table once** for the trigger and every step that
  uses it. Recipes set step types, names and schedules; tables, recipients and
  messages are chosen in each step.
- **Plain-language summary of settings** on the cards ("in Tasks, when Status
  changes"): each service type would need a describer.
- **Run history on the canvas** (last run's outcome per step).
