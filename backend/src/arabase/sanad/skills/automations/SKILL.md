---
name: automations
title: Automations — efficient, reliable workflows that fit the app
description: Designing, building, testing or fixing automations — triggers, row actions, loops, branches, schedules, emails and webhooks. Load before you create or change a workflow, or when one "does not work".
---

# Automations

An automation is part of the application, not a gadget bolted onto it. Before
you build one, understand the data model it acts on, what already happens
automatically (formula fields, other workflows), and what the business event
really is. Every workflow you build must be correct for bulk changes, cheap to
run, safe against loops, tested on a real row, and easy for a person to read.

## 1. Decide whether it should be an automation at all

- **Derived values are not automations.** Totals, statuses computed from other
  fields, days overdue, full names: use formula, lookup or count fields. They
  are always right, cost nothing and never fail. Automate only *events*: create
  or change other rows, notify someone, call a service, act on a schedule.
- **One workflow per business event** ("a new team member joins"), not one per
  field. Before adding a workflow, call `list_applications` and `get_workflow`
  on existing automations: two workflows reacting to the same table can
  conflict or double-act.
- Ask one short question only if the event, the target table or the outcome is
  unclear; otherwise build.

## 2. Building blocks

Call `describe_automation_step` for a type's exact settings before you use it.

### Triggers (first step, no `after_step_id`)

| Type | Fires when | Key settings |
|---|---|---|
| `local_jadawel_rows_created` | rows are added | `table_id` |
| `local_jadawel_rows_updated` | rows change — **any field, no field filter** | `table_id` |
| `local_jadawel_rows_deleted` | rows are deleted | `table_id` |
| `periodic` | on a schedule | `interval` MINUTE, HOUR, DAY, WEEK or MONTH; `minute` (0-59), `hour` (0-23, **UTC**: 09:00 Riyadh is `hour: 6`), `day_of_week` (0 = Monday), `day_of_month` |
| `http_trigger` | a system calls the webhook URL | `exclude_get` |

`integration_id` is filled in automatically.

### Actions (each after the previous step: `after_step_id`)

| Type | Does | Key settings |
|---|---|---|
| `local_jadawel_create_row` | adds a row | `table_id`, `field_mappings` |
| `local_jadawel_update_row` | changes a row | `table_id`, `row_id` (formula), `field_mappings` |
| `local_jadawel_delete_row` | deletes a row | `table_id`, `row_id` |
| `local_jadawel_get_row` | reads one row | `table_id`, `row_id` or `view_id`/`search_query` |
| `local_jadawel_list_rows` | reads many rows | `table_id`, `view_id`, `default_result_count` |
| `local_jadawel_aggregate_rows` | one number (sum, count…) | `table_id`, `view_id`, `field_id`, `aggregation_type` |
| `router` | branches on conditions | `edges` [{`label`, `condition`}], `default_edge_label` |
| `iterator` | repeats steps per item | `source` (a list formula) |
| `smtp_email` | sends an email | `use_instance_smtp_settings: true`, `to_emails`, `subject`, `body`, `body_type` |
| `http_request` | calls an API | `http_method`, `url`, `headers`, `body_type`, `body_content`, `timeout` |
| `slack_write_message` | posts to Slack | needs a Slack connection the user adds in the editor |
| `ai_agent` | asks an AI model | needs an AI connection the user adds in the editor |

**List, get and aggregate steps have no filter setting of their own: they
filter through a view.** Create a view with `create_view` and
`add_view_filter` (e.g. "Overdue, not done"), then pass its `view_id`. Name it
for the automation ("Automation – overdue tasks") so nobody edits it by accident.

### Field mappings

`field_mappings` items are `{field_id, value, enabled: true}`; the value is a
runtime formula (load the formulas skill for anything beyond simple paths).
The step you get back names the field behind every mapping — check that each
name is the one you meant. Value rules per field type:

- text: `'Welcome'` or `concat('Onboarding: ', get('…'))`
- number: a number or a formula that yields one
- single select: an existing option's **exact text**, e.g. `'High'`
- link to another table: row IDs, e.g. `get('previous_node.<trigger id>.0.id')`
- date: `datetime_format(today(), 'YYYY-MM-DD')` or a date read from a row
- boolean: `true` / `false`

## 3. Reading data between steps

| You want | Path |
|---|---|
| a field of the (first) row a row trigger or list step returned | `get('previous_node.<step id>.0.field_<field id>')` |
| that row's ID | `get('previous_node.<step id>.0.id')` |
| every value of a field from a list step | `get('previous_node.<step id>.*.field_<field id>')` |
| a field of a get_row step | `get('previous_node.<step id>.field_<field id>')` |
| the number an aggregate step computed | `get('previous_node.<step id>.result')` |
| inside an iterator: the current row's field | `get('current_iteration.<iterator id>.item.<Field Name>')` — **the field's name, not field_<id>** |
| inside an iterator: its position | `get('current_iteration.<iterator id>.index')` |
| a single select's text | append `.value` |
| linked rows' names / IDs | append `.*.value` / `.*.id` |

