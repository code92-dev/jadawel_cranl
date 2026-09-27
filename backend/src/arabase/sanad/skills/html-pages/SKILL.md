---
name: html-pages
title: Pages (صفحة) — hand-written HTML pages on a table's live data
description: Writing, redesigning or fixing a Page view (صفحة) — the HTML page a table shows from its own rows, which the user names by its number ("page 91") — or creating new ones. Load before you create, read or write a page.
---

# Pages (صفحة)

A Page view is a table view whose content is one HTML document you write. It
receives the view's rows live, runs in a sealed sandbox, and can be shared on a
public link. Nothing in Jadawel limits how it looks: you are the designer and
the front-end engineer. Build what a senior product designer would ship for
that exact reader — a team directory, a KPI board, a monthly report, a
profile sheet, a timeline, a poster — with real data, flawless in Arabic and
English, and correct to the last number.

## 1. Which page

- **The page's number is its view ID.** Its setup panel shows it; the user
  says "page 91" / "الصفحة رقم 91". When the user is on a Page view, the chat
  context carries its `view_id`: "this page" means that one.
- A new page: `create_page_view(table_id, name)`. Asked for several pages,
  create each one. Choose the table whose rows the page is about.
- Not to be confused with application pages (`create_page`), which belong to
  the application builder.

## 2. Tools

| Tool | Use |
|---|---|
| `get_page_view` | fields (with select options), `row_count`, `truncated`, 5 sample rows exactly as the page receives them, the current HTML |
| `create_page_view` | a new page on a table; returns the same as `get_page_view` |
| `write_page_view` | the whole document; the old one is kept as a revision |
| `edit_page_view` | exact find/replace edits for small changes (a colour, a heading) |
| `list_page_view_revisions`, `restore_page_view_revision` | undo |

Writes return `warnings`: misspelt field names, blocked network calls,
external files, left/right CSS. **Fix every warning before you report.** A
page under MCP data protection returns `awaiting_approval`: the user approves
it in the page's settings.

Rows can be narrowed with `add_view_filter` / `add_view_sort` on the page's
own `view_id`: the page then receives only those rows, in that order.

## 3. The sandbox

- Write a complete document: `<!doctype html><html>…</html>`. Jadawel injects
  its security policy and the `window.jadawel` runtime into `<head>`; it also
  sets `html, body { margin: 0 }`.
- **No network**: `fetch`, XHR, WebSocket are blocked. **No storage**:
  `localStorage`, cookies throw. **No navigation**: links out, `window.open`
  and forms do nothing. Keep state in variables; tabs, filters and search
  happen inside the page.
- **No external files** unless the user turned on external resources for the
  page (`allow_external_resources` in `get_page_view`): no CDN libraries, web
  fonts or remote images. Inline all CSS and JS, draw charts and icons with
  inline SVG, use system fonts. Photos from file fields do not load either:
  use initials avatars.
- The frame grows with `<body>`'s height by itself. Read-only: a page cannot
  change rows; point the user at a form view for that.

## 4. The data

```js
window.jadawel.onData(({ fields, rows, view }) => render(rows, view))
```

`onData` runs when the rows arrive and again on every refresh: render
everything inside it, never at load.

- `fields`: `[{ id, name, type, order }]`.
- `rows`: `[{ id, order, values, raw }]`; `values['Field name']` (exactly the
  names `get_page_view` lists), `raw['field_<id>']`.
- `view`: `{ id, name, count, rowLimit, truncated, locale, dir }`. `count` is
  every row in the view; `rows` holds at most `rowLimit`.

