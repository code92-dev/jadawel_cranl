---
name: dashboards
title: Dashboards — creative, decision-ready dashboards
description: Designing, building or changing dashboards and their widgets — key numbers, charts, targets, lists, agendas and text sections — their size, colour, icon and number format, or explaining what a dashboard can show. Load before you create or change a dashboard.
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

## 2. The board

Dashboards are applications of the workspace. Each widget owns its data: a
table, optionally a **view** (whose filters, and for lists its sort, apply),
and its own settings. A `text` widget has no data.

**A 12-column grid.** `width` is columns out of 12, `height` is rows of about
88 px, both 1–12.

| Width | Share of the row | Height | Fits |
|---|---|---|---|
| 3 | a quarter — four in a row | 1 | a section heading |
| 4 | a third — three in a row | 2 | a key number, a progress bar or a note |
| 6 | half | 3 | a gauge, a small chart |
| 8 | two thirds | 4 | a chart |
| 12 | the full row | 5–6 | a list or an agenda |

- Widgets flow in the order you add them, left to right in English and right
  to left in Arabic, and a narrow widget fills a gap an earlier wide one left.
  **Add them in reading order**; you cannot reorder them afterwards (the user
  can, by dragging in edit mode). Changing `width`/`height` with
  `update_dashboard_widget` is how you rearrange.
- Widths in a row should add up to 12, or the row ends with a hole.
- Each type has a smallest size; a smaller one is drawn at that size anyway:
  summary and progress 2×2, chart 3×3, upcoming_dates 3×3, records_list 4×3,
  text 2×1.
- On a phone the board is one column: every widget takes the full width and
  keeps its height.

Sharing through a public link is done by the user from the dashboard's menu.
Readers see when the numbers were fetched and can refresh them.

## 3. Appearance — every widget

`appearance` is how a widget looks; pass only what you want, and on update
only what changes (it is merged, so a new `suffix` keeps the `color`).

| Key | Values | Used by |
|---|---|---|
| `color` | `primary` (the workspace colour), `blue`, `cyan`, `green`, `yellow`, `red`, `magenta`, `purple`, `neutral` | icon chip; chart series; section bar; callout tint |
| `icon` | `coins`, `cash`, `wallet`, `bank`, `credit-card`, `cart`, `shop`, `box-iso`, `truck`, `graph-up`, `graph-down`, `percentage`, `user`, `group`, `user-crown`, `building`, `calendar`, `clock`, `hourglass`, `check-circle`, `warning-triangle`, `triangle-flag`, `trophy`, `star`, `rocket`, `light-bulb`, `help-circle`, `task-list`, `headset-help`, `mail`, `phone`, `globe` | summary, lists, note, callout |
| `prefix`, `suffix` | up to 12 characters: `ر.س`, `SAR`, `%`, `يوم`, `$` | summary, progress, chart |
| `decimals` | 0–4 (leave out for automatic) | summary, progress, chart |
| `compact` | `true`: 1.6M / 1.6 مليون instead of 1,610,000 | summary, progress, chart |
| `stacked` | `true`: several series stacked in one bar or area | chart with 2+ series |

- **Icons.** A key number shows no icon unless you give one. Give every
  summary an icon that names what it counts — `coins` for money, `group` for
  people, `warning-triangle` for what is late, `check-circle` for what is
  done. Lists and notes take one too (`task-list`, `calendar`).
- **Units.** Put the unit in `suffix` (or `prefix`), not only in the title:
  it is printed beside every value, and axis ticks leave it off so they stay
  short. Use `compact` for amounts in the hundreds of thousands and above —
  a long number shrinks to fit its card, a compact one stays large.
- **Colour means something.** One colour per theme — money `blue`, risk
  `red`, done `green`, time `yellow` — not a rainbow; `red` and `yellow` read
  as warnings. Charts start from **blue** when no colour is set; `primary`
  follows the workspace theme, which may be grey, so name a colour when it
  matters.
- A colour or icon outside these lists is ignored.