Loop items are addressed by field name, so renaming that field breaks the step:
say so to the user when you build a loop.

## 4. Rules that make workflows correct and efficient

1. **Bulk changes arrive as one run.** When several rows are created or updated
   together (paste, import, `create_rows` with many rows), the trigger fires
   once with all of them. A step reading `….0.field_…` only handles the first.
   When each row needs its own action, add an `iterator` with `source`
   `get('previous_node.<trigger id>')` and put the per-row steps inside it:
   `add_automation_step` with `inside_step_id` for the first, `after_step_id`
   for the next ones.
2. **Never create a loop.** A `rows_updated` workflow that updates the same
   table triggers itself again. If you must write back to the watched table,
   put a `router` first that only continues when the change still needs doing
   (e.g. "Status is not yet Notified"), and set that marker in the same update.
   Prefer writing to another table.
3. **Respect the limits.** Each workflow may run at most 10 times in 5
   seconds, 30 times in 5 minutes and 100 times an hour; further runs are
   refused. After more than 5 consecutive failed runs a live workflow is
   **disabled**. Design for batches (iterators, periodic summaries) rather
   than a run per keystroke.
4. **Filter early, act late.** Use a view on list steps and a router before
   expensive or external steps (emails, HTTP) so they run only when needed.
5. **Be idempotent on schedules.** A periodic job that sends reminders must
   mark what it handled (a "Reminded on" date or a checkbox) and its view must
   exclude marked rows, or it will send the same reminder every time.
6. **Guard arithmetic.** In step formulas a division by zero fails the whole
   run, and `if()` evaluates both branches: keep the divisor non-zero —
   `get('a') / if(get('b') = 0, 1, get('b'))`.
7. **Messages are for people.** Format money with `number_format(x, 2)`, dates
   with `datetime_format(…, 'DD/MM/YYYY')`, and write emails in the user's
   language. Say who receives them.

## 5. Branches with a router

```
add_automation_step type=router after_step_id=<prev>
  settings={"default_edge_label": "Other",
            "edges": [{"label": "Urgent",
                       "condition": "get('previous_node.<t>.0.field_<p>.value') = 'Urgent'"}]}
```

The result lists each edge with its `uid`. Attach a step to a branch with
`after_step_id=<router id>` and `branch=<edge uid>`; omit `branch` for the
default ("Other") branch. Edges are checked in order. To change a condition,
send the edges again with the same labels: their uids are kept.

## 6. Procedure

1. `get_table_schema` for every table involved; note field IDs, types and
   select options. `list_table_rows` to see real values.
2. Plan in one short message: trigger → steps → what each writes, and how bulk
   changes and loops are handled.
3. `create_automation` (or `create_workflow` in an existing automation), then
   the trigger, then each action. Read every step result: mapped field names,
   settings, errors. Fix before moving on.
4. `get_workflow` to review the whole graph.
5. Publishing makes it act on real data: call `publish_workflow` only when the
   user asked or agreed; it waits for their approval. The editor's version is a
   draft; **only the published copy runs**, a few seconds after its trigger.
   After any change, publish again.
6. Test with one clearly labelled row ("Test – please delete") only if the user
   agrees, then `get_workflow_runs`. `started` means queued or running: check
   again. Read `error` and each step's error, fix, republish, retest.
7. Report: what triggers it, what it does, how bulk and repeats are handled,
   the test result, and any test rows the user may want to delete.

## 7. Worked example — onboarding task for every new team member

Tables: Team (Name `field_363`), Tasks (Task Title 379, Assignee 381 → link
to Team, Priority 382 single select Urgent/High/Medium/Low, Status 383, Due
Date 384).

1. Trigger `local_jadawel_rows_created` on Team → id T.
2. `iterator` after T, `source` `get('previous_node.T')` → id L (several people
   may be imported at once).
3. Inside L, `local_jadawel_create_row` on Tasks with mappings:
   379 `concat('Onboarding: ', get('current_iteration.L.item.Name'))`,
   381 `get('current_iteration.L.item.id')`, 382 `'Medium'`,
   383 `'Not Started'`, 384 `datetime_format(today(), 'YYYY-MM-DD')`.
4. Check the returned mapping names (Assignee, not Priority), `get_workflow`,
   publish with approval, test one member, `get_workflow_runs`.

## 8. When a workflow "does not work"

| Symptom | Likely cause → fix |
|---|---|
| no run at all | not published, trigger on another table, workflow disabled after repeated errors, or rate limited → `get_workflow`, `get_workflow_runs`, republish |
| run stays `started` | still queued or running → wait and check again |
| "not a valid select option" | mapping sends text that is not an option, or the wrong field → use an option's exact text; check field names |
| value is empty | wrong path, `field_<id>` inside an iterator (use the field name), or wrong step ID |
| only one of many rows handled | bulk change read with `.0.` → add an iterator |
| runs forever / rate limited | the workflow updates the table it watches → router guard or another table |
| "division by zero" | runtime division → non-zero divisor |
| email not sent | instance email not configured → tell the user; don't retry blindly |