| Field type | Value |
|---|---|
| text, long text, email, phone, url | string or `null` |
| number, formula number, count, rollup | **string** (`"1250.50"`) — `parseFloat` it |
| boolean | `true` / `false` |
| date, created/modified on | ISO string `"2026-01-31"` or `"2026-01-31T09:00:00Z"` |
| single select | `{ id, value, color }` or `null` |
| multiple select | `[{ id, value, color }]` |
| link to table | `[{ id, value }]` (value = the linked row's name) |
| file | `[{ url, visible_name, thumbnails }]` |

Any value can be `null`. Read the sample rows before you write code.

## 5. Procedure

1. `get_page_view` (or `create_page_view`). Read fields, types, options,
   `row_count` and the sample.
2. Decide the reader and the 2–4 things the page must make obvious. For a
   loose request ("make it nice"), choose the page genre that fits the data:
   people → directory; amounts and statuses → KPI board; dates → timeline or
   agenda; one record type with rich fields → profile cards.
3. Tell the user the plan in 2–4 lines, then write the full document with
   `write_page_view` in one call.
4. Read `warnings`; fix with `edit_page_view` (or rewrite). Check that every
   `values['…']` name is in the field list.
5. Report in the user's language: what the page shows, how to use its
   controls, and that the view's **Share** button gives a public link with an
   optional password. Public visitors see every field the page receives.

## 6. Starter

Adapt freely; keep the helpers. It escapes every value, parses numbers,
formats with Western digits and handles every value shape.

```html
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root { --ink:#1e293b; --muted:#64748b; --line:#e2e8f0; --bg:#f8fafc;
  --card:#fff; --brand:#0f766e; --radius:14px; }
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink);
  font: 15px/1.7 system-ui, "Segoe UI", Tahoma, "Noto Sans Arabic", Arial, sans-serif; }
.wrap { max-width: 1120px; margin-inline: auto; padding: 32px 24px 48px; }
.grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
.card { background: var(--card); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 20px; }
.muted { color: var(--muted); }
</style>
</head>
<body>
<main class="wrap" id="app"><p class="muted">…</p></main>
<script>
const $ = (s) => document.querySelector(s)
const esc = (v) => String(v ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])
const num = (v) => { const n = parseFloat(v); return Number.isFinite(n) ? n : 0 }
const fmt = (n, d = 0) => n.toLocaleString('en-US',
  { minimumFractionDigits: d, maximumFractionDigits: d })
const sep = () => (document.documentElement.dir === 'rtl' ? '، ' : ', ')
const text = (v) => v == null ? '' : Array.isArray(v) ? v.map(text).filter(Boolean).join(sep())
  : typeof v === 'object' ? String(v.value ?? v.visible_name ?? '')
  : typeof v === 'boolean' ? (v ? '✓' : '') : String(v)
const HUES = { blue: '#2563eb', cyan: '#0891b2', green: '#16a34a', yellow: '#ca8a04',
  orange: '#ea580c', red: '#dc2626', pink: '#db2777', purple: '#7c3aed',
  brown: '#92400e', gray: '#64748b' }
const hue = (o) => HUES[String((o && o.color) || 'gray').split('-').pop()] || HUES.gray
const groupBy = (rows, name) => rows.reduce((m, r) => {
  const k = text(r.values[name]) || '—'; (m[k] ||= []).push(r); return m }, {})
const day = (iso) => (iso ? iso.slice(0, 10).split('-').reverse().join('/') : '')

window.jadawel.onData(({ rows, view }) => {
  $('#app').innerHTML = `
    <h1>${esc(view.name)}</h1>
    ${view.truncated ? `<p class="muted">${fmt(view.rowLimit)} / ${fmt(view.count)}</p>` : ''}
    <section class="grid">${rows.map((r) => `
      <article class="card">…${esc(text(r.values['Name']))}…</article>`).join('')}
    </section>`
})
</script>
</body>
</html>
```

**Always `esc()` a value you put in HTML**; row text can contain `<`.

## 7. Design at master level

- **Hierarchy first.** One clear title and a one-line subtitle (what, for
  whom, as of when). Then the headline numbers, then the detail. The eye
  should know where to go in one second.
- **Type scale:** 30–36 px title (weight 700), 20–22 px section headings,
  15–16 px body, 12–13 px labels in `--muted`. Line-height 1.6–1.8 for Arabic.
  Never letter-space Arabic. Numbers in KPIs: 28–40 px, weight 700,
  `font-variant-numeric: tabular-nums`.
- **Spacing:** an 8 px scale (8, 16, 24, 32, 48). Generous white space around
  sections; tight inside a card.
- **Colour:** one brand colour, neutrals for everything else, and the
  options' own colours (`hue(option)`) for statuses, as a soft tinted pill:
  background `color-mix(in srgb, ${c} 14%, white)`, text `c`. Contrast at
  least 4.5:1 for text.
- **Surfaces:** white cards on a faint background, 1 px border or a very soft
  shadow (`0 1px 2px rgb(0 0 0 / .06)`), radius 12–16 px. Consistency beats
  decoration.
- **People:** initials avatars — a circle with the first letters of the first
  and last name on a colour derived from the name, so each person keeps their
  colour. In Arabic names skip the article ال (عبدالله الغامدي → ع غ).
- **Charts in inline SVG.** Bars: one `<rect>` per group, width
  `value / max * W`, label and value beside it (horizontal bars suit Arabic
  labels). Donut: a `<circle>` per slice with `stroke-dasharray` = share of
  the circumference and `stroke-dashoffset` = the running total; put the total
  in the middle. Always write the numbers next to the shapes.
- **Interaction:** a search box (`input` event, match on `text()` of the
  shown fields, case-insensitive), filter chips per option, sortable columns,
  tabs. Keep the filter state in a variable and call one `render()`. Show a
  friendly empty state ("No matches").
- **Responsive:** CSS grid with `auto-fill, minmax(…)`; tables inside a
  wrapper with `overflow-x: auto`; test in your head at 360 px and 1200 px.
- **Print** (reports): `@media print { body { background: #fff } .card {
  break-inside: avoid } .no-print { display: none } }`.
- **Motion:** at most a subtle fade or bar grow, inside
  `@media (prefers-reduced-motion: no-preference)`.

## 8. Arabic, RTL and numbers

- `dir` follows the user's language: the runtime sets `<html dir>` from
  `view.dir`. Write every rule with logical properties:
  `margin-inline-start`, `padding-inline`, `inset-inline-end`,
  `text-align: start`, `border-inline-start`. Never left/right.
- Write the page's own words in the user's language.
- **Western digits (0–9)**: format with `'en-US'`, never an `ar` locale.
  Dates as `DD/MM/YYYY` (`day()`), money as `fmt(n, 2)` plus the currency
  ("SAR" / "ر.س").
- Totals: `rows.reduce((s, r) => s + num(r.values['Amount']), 0)`, then round
  once for display. Averages over non-empty values only. A percentage checks
  the divisor is not 0. Parse dates by their parts (`'2026-01-31'.split('-')`),
  not `new Date('2026-01-31')`, which reads it as UTC.
- If `view.truncated`, say that the page shows part of the rows; never
  present a partial total as the total.

## 9. Before you say it is done

- Every field name in the code exists; no `warnings` left.
- Empty values and an empty table look intentional, not broken.
- Works right-to-left and left-to-right; nothing overflows on a phone.
- Numbers checked against `row_count` and the sample.
- Tell the user what you built and how to share it; offer one next step.
