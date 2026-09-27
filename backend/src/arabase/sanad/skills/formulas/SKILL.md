---
name: formulas
title: Formulas — numbers, money, dates and logic done right
description: Writing, fixing or explaining any formula — formula fields in tables, and the formulas inside automation steps and app pages. Load before you create or change a formula or answer how to calculate something.
---

# Formulas

Work like a scientist and a chartered accountant who has written formulas for
twenty years. A number is only as good as its precision, its units and its edge
cases. You never guess how an engine rounds or divides: the facts below are
tested against this engine, so rely on them, and when something is not listed
here, test it on a real row before you promise it.

## 1. Know which language you are writing

Jadawel has two formula languages. Mixing them up is the most common mistake.

| | Table formula fields | Runtime formulas (automation steps, app pages) |
|---|---|---|
| Where | a `formula` field made with `create_fields` / `update_fields` | step settings, field mappings, element values |
| Refer to data | `field('Price')`, `lookup('Link', 'Field')` | `get('previous_node.<id>.0.field_<id>')`, `get('current_record.field_<id>')`, `get('page_parameter.id')` |
| Division by zero | returns NaN (no error) | **raises an error and fails the step** |
| `round(x, n)` | half away from zero: 2.5 → 3, −2.5 → −3 | half to even: 2.5 → 2, 3.5 → 4, −2.5 → −2; floats: `round(1.005, 2)` → 1.0 |
| `round(x)` without places | not allowed — always give places | 2 places |
| Decimals | exact decimals; see precision rules | binary floats: `0.1 + 0.2` → 0.30000000000000004 |
| Display a number | the field shows its decimals; `totext()` keeps them | `number_format(x, 2)` → "1,234.50"; `concat('SAR ', 2.50)` → "SAR 2.5" |
| Operators | `+ - * / = != > < >= <=` and functions | the same operators and functions |
| `if()` guard around a division | works (the division only yields NaN) | **does not work: both branches are evaluated** |

## 2. Principles

1. **Decide the precision first.** Money in SAR has 2 decimals (KWD, BHD and OMR
   have 3). Percentages shown to 1 decimal. Quantities are whole numbers unless
   the unit says otherwise. Write the precision into the formula with `round()`.
2. **Round once, at the boundary the law or the reader cares about.** Keep full
   precision in intermediate steps and round the result. When an invoice's VAT
   is legally computed per line, round per line and sum the rounded lines;
   never sum unrounded lines and expect the same total.
3. **Guard every division.** In tables: `if(field('Qty') = 0, 0, …)` or
   `when_nan(…, 0)`. In runtime formulas the divisor itself must never be
   zero: `if(get('x') = 0, 0, get('y') / if(get('x') = 0, 1, get('x')))`.
4. **Treat blanks deliberately.** A blank number counts as 0 in arithmetic
   (`7.50 + blank` = 7.50, `7.50 × blank` = 0.00). If blank means "unknown",
   test it with `isblank()` and return blank or a label instead of a wrong 0.
5. **Never compare computed decimals for exact equality** in runtime formulas;
   compare rounded values: `round(get('a'), 2) = round(get('b'), 2)`.
6. **Name fields with their unit and meaning**: "Net (SAR)", "VAT 15% (SAR)",
   "Margin %", "Days overdue". One idea per field; build complex results from
   small, checkable helper fields.
7. **Check on real rows, including the awkward ones**: zero, blank, negative,
   very large, the last day of a month, 29 February, a date in the future. Use
   `list_table_rows` after creating the field and read the values back.

## 3. Table formula fields

### Precision rules (tested)

- `+`, `−`, `×` keep the most decimals of their inputs: `field('Price') *
  field('Qty')` with Price at 2 decimals and Qty at 0 gives 2 decimals (22.50).
- `/` always gives 10 decimals (2.5000000000). Wrap it: `round(a / b, 2)`.
- Functions such as `power` inherit the decimals of their inputs:
  `power(1.05, 12)` shows **1.80**, but `power(1.050000, 12)` shows 1.795856.
  To get more precision, write literals with more decimals, or multiply by
  `1.000000` first: `power(field('Rate') * 1.000000, 2)`.
- The number of decimals a formula field shows follows from these rules; set
  it explicitly by rounding.

### Rounding family (tested)

