---
name: forms
title: Forms — Form views that collect rows
description: Building or changing a Form view (نموذج) — a form whose every submission adds a row to a table — its questions, order, required answers, conditions, the message after submitting and its public link. Load before you create or change a form view.
---

# Forms (نموذج)

A Form view is a table's front door: each submission becomes one new row. A
good form asks only what the table needs, in the order a person thinks about
it, in their language, and tells them clearly what happens next.

## 1. Which form

- **Form view** (this skill) — the fastest way to collect rows: a page with
  questions, a public link, and nothing to publish. Use it for sign-ups,
  requests, surveys, applications, feedback, orders.
- **Builder form** (`app-builder`, `add_form_to_page`) — only when the form
  must live inside an application with its own pages, menu and theme.

Never build a form with `create_view` type `form`: that view starts with every
field turned off and asks nothing. Use `create_form`.

## 2. Plan the table first

The form can only ask fields that exist, so shape the table before the form
(`get_table_schema`, then `create_fields`):

| The person answers | Field type | Notes |
|---|---|---|
| a name, a short answer | `text` | the primary field is usually the name |
| a long answer | `long_text` | |
| an email, a phone, a link | `email`, `phone_number`, `url` | validated as typed |
| a number, an amount | `number` (`number_decimal_places`) | |
| a date | `date` | |
| yes / no, consent | `boolean` | |
| one choice | `single_select` | `style: "radios"` shows every option at once |
| several choices | `multiple_select` | `style: "checkboxes"` |
| a rating | `rating` | |
| a file, a photo, a CV | `file` | |
| a record from another table | `link_row` | the visitor picks from that table's rows |

**Cannot be asked** — they are computed or filled in by Jadawel: formula,
lookup, count, rollup, created on, last modified, created by, last modified by,
autonumber, UUID. `create_form` without `questions` reports them in
`skipped_fields`; naming one in `questions` is refused. Add a status or a
"received on" field as a computed or default-valued field instead of a question.

**A link field shows the linked table on the public form.** The visitor picks
from that table's rows by their primary field, so anyone with the link can read
those names. Link to a table of choices (products, branches, courses), never to
a table of people or private records; use a single select when the list is
short and fixed.

## 3. Build it in one call

```json
create_form({
  "table_id": 12,
  "name": "طلب تواصل",
  "title": "تواصل معنا",
  "description": "نرد خلال يوم عمل واحد.",
  "submit_text": "أرسل",
  "success_message": "شكرًا لك! وصلنا طلبك.",
  "questions": [
    {"field_id": 101, "label": "الاسم الكامل", "required": true},
    {"field_id": 102, "label": "البريد الإلكتروني", "required": true},
    {"field_id": 103, "label": "كيف عرفتنا؟", "style": "radios"},
    {"field_id": 104, "label": "من أين تحديدًا؟",
     "show_when": [{"field_id": 103, "type": "single_select_equal", "value": "أخرى"}]},
    {"field_id": 105, "label": "رسالتك", "description": "بإيجاز، من فضلك."}
  ]
})
```

- `questions` is the whole form, in order. Fields left out are not asked (they
  stay empty on the new row). Omit `questions` to ask every field that can be
  asked, in the table's order — fine for a quick form, rarely the best one.
- `label` is what the visitor reads; the field keeps its own name. Write labels
  as questions or clear prompts in the user's language; `description` adds help
  under the question.
- `title` and `description` sit at the top. `description` and
  `success_message` are plain text: line breaks are kept, Markdown is shown as
  typed, so write no `**` or `#`.
- After submitting, show `success_message`, or send the visitor to
  `redirect_url` (a full `https://` address; `{row_id}` in it becomes the new
  row's ID). Give one or the other.

`create_form` returns the form as `get_form` reads it — check it.

## 4. Required answers and conditions

- `required: true` makes the form refuse to submit without an answer.
- `show_when` shows a question only when its conditions match answers to
  **earlier** questions (a condition on a later question is refused). All must
  match; `show_when_any: true` shows it when any one does.
- Condition types are the view filter types for that field: `equal`,
  `not_equal`, `contains`, `empty`, `not_empty`, `higher_than`, `lower_than`,
  `boolean` (value `"1"` or `"0"`), `single_select_equal`,
  `single_select_not_equal`, `multiple_select_has`, `date_is`… A select
  condition takes the option's text (`"أخرى"`); it is stored as the option's ID.
- **A conditional question is only required in the browser.** The server
  cannot know whether it was shown, so it accepts a submission without it. Do
  not rely on a conditional required answer for anything that must be there.

## 5. Change a form

`get_form` first: it returns the settings, the questions in order with their
labels, required flags, styles and conditions, and `not_asked` (with
`cannot_be_asked` when a field can never be a question).

`update_form` changes any setting you pass and leaves the others. Passing
`questions` **replaces them all**: send the full list, in order, including the
questions you keep unchanged. To add a question, send the current list with the
new one in its place.

## 6. Share it

A form is private until its public link is on. `share_form` turns it on and
returns `public_url`; it pauses for the user's approval, because anyone with
the link can then add rows. Only call it when the user asked to publish or
share the form, then give them the link.

The user can add a password, change the link, or turn it off from the form's
**Share** button. Links can prefill or hide answers:

- `?prefill_<field name>=<value>` fills an answer in (`+` for a space in the
  name): `…/form/abc?prefill_Source=Web`.
- `?hide_<field name>` hides a question; combined with a prefill it records a
  fixed value, e.g. which campaign the link was sent in.

## 7. What happens to a submission

Each submission is an ordinary new row: it appears in the table's views, and
"rows are created" automations and webhooks run on it. Suggest one when it
helps — a confirmation email, a notification, a status set to "New" (load the
`automations` skill). Answers are saved as typed; a form cannot compute or
clean them, so put that logic in formula fields or an automation.

## 8. Arabic

Write the title, labels, descriptions, button text and messages in the user's
language, Arabic by default, with Western digits (0–9). Keep option texts in
conditions exactly as they are in the field.