## 4. The widgets

### summary — one key number
`field_id` + `aggregation_type`:

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

Plain numbers get thousands separators and the widget's number format;
currencies, durations, dates and percentages keep their field's own format.
With no `description`, a caption says what is counted ("Sum of Budget"), so
use the description for what the caption cannot say: the period, the rule.

### chart — a breakdown or a trend
`chart_type`, `group_by_field_id` (one field: its values become the
categories), `series` 1–5 items `{field_id, aggregation_type, label, color}`,
`sort` (`value_desc`, `value_asc`, `label_asc`, `label_desc`), `show_legend`.

| `chart_type` | Best for |
|---|---|
| `bar` | comparing a few categories |
| `horizontal_bar` | rankings and long names — projects, clients, products |
| `line` | a trend over time buckets |
| `area` | a total over time, or its parts with `stacked` |
| `doughnut` | parts of a whole, ≤ 6 categories; shows the total in the middle |
| `pie` | the same without the total |

- Categories come from one field's values: single select, text, number,
  boolean, date. **Date fields group by day.** At most 100 categories are
  drawn (the largest first unless you sort otherwise). Linked records and
  multiple selects cannot be grouped directly — see the techniques below.
- Pie and doughnut slices take the single select's own option colours; bars
  and lines take the widget's `color`, then the palette for further series.
  A series `color` (`#rrggbb`) overrides both.
- Pie and doughnut list every slice beside the chart with its value and
  share. Bar, line and area show a legend only for 2+ series — so give each
  series a `label`.
- Long category names wrap onto two lines; beyond ~28 characters they are
  cut — prefer `horizontal_bar` for them.

### progress — a number against a target
`field_id` + `aggregation_type` as in summary, `target_value` (> 0, = 100%),
`display_style` (`bar`, `ring` or `gauge` — a half dial, best at 3×3),
`warning_threshold` and `success_threshold` (percentages; warning ≤ success).
It shows its state in words beside the title — below warning **At risk**,
from warning **On track**, from success **Target met** — and the bar marks
where "at risk" ends. The value and target both take the number format, so a
`suffix` of `ر.س` reads "1.3M ر.س of 2M ر.س".

### records_list — the latest rows
`field_ids` (up to 6, in order), `row_count`. Order and filter come from the
view: pass a `view_id` sorted by date, newest first. Cells render by type —
select options as coloured pills, numbers aligned — and **the first field
gets the widest column**: put the row's name first. The header counts the
rows and links to the table.

### upcoming_dates — an agenda
`date_field_id` (a date, created-on or last-modified field), `days_ahead`
1–365, `include_overdue`, `field_ids` (up to 6), `row_count`. Each row is a
date tile, **the first of `field_ids` as its title** and the rest as one line
of details, grouped Overdue / Today / Next 7 days / Later with "in 3 days" or
"2 days ago". The overdue count sits in the header.

### text — a section heading, a note or a callout
No table. `title`, `body` (plain text up to 2,000 characters, line breaks
kept, no Markdown) and `text_style`:
- `section` — a heading on the board itself (no card) with a bar in the
  widget's `color`; `width: 12`, `height: 1`, a short `body` as its subtitle.
- `note` — a card explaining how to read the numbers; `height: 2`–`3`.
- `callout` — a tinted card for what needs attention; blue with a light bulb
  unless you set `appearance.color` and `icon`.

## 5. One call per widget

Give `add_dashboard_widget` everything the widget needs in the same call —
never create a bare widget and patch it setting by setting. A widget missing
what its type needs is refused with the list of what is missing (every type
but `text` needs `table_id`). Examples:

```
{"dashboard_id": 7, "type": "text", "text_style": "section",
 "title": "الأداء", "body": "حتى نهاية الشهر", "width": 12, "height": 1}

{"dashboard_id": 7, "type": "summary", "title": "قيمة الصفقات المفتوحة",
 "description": "الصفقات غير المغلقة", "width": 3, "height": 2,
 "appearance": {"icon": "coins", "color": "blue", "suffix": "ر.س",
                "compact": true},
 "table_id": 55, "view_id": 85, "field_id": 437, "aggregation_type": "sum"}

{"dashboard_id": 7, "type": "progress", "title": "هدف الربع",
 "width": 3, "height": 2, "table_id": 55, "view_id": 86, "field_id": 437,
 "aggregation_type": "sum", "target_value": 500000, "display_style": "bar",
 "warning_threshold": 60, "success_threshold": 100,
 "appearance": {"suffix": "ر.س", "compact": true}}

{"dashboard_id": 7, "type": "chart", "chart_type": "horizontal_bar",
 "title": "القيمة حسب العميل", "width": 8, "height": 4, "table_id": 55,
 "group_by_field_id": 440, "sort": "value_desc",
 "series": [{"field_id": 437, "aggregation_type": "sum", "label": "القيمة"}],
 "appearance": {"suffix": "ر.س", "compact": true}}

{"dashboard_id": 7, "type": "chart", "chart_type": "doughnut",
 "title": "الصفقات حسب المرحلة", "width": 4, "height": 4, "table_id": 55,
 "group_by_field_id": 438, "sort": "value_desc",
 "series": [{"field_id": 436, "aggregation_type": "count", "label": "صفقات"}]}

{"dashboard_id": 7, "type": "upcoming_dates", "title": "تُغلق قريبًا",
 "width": 4, "height": 5, "table_id": 55, "date_field_id": 439,
 "days_ahead": 30, "include_overdue": true, "field_ids": [436, 438],
 "appearance": {"icon": "calendar"}}

{"dashboard_id": 7, "type": "records_list", "title": "أحدث الصفقات",
 "width": 8, "height": 5, "table_id": 55, "view_id": 87,
 "field_ids": [436, 438, 437], "row_count": 8,
 "appearance": {"icon": "task-list"}}

{"dashboard_id": 7, "type": "text", "text_style": "callout",
 "title": "كيف تُقرأ هذه اللوحة",
 "body": "الأرقام تُحدَّث مباشرة من جدول الصفقات.\nالصفقة المتأخرة: تجاوزت تاريخ الإغلاق.",
 "width": 12, "height": 2}
```

Create the helper fields and views first, in as few calls as you can, then
add the widgets one call each. A 10-widget dashboard should take about 15
tool calls in total.

## 6. Creative techniques

Charts and numbers are limited to one table, one grouping and simple
aggregations. Creativity is in preparing the data so a simple widget tells a
rich story. Adding a helper field or view changes the user's table, so mention
it in your plan; name helpers clearly ("Month", "Is overdue").

1. **Views as lenses.** One table can feed many widgets through views: "This
   month", "Open", "Won", "Overdue". A summary of `count` on the "Overdue" view
   is a sharper number than a count of everything.
2. **Time buckets.** Dates group by day; for a monthly trend add a formula
   field `datetime_format(field('Date'), 'YYYY-MM')` and chart it as a `line`
   or `area` with `sort: label_asc`. Weeks:
   `datetime_format(field('Date'), 'IYYY-IW')`. Quarters:
   `concat(year(field('Date')), '-Q', ceil(month(field('Date')) / 3))`.
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
   budget vs spent (sum of each) — show variance at a glance. Label each, and
   colour the actual strongly and the plan muted (`#97a394`).
7. **Parts over time.** An `area` chart with `stacked` and one series per
   part (a boolean or select turned into sums by helper formulas) shows the
   total and its make-up at once.
8. **Pareto.** A `horizontal_bar` sorted `value_desc` of amount by customer
   shows where most value comes from.
9. **Targets that mean something.** Progress for goals with a real number
   (monthly sales, collections, capacity). Set thresholds from the business:
   warning at 60%, success at 100% is a sensible default. A `gauge` makes the
   single most important target the eye-catcher of its row.
10. **An agenda beats a list.** For deadlines, use upcoming_dates with
    `include_overdue` rather than a records list.