| Formula | Result | Use |
|---|---|---|
| `round(2.5, 0)` / `round(-2.5, 0)` | 3 / −3 | half away from zero |
| `round(1234.5, -2)` | 1200 | round to hundreds (negative places) |
| `trunc(2.789)` | 2 | drop the decimals |
| `floor(-2.5)` / `ceil(2.1)` | −3 / 3 | toward −∞ / +∞ |
| `int(7.9)` | 7 | whole part |
| `mod(10, 3)` | 1 | remainder |
| `even(x)`, `odd(x)`, `sign(x)`, `abs(x)` | | parity, sign, magnitude |

### Invalid numbers

`x / 0`, `tonumber('abc')` and `sqrt(-1)` give **NaN**, not an error.
`error_to_null()` does **not** turn NaN into blank; use `when_nan(x, 0)` or
`is_nan(x)`. Guard at the source so a NaN never reaches a total or a report.

### Functions by purpose

- Arithmetic: `add minus multiply divide power sqrt exp ln log abs sign mod
  greatest least round trunc floor ceil int even odd`
- Logic: `if and or not equal not_equal greater_than less_than … isblank
  is_null when_empty is_nan when_nan error_to_nan error_to_null`
- Text: `concat totext tonumber upper lower trim left right length contains
  search replace regex_replace split_part reverse encode_uri`
- Dates: `today now todate todate_tz datetime_format datetime_format_tz year
  month day second date_diff date_interval toseconds toduration`
- Links and lookups: `lookup count sum avg min max stddev_pop stddev_sample
  variance_pop variance_sample filter join array_unique first last
  array_length any every`
- Selects: `totext(field('Status'))` (the option text), `has_option(field('Tags'),
  'x')` for multiple selects
- Others: `row_id()`, `link(url)`, `button(url, label)`, `tourl`

### Dates (tested)

- `date_diff('dd', a, b)` counts days (b − a; negative if b is earlier).
- **`date_diff('mm', …)` and `date_diff('yy', …)` count calendar boundaries
  crossed, not whole periods**: 31 Jan → 1 Feb is 1 month; 31 Dec → 1 Jan is
  1 year. Never use them for age, tenure or "full months".
- Exact age or tenure in whole years:
  `year(today()) - year(field('Birth')) - if(datetime_format(today(), 'MMDD') <
  datetime_format(field('Birth'), 'MMDD'), 1, 0)`
- `field('Start') + date_interval('1 month')` clamps to the month's end:
  31 Jan + 1 month = 28 Feb. `field('End') - field('Start')` is a duration.
- Buckets for reports and charts: month `datetime_format(field('Date'),
  'YYYY-MM')`, ISO week `datetime_format(field('Date'), 'IYYY-IW')`, quarter
  `concat(year(field('Date')), '-Q', ceil(month(field('Date')) / 3))`,
  month name `datetime_format(field('Date'), 'Mon YYYY')`.
- Overdue days: `if(field('Due') < today(), date_diff('dd', field('Due'),
  today()), 0)`. `today()` follows the day; don't store it in a normal field.

### Lookups and linked rows (tested)

- `sum(lookup('Items', 'Amount'))`, `avg(…)`, `min(…)`, `max(…)`, `count(field('Items'))`.
- Conditional sum: `sum(filter(lookup('Items', 'Amount'), lookup('Items',
  'Amount') > 15))`.
- Names of linked rows as one text: `join(totext(lookup('Project', 'Name')), ', ')`
  — also the way to group a chart by a linked record.

## 4. Accounting recipes (tested where marked ✓)

- **VAT 15% per line** ✓: `round(field('Unit price') * field('Qty') * 0.15, 2)`;
  gross ✓ `round(field('Unit price') * field('Qty') * 1.15, 2)`; net from gross
  ✓ `round(field('Gross') / 1.15, 2)`. Keep the rate in a number field
  ("VAT rate", 0.15) when it can change, not buried in formulas.
- **Discount then VAT**: net = `round(price * qty * (1 - field('Discount %') /
  100), 2)`, VAT on the net. State the order to the user; it changes the tax.
- **Margin vs markup**: margin % = (price − cost) / price × 100; markup % =
  (price − cost) / cost × 100. They are different numbers; name which one.
- **Percentage change** ✓: `if(field('Old') = 0, 0, round((field('New') -
  field('Old')) / field('Old') * 100, 1))`. Say "percentage points" for the
  difference between two percentages.
- **Weighted average price**: `sum(lookup('Lines','Amount')) /
  sum(lookup('Lines','Qty'))` — guarded — never the average of unit prices.
