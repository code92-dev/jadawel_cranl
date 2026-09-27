---
name: dashboards
title: Dashboards — creative, decision-ready dashboards
description: Designing, building or changing dashboards and their widgets — key numbers, charts, targets, lists and agendas — or explaining what a dashboard can show. Load before you create or change a dashboard.
---

# Dashboards

A great dashboard answers the questions its reader asks every morning, at a
glance, with numbers they trust. Be creative in *how* you reveal the story in
the data — a ratio instead of a raw count, a trend instead of a total, a
target instead of a number — but never at the cost of clarity or correctness.

## 1. Start from the reader

Before any widget, settle three things (from the request, or one short
question): **who** reads it (manager, team, finance), **what decisions** it
supports, and **what period** matters (today, this month, this quarter). Pick
3–5 questions the dashboard must answer, e.g. "Are we on target?", "Where is
work stuck?", "What is due this week?". Every widget answers one of them.

## 2. Everything a dashboard can do

Dashboards are applications of the workspace. Each widget owns its data: a
table, optionally a **view** (whose filters, and for lists its sort, apply),
and its own settings. Widgets sit on a three-column grid: `width` 1–3 (3 = full
row) and `height` 1–3. They appear in the order you add them. Sharing a
dashboard through a public link is done by the user from the dashboard's menu.

### summary — one key number
`field_id` + `aggregation_type`. Aggregations:

| Type | Meaning | Field types |
|---|---|---|
| `count` | rows | any |
| `not_empty_count`, `empty_count` | filled / empty cells | any |
| `not_empty_percentage`, `empty_percentage` | share filled / empty | any |
| `checked_count`, `not_checked_count` | ticked / unticked | boolean (incl. boolean formulas) |
| `checked_percentage`, `not_checked_percentage` | share ticked | boolean |
| `unique_count` | distinct values | text, number, select… |
| `sum`, `average`, `median`, `min`, `max` | numbers | number, formula number, rating… |
| `std_dev`, `variance` | spread | number |
| `min_date`, `max_date` | earliest / latest | date |

### chart — a breakdown or a trend
`chart_type` `bar`, `line`, `pie` or `doughnut`; `group_by_field_id` (one
field: its values become the categories); `series` 1–5 items
`{field_id, aggregation_type, label, color}`; `sort` `value_desc`,
`value_asc`, `label_asc`, `label_desc`; `show_legend`.
- Categories come from one field's values: single select (with its colours),
  text, number, boolean, date. **Date fields group by day.** At most 100
  categories are drawn (the largest first unless you sort otherwise).
- Linked records and multiple selects cannot be grouped directly — see the
  helper-field techniques below.

### progress — a number against a target
`field_id` + `aggregation_type` as in summary, `target_value` (> 0, = 100%),
`display_style` `bar` or `ring`, `warning_threshold` and `success_threshold`
(percentages; warning ≤ success). Below warning it shows at risk, from success
it shows met.

### records_list — the latest rows
`field_ids` (up to 6, in order), `row_count`. Order and filter come from the
view: pass a `view_id` sorted by date, newest first.

### upcoming_dates — an agenda
`date_field_id` (a date, created-on or last-modified field), `days_ahead`
1–365, `include_overdue`, `field_ids` (up to 6), `row_count`.

### One call per widget

Give `add_dashboard_widget` everything the widget needs in the same call —
never create a bare widget and patch it setting by setting. A widget missing
what its type needs is refused with the list of what is missing. Examples:

```
{"dashboard_id": 7, "type": "summary", "title": "Open pipeline (SAR)",
 "description": "Sum of Amount, open deals", "width": 1, "height": 1,
 "table_id": 55, "view_id": 85, "field_id": 437, "aggregation_type": "sum"}

{"dashboard_id": 7, "type": "chart", "chart_type": "doughnut",
 "title": "Deals by stage", "width": 1, "height": 2, "table_id": 55,
 "group_by_field_id": 438, "sort": "value_desc",
 "series": [{"field_id": 436, "aggregation_type": "count", "label": "Deals"}]}

{"dashboard_id": 7, "type": "progress", "title": "Quarter target",
 "width": 1, "height": 1, "table_id": 55, "view_id": 86, "field_id": 437,
 "aggregation_type": "sum", "target_value": 500000, "display_style": "ring",
 "warning_threshold": 60, "success_threshold": 100}

{"dashboard_id": 7, "type": "records_list", "title": "Latest deals",
 "width": 2, "height": 2, "table_id": 55, "view_id": 87,
 "field_ids": [436, 437, 438], "row_count": 8}

{"dashboard_id": 7, "type": "upcoming_dates", "title": "Closing soon",
 "width": 1, "height": 2, "table_id": 55, "date_field_id": 439,
 "days_ahead": 30, "include_overdue": true, "field_ids": [436, 437]}
```

Create the helper fields and views first, in as few calls as you can, then
add the widgets one call each. A 6-widget dashboard should take about 10 tool
calls in total.

## 3. Creative techniques