11. **Averages lie; medians don't.** For response times, deal sizes or prices
    with a few extreme values, show `median` (and maybe `max`), not `average`.
12. **Say how to read it.** A `note` or `callout` naming the rules — what
    counts as late, where the numbers come from — saves the reader a question.

## 7. Choosing the right widget

| Question | Widget |
|---|---|
| How many / how much in total? | summary (count, sum) |
| What share? | summary (checked_percentage of a boolean formula) or doughnut |
| Are we on track? | progress (`bar` in a row of numbers, `gauge` to stand out) |
| How is it changing over time? | line or area by a month/week bucket, `label_asc` |
| Which category is biggest? | bar, `value_desc` |
| Who or what ranks first? | horizontal_bar, `value_desc` |
| Part of a whole, ≤ 6 categories | doughnut (shows the total) or pie |
| Compare plan and actual | bar with two labelled series |
| What happened last? | records_list on a view sorted newest first |
| What is due soon? | upcoming_dates |
| What is this part of the board about? | text `section` |
| How do I read this board? / What needs attention? | text `note` / `callout` |

Avoid pies with more than 6 categories or negative values, line charts over
categories that are not time, and a sum of a field that is not a number.

## 8. Layout

A proven shape, top to bottom:

1. **Section heading** (`text`, `section`, 12×1) — what this part answers.
2. **The headline:** four key numbers or progress bars, 3×2 each (or three at
   4×2). The most important first — it sits at the start of the row (the
   right, in Arabic).
3. **Section heading.**
4. **The story:** a trend or ranking (8×4) beside a breakdown (doughnut, 4×4).
5. **Section heading.**
6. **The action:** records_list (8×5) beside upcoming_dates (4×5), or 6 + 6.
7. Optionally a `callout` or `note` (12×2) on how to read it.

- Keep each row's widgets the same height, and widths adding up to 12.
- Titles are short and specific ("Revenue this month"); the unit goes in
  `suffix`, the period or rule in the description. Write everything in the
  user's language, Arabic by default, with Western digits.
- 6–9 data widgets is plenty; section headings and notes do not count. More
  is noise.

## 9. Procedure

1. `get_table_schema` and `list_table_rows` on the source tables: know the
   field types, the select options and what real values look like.
2. Tell the user your plan in a short list: the questions, the widgets that
   answer them in layout order, and any helper fields or views you will add.
3. Add helper fields (`create_fields`) and views (`create_view`,
   `add_view_filter`, `add_view_sort`) first.
4. `create_dashboard`, then `add_dashboard_widget` **in reading order**, sized
   and styled in the same call. Each result has `shows_now`: what the widget
   displays right now. **Read it.** An error, an empty result or an
   implausible number means the setup is wrong: fix it with
   `update_dashboard_widget` before moving on. Cross-check one headline
   number with `list_table_rows` or common sense.
5. `get_dashboard` with `preview: true` for a final review: every row adds up
   to 12, every number has its unit and icon, nothing is empty.
6. Report in the user's language: the dashboard's name, what each section
   answers, helper fields and views you added, and that they can drag widgets
   to rearrange them, resize them from the corner in edit mode, and share the
   dashboard from its menu.

## 10. Mistakes to avoid

- A `sum` or `average` on a text field is rejected — pick a number field.
- `target_value` must be greater than 0; `warning_threshold` must not exceed
  `success_threshold`.
- A chart grouped by a raw date field shows one bar per day; bucket by month.
- More than 100 categories are cut off; group by something coarser.
- The old three-column sizes (`width` 1–3) are now a twelfth to a quarter of
  the row: a key number is `width: 3`, not `1`.
- A unit only in the title leaves bare numbers in tooltips and legends; set
  `suffix`.
- `stacked` does nothing with one series, and on pie or doughnut.
- Widgets that read a shared, everyday view change when someone edits that
  view; make dedicated views for the dashboard.
- Deleting a widget needs the user's approval (`delete_dashboard_widget`);
  prefer `update_dashboard_widget` to fix one.
