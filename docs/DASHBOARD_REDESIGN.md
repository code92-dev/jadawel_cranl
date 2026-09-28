# Dashboard redesign — canvas, widgets and editing (2026-09-28)

The dashboards looked like a form someone had put numbers in: a white box around
a grid of identical boxes, raw numbers (`1610000`), a progress ring whose label
had a yellow block behind it and ran over the description, pie slices outlined
in blue, and a size picker that only knew thirds. This redesign gives every
widget one frame, a reason to look the way it does, and an editor that works
like a canvas.

It follows the Jadawel identity's rules for data graphics (the
`jadawel-visual-identity` skill): one accent highlights, mint/amber/coral are for
state only, labels and units stay visible, no 3D or decorative gradients, and a
state is never shown by colour alone. The accent is the product's own — the sage
brand green, which a workspace theme can change — so dashboards match the rest
of the app.

## The canvas

- **No box around the board.** The dashboard sits on the page's quiet
  background (`$palette-neutral-50`); the widgets are the only white surfaces.
  Width is capped at 1600 px.
- **A header row.** Title and description on one side; on the other, when
  reading, *Updated 10:42* and a refresh button (a dashboard left open on a wall
  screen otherwise shows the morning's figures all day). The button re-dispatches
  each data source once, on the private and the public dashboard alike.
- **A 12-column grid of 72 px rows** (16 px gaps), replacing 3 columns of 160 px
  rows. Twelve columns give the sizes dashboards are built from — four key
  numbers in a row (3 each), three (4 each), halves, two thirds — and a row short
  enough that a section heading takes one and a key number two. Widgets still
  flow in `order` with `dense` packing, which is what keeps them sane on a phone.

### Editing

- **Drag anywhere** on a widget to move it (the whole card is the handle, with a
  grab cursor); the drop target is outlined in the accent.
- **Drag the corner** to resize. It snaps to cells as the pointer moves, shows
  `6 × 4` beside the pointer, respects the widget type's minimum, mirrors in
  Arabic (the handle is at the bottom-left, dragging left widens), and saves once,
  on release. Escape cancels.
- **A floating toolbar** on hover or selection: move, size, delete. The size menu
  offers ¼, ⅓, ½, ⅔ and full widths and 1–8 rows — the keyboard-reachable way to
  the common sizes, next to the handle's any-size drag.
- **Column guides** show faintly behind the widgets while editing.
- **An "Add widget" tile** closes the grid, and the header carries the same
  button.
- **The gallery** lists every widget variation by what it is for — Numbers,
  Charts, Lists, Text and layout — with a preview and one line on when to use it.
  A widget is created at a size that suits it (a key number 3×2, a line chart
  8×4, a list 8×5, a section heading 12×1) instead of the full row.
- **Empty dashboard:** a sketch of a finished board and one button.

On screens narrower than `$dashboard-breakpoint` (900 px) the board is one column;
widgets keep their heights, and moving and resizing are off.

## The widgets

Every widget renders in **`WidgetFrame`**: an optional icon chip in the widget's
accent, the title, a one-line description, badges beside the title, and the body.
While loading it shows the title and a shimmer rather than a spinner; unset
widgets say what to do ("Select it to finish its settings" when editing), empty
ones say so with an icon.

| Widget | What changed |
|---|---|
| **Key number** (`summary`) | Upstream's summary widget, drawn by the fork. Grouped digits (`1,610,000`), optional compact notation (`1.6M`, `1.6 مليون`), fixed decimals, a unit before or after, an icon and accent. The number scales with the card (container query units). Without a description a caption says what is counted: *Sum of Budget*. |
| **Progress** | A status pill in words and an icon — *Target met*, *On track*, *At risk* — beside the title. Bar: big percentage, *1.3M of 2M*, and a tick where "at risk" ends. Ring: dial beside the value and target. New **gauge** style: a half dial. The yellow block and the overlap are gone. |
| **Chart** | Six types: bar, **horizontal bar** (rankings and long names), line, **area**, pie, doughnut. Rounded bars, no vertical grid lines, compact axis ticks, a dark tooltip, circular legend markers shown only when there is more than one series. Pie and doughnut get white separators, an HTML legend with each value and its share, and the doughnut its total in the centre; below 340 px the legend moves under the chart. Series colours start from the widget's accent. Several series can be **stacked**. |
| **Records list** | Cells by field type: select options as pills in their grid colours, linked rows as chips, people with an initial, numbers grouped and end-aligned, dates written out, a tick for booleans, stars for ratings. A sticky header, row hover, a record count and a link to open the table (or view) behind it. |
| **Upcoming dates** | An agenda: a date tile per row (day and month), the first field as the title and the rest as details, grouped *Overdue / Today / Next 7 days / Later*, with *in 3 days*, *tomorrow*, *2 days ago* counted by calendar day. Overdue and today are tinted; the overdue count sits in the header. |
| **Text** (new) | A **section heading** that splits the board (on the canvas, no card, an accent bar at its start), a **note** card explaining how to read the numbers, or a tinted **callout** with an icon. Plain text; line breaks are kept; nothing is parsed as markup. |

Arabic plurals ("3 سجلات", "بعد 11 يومًا", "بندان متأخران") go through the CLDR
categories in `core/utils/plural.js`, as elsewhere in the fork. Numbers and dates
use Western digits.

## Appearance

`Widget.appearance` is a new JSON field on the base widget: a flat dict the
frontend interprets and the API only bounds (at most 16 keys, scalar values,
strings up to 64 characters). Known keys:

| Key | Used by | Values |
|---|---|---|
| `color` | all | `primary` (the workspace colour), `blue`, `cyan`, `green`, `yellow`, `red`, `magenta`, `purple`, `neutral` |
| `icon` | key number, lists, text | 32 curated iconoir names (`dashboard/appearance.js`) |
| `prefix`, `suffix` | key number, progress, chart | up to 12 characters |
| `decimals` | key number, progress, chart | 0–4, absent for automatic |
| `compact` | key number, progress, chart | `true` for `1.6M` |
| `stacked` | bar, horizontal bar, area | `true` |

Anything else is ignored, and a colour or icon outside the lists never reaches
the page — they end up in class names, so the lists are the allow-list. The
settings panel has an **Appearance** section per widget (swatches, an icon grid,
number format, chart type tiles). Sanad chooses from the same lists
(`backend/src/arabase/dashboard/appearance.py`); `appearance.spec.js` fails if the
two drift.

## Data and compatibility

- **Migration `dashboard.0005_widget_grid_12_appearance`** multiplies every stored
  width by 4 and height by 2, so existing dashboards look the same on the new
  grid, and adds `appearance`. It is reversible (divides and rounds back into
  1–3).
- **Exports record `widget_grid_columns: 12`.** An export without it comes from
  the 3-column board and is rescaled on import the same way, so older templates
  and backups keep their layout.
- **Migration `arabase.0022`** adds the text widget and the `horizontal_bar`,
  `area` and `gauge` choices.
- The `summary` type keeps its name and API; the fork registers its own frontend
  type over upstream's, so stored widgets get the new look without a change.

## Sanad

`add_dashboard_widget` / `update_dashboard_widget` take the 12-column sizes, the
new chart types and gauge, the `text` widget (no table) and `appearance`
(merged on update, so changing a unit keeps the colour). The dashboards skill
explains the grid, the layout rows (four key numbers, a trend beside a
breakdown, lists), and when to use each new piece.

## Where the code is

| Piece | Path |
|---|---|
| Canvas, board, edit chrome, gallery, empty state styles | `web-frontend/modules/arabase/assets/scss/dashboard_canvas.scss` |
| Widget styles | `web-frontend/modules/arabase/assets/scss/dashboard_widgets.scss` |
| Frame, widgets, settings, size menu, chrome | `web-frontend/modules/arabase/dashboard/components/` |
| Grid maths, number format, appearance lists, chart theme | `web-frontend/modules/arabase/dashboard/{layout,format,appearance,chartTheme}.js` |
| Widget types and gallery metadata | `web-frontend/modules/arabase/dashboard/widgetTypes.js` |
| Core components patched | see `PATCHES.md`, "Dashboard redesign" |
| Text widget, styles | `backend/src/arabase/dashboard/widgets/` |
| Tests | `backend/tests/arabase/test_dashboard_redesign_widgets.py`, `test_widget_grid_layout.py`; `web-frontend/test/unit/arabase/dashboard/` |

## Not done

- **Free placement.** Widgets flow in order and pack densely; there is no x/y
  position, so a gap can only be closed by moving or resizing a neighbour.
- **Comparisons and sparklines** on key numbers (vs. last month, a trend line)
  need a second, date-filtered aggregation per widget.
- **Duplicating a widget** needs a backend copy of its data source.
- **Dashboard-wide filters** (a date range for every widget).