Charts and numbers are limited to one table, one grouping and simple
aggregations. Creativity is in preparing the data so a simple widget tells a
rich story. Adding a helper field or view changes the user's table, so mention
it in your plan; name helpers clearly ("Month", "Is overdue").

1. **Views as lenses.** One table can feed many widgets through views: "This
   month", "Open", "Won", "Overdue". A summary of `count` on the "Overdue" view
   is a sharper number than a count of everything.
2. **Time buckets.** Dates group by day; for a monthly trend add a formula
   field `datetime_format(field('Date'), 'YYYY-MM')` and chart it as a `line`
   with `sort: label_asc`. Weeks: `datetime_format(field('Date'), 'IYYY-IW')`.
   Quarters: `concat(year(field('Date')), '-Q', ceil(month(field('Date')) / 3))`.
3. **Group by a linked record.** Add a text formula
   `join(totext(lookup('Project', 'Project Name')), ', ')` and group by it:
   "tasks per project", "revenue per client".
4. **Rates from boolean formulas.** A boolean formula such as `field('Due') <
   today()` ("Is overdue") or `totext(field('Stage')) = 'Won'` ("Is won")
   turns into a percentage with `checked_percentage`: on-time rate, win rate,
   completion rate. Rates beat raw counts for decisions.
5. **Bands and tiers.** A formula like `if(field('Amount') >= 100000, 'Large',
   if(field('Amount') >= 10000, 'Medium', 'Small'))` gives a clean
   distribution chart from a continuous number.
6. **Comparison series.** Two series on one bar chart — planned vs actual,
   budget vs spent (sum of each) — show variance at a glance. Give each a
   `label` and a meaningful `color` (actual in the primary colour, plan muted).
7. **Pareto.** A bar chart sorted `value_desc` of amount by customer shows
   where most value comes from.
8. **Targets that mean something.** Progress rings for goals with a real
   number (monthly sales target, collection target, capacity). Set thresholds
   from the business: warning at 60%, success at 100% is a sensible default.
9. **An agenda beats a list.** For deadlines, use upcoming_dates with
   `include_overdue` rather than a records list.
10. **Averages lie; medians don't.** For response times, deal sizes or prices
    with a few extreme values, show `median` (and maybe `max`), not `average`.

## 4. Choosing the right widget

| Question | Widget |
|---|---|
| How many / how much in total? | summary (count, sum) |
| What share? | summary (checked_percentage of a boolean formula) or doughnut |
| Are we on track? | progress |
| How is it changing over time? | line chart by a month/week bucket, `label_asc` |
| Which category is biggest? | bar chart, `value_desc` |
| Part of a whole, ≤ 6 categories | pie / doughnut |
| Compare plan and actual | bar chart with two series |
| What happened last? | records_list on a view sorted newest first |
| What is due soon? | upcoming_dates |

Avoid pies with more than 6 categories or negative values, line charts over
categories that are not time, and a sum of a field that is not a number.

## 5. Layout

- **Row 1 – the headline:** 3 summary or progress widgets, `width: 1`,
  `height: 1`. The single most important number first.
- **Row 2 – the story:** a trend (`line`, `width: 2`, `height: 2`) next to a
  breakdown (`doughnut`, `width: 1`, `height: 2`).
- **Row 3 – the action:** records_list and upcoming_dates, `width: 1` or
  `2`, `height: 2` or `3`.
- Titles are short and specific ("Revenue this month (SAR)"). Use the
  description for the period, unit or rule ("Won deals, closed this month").
  Write them in the user's language.
- 6–9 widgets is plenty. More is noise.

## 6. Procedure

1. `get_table_schema` and `list_table_rows` on the source tables: know the
   field types, the select options and what real values look like.
2. Tell the user your plan in a short list: the questions, the widgets that
   answer them, and any helper fields or views you will add.
3. Add helper fields (`create_fields`) and views (`create_view`,
   `add_view_filter`, `add_view_sort`) first.
4. `create_dashboard`, then `add_dashboard_widget` in layout order. Each result
   has `shows_now`: what the widget displays right now. **Read it.** An error,
   an empty result or an implausible number means the setup is wrong: fix it
   with `update_dashboard_widget` before moving on. Cross-check one headline
   number with `list_table_rows` or common sense.
5. `get_dashboard` with `preview: true` for a final review of the whole set.
6. Report in the user's language: the dashboard's name, what each row answers,
   helper fields and views you added, and how to share it (dashboard menu →
   share) if they want others to see it.

## 7. Mistakes to avoid

- A `sum` or `average` on a text field is rejected — pick a number field.
- `target_value` must be greater than 0; `warning_threshold` must not exceed
  `success_threshold`.
- A chart grouped by a raw date field shows one bar per day; bucket by month.
- More than 100 categories are cut off; group by something coarser.
- Widgets that read a shared, everyday view change when someone edits that
  view; make dedicated views for the dashboard.
- Deleting a widget needs the user's approval (`delete_dashboard_widget`);
  prefer `update_dashboard_widget` to fix one.