- **Loan or instalment payment** ✓ (100,000 over 12 months at 0.5% a month →
  8606.64): `round(P * r / (1 - power(1 + r, -n)), 2)` with `r` written to 6
  decimals, e.g. `0.005000`.
- **Compound growth**: `round(field('Principal') * power(1 + field('Rate') *
  1.000000, field('Years')), 2)`.
- **Straight-line depreciation per year**: `round((field('Cost') -
  field('Salvage')) / field('Life years'), 2)`, guarded for 0 years.
- **Running totals and period totals are not row formulas.** A formula sees one
  row (and its links). For totals per month use a dashboard chart or an
  aggregate step; for a balance, link rows to a parent and sum the lookup.

## 5. Scientific habits

- Convert units with an explicit, named factor ("kg" = "lb" × 0.45359237).
- Report the precision the measurement supports: `round(x, 2)`, not 10 decimals.
- Clamp to a valid range: `greatest(0, least(100, field('Score')))`.
- Use median and standard deviation (dashboard aggregations) when a few
  extreme values would distort an average.
- Distinguish "no data" (blank) from "zero" in every ratio.

## 6. Runtime formulas (automations and app pages)

- Read data with `get('<path>')`. Paths: `previous_node.<step id>.0.field_<id>`
  (first row of a row trigger or list step), `previous_node.<step id>.field_<id>`
  (single-row steps), `current_iteration.<iterator id>.item.<Field Name>`
  (inside a loop over rows — the field's **name**), `current_record.field_<id>`
  (inside a table or repeat), `data_source.<id>.field_<id>` (a single-row data
  source), `page_parameter.<name>`, `form_data.<element id>`.
- A single select read from a row is an object: add `.value` for its text.
  Linked rows are lists: `.*.value` for their names, `.*.id` for their IDs.
- Literal text is quoted: `'Hello'`. Build text with `concat()`.
- Money and counts in messages: `number_format(x, 2)` → "1,234.50";
  `number_format(x, 2, ' ', ',')` → "1 234,50" (thousand then decimal
  separator; allowed: ',', '.', ' ', ''). Without places it shows 0 decimals.
- Dates: `datetime_format(get('...'), 'DD/MM/YYYY')`, `today()`, `now()`.
- Lists: `sum(get('previous_node.<id>.*.field_<id>'))`, `avg`, `join(list,
  ', ')`, `length`, `at(list, 0)`, `is_empty`.
- Functions available: `concat get add minus multiply divide equal not_equal
  greater_than less_than greater_than_or_equal less_than_or_equal upper lower
  capitalize round abs is_even is_odd datetime_format day month year hour minute
  second now today get_property random_int random_float random_bool
  generate_uuid if and or replace length contains reverse join split is_empty
  strip sum avg at to_array range to_json from_json null number_format
  to_duration duration_format to_datetime`. There is no `totext`, `tonumber`
  or `date_diff` here; those belong to table formulas. Put heavy arithmetic in
  a table formula field and read its result with `get()`.
- Comparisons do not convert types: `equal(7, '7')` is false, though `'7' + 3`
  is 10.

## 7. Procedure

1. Read the table with `get_table_schema`; note field types and decimals.
2. Say, in one line, what the formula computes and to what precision.
3. Create or update the field with `create_fields` / `update_fields`
   (`{"type": "formula", "formula": "…"}`), or set the runtime formula.
4. Read results back (`list_table_rows`, `get_workflow_runs`) and check one row
   by hand. If a value is NaN, blank or has 10 decimals, fix it before you
   report success.
5. Tell the user the rule you applied (rounding, VAT order, blank handling).

## 8. Fixing a broken formula

| Symptom | Cause and fix |
|---|---|
| NaN | division by zero or bad `tonumber` → guard with `if` / `when_nan` |
| 10 decimals | a division → `round(…, n)` |
| too few decimals (1.80) | inputs' precision → literal with more decimals |
| wrong month or year count | `date_diff('mm'/'yy')` counts boundaries → use the age recipe or days |
| step fails "division by zero" | runtime divide → keep the divisor non-zero |
| step writes nothing | wrong path or field ID → `get_workflow` names every mapped field |
| "Unsupported function" in a step | a table-only function (e.g. `totext`) in a runtime formula |
| select shows `[object]` or an ID | read `.value` of the option |
