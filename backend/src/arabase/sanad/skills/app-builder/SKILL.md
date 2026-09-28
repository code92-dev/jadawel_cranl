---
name: app-builder
title: Application builder — designing and building apps like a master
description: Designing or building application-builder apps — pages, layout, navigation, data on pages, forms, detail pages, headers, menus and the theme. Load before you create or change an app or any of its pages.
---

# Application builder

You design apps the way a senior product designer and front-end engineer
would: start from the people who will use the app and the data behind it, give
it a clear structure, a consistent visual system and real data on every page,
then check every page before you hand it over. An app is finished when a first
time visitor understands each page in five seconds.

## 1. Your tools

Always available:
- `create_builder_application`, `list_pages`, `create_page`, `delete_page`
- `add_page_content` — headings, text, links and images from plain text
- `add_table_to_page` — a table of a table's rows, readable columns picked for you
- `add_form_to_page`, `add_fields_to_form` — forms that save rows (linked fields
  become dropdowns of the linked table)

Available once this skill is loaded:
- `list_page_elements` — what a page holds, its header/footer and data sources
- `describe_page_element` — every element type, or one type's settings
- `add_page_element`, `update_page_element`, `delete_page_element` (approval);
  both take `box_style` — the editor's Card, Tinted, Outlined or Plain box
- `add_page_data_source` — many rows (`list_rows`) or one row (`get_row`)
- `get_app_theme`, `update_app_theme` — colours, fonts, buttons, links, inputs,
  tables

Use the intent tools for quick results (a table, a form), and the element
tools for layout and design. Call `describe_page_element` for a type before
the first time you use it.

## 2. Plan before you build

1. Read the data: `get_table_schema` for each table the app shows; note field
   IDs, types and which field names a row (the primary field).
2. Decide the audience and the jobs: "customers submit requests and follow
   them", "staff browse projects and open one".
3. Sketch the pages (3–7 is typical) and tell the user in a short list:

| Page kind | Path | Holds |
|---|---|---|
| Home | `/` | a hero (title, one sentence, 1–2 buttons), key sections |
| List | `/projects` | heading, short intro, a table or a repeat of cards |
| Detail | `/project/:id` | the one row's fields, related rows, a back link |
| Form | `/request` | heading, why/what happens next, the form |
| Thank you / help | `/about` | short text and a way back |

Paths are lowercase English words with hyphens, even in Arabic apps. A path
with `:id` declares a page parameter; `create_page` tells you how to read it:
`get('page_parameter.id')`.

## 3. Build order

1. `create_builder_application`, then `update_app_theme` with a preset and the
   content language (section 5).
2. `create_page` for every page first, so links can point to them.
3. The shell shared by all pages: a `header` (with a `menu`) and a `footer`.
4. For each page: data sources, then content top to bottom.
5. Forms with `add_form_to_page`.
6. Review each page with `list_page_elements`; fix what is off.
7. Tell the user the app is ready to preview in the editor; publishing it to
   a domain is done by the user in the app's settings.

## 4. Elements and layout

`add_page_element` takes `type`, `settings`, and optionally
`parent_element_id` (a container), `place_in_container` (a column index as
text: '0', '1'…), `before_element_id` and `box_style`.

**Formula settings.** Texts, labels, URLs and values are formulas. At the top
level of `settings`, plain text is taken literally, so `"value": "Our
projects"` works. Inside lists and objects, the formula ones are table column
`value`/`link_name`, page parameter `value` and `navigate_to_url`: quote text
`'Open'`, read data with `get('…')`, combine with `concat()`. A menu item's
`name` is plain text — write `"name": "الرئيسية"`, never `"'الرئيسية'"`.

The elements, grouped as the editor's "Add element" gallery groups them:

| Group | Type | Key settings |
|---|---|---|
| Text and media | `heading` | `value`, `level` 1–6 (one level 1 per page) |
| | `text` | `value`, `format` 'plain' or 'markdown' (lists, bold, links) |
| | `image` | `image_source_type` 'url', `image_url`, `alt_text` (always) |
| | `rating` | `value`, `max_value`, `rating_style` 'star'/'heart'/… |
| | `iframe` | `source_type` 'url' + `url`, or 'embed' + `embed`; `height` |
| Data | `table` | `data_source_id`, `items_per_page`, `fields` (columns) — or use `add_table_to_page` |
| | `repeat` | `data_source_id`, `items_per_page`; a card grid is `orientation` 'horizontal' with `items_per_row` {"desktop": 3, "tablet": 2, "smartphone": 1}, `horizontal_gap`, `vertical_gap` (px); its children form each item |
| Layout | `column` | `column_amount` 1–6, `layout_type` 'auto', '1:2', '2:1', '1:3', '3:1', '1:1:2', '2:1:1', '1:2:1'; `column_gap` (px), `alignment` 'top'/'center'/'bottom' |
| | `simple_container` | a box that groups elements; give it a `box_style` |
| | `header` / `footer` | `share_type` 'all', 'only' or 'except' with `pages`; placed on the shared page for you |
| Navigation and actions | `menu` | `orientation`, `alignment`, `menu_items` [{`type` 'link', `name`, `variant`, `navigation_type`, `navigate_to_page_id` or `navigate_to_url`, `target`}] |
| | `link` | `value` (label), `variant` 'link' or 'button', `navigation_type` 'page' + `navigate_to_page_id` + `page_parameters` [{`name`, `value`}], or 'custom' + `navigate_to_url`; `target` 'self'/'blank' |
| | `button` | runs actions the user adds in the editor; for navigation use a `link` with `variant: 'button'` |
| Forms | `form_container`, `input_text`, `choice`, `checkbox`, `datetime_picker`, `record_selector`, `rating_input` | build forms with `add_form_to_page` (section 7) rather than input by input |

### Boxes

Give boxes a **`box_style`**, the same four the editor's Style panel offers
(and marks as chosen), computed from the app's theme:

| `box_style` | Draws | Use for |
|---|---|---|
| `card` | the theme's white surface, a 1 px border, 12 px corners, 24 px padding | cards in a grid, a detail page's panels, a form's frame |
| `tinted` | a soft panel of the primary colour (8 %), no border, 24 px padding | a hero, a callout ("what happens next"), a highlighted section |
| `outlined` | a 1 px border, 12 px corners, no fill | quiet groupings, side notes |
| `plain` | no box (the element's default) | undoing a box |

`box_style` works on any element — a `text` with `tinted` is a callout — and
anything in `settings` wins over it, so `"box_style": "card", "settings":
{"style_padding_top": 32, …}` is a card with more room. Only reach for the raw
box settings to adjust one: `style_padding_top/bottom/left/right`,
`style_margin_top/bottom/left/right` (px), `style_border_<side>_size`,
`style_border_<side>_color`, `style_border_radius`, `style_background`
'none'/'color' with `style_background_color`, `style_background_radius`,
`style_width` 'full', 'full-width', 'normal', 'medium', 'small'. Colours are
the theme's names — 'primary', 'secondary', 'border', 'success', 'warning',
'error', 'transparent' — or `#rrggbbaa`; prefer the names, which follow the
theme when it changes.

### Layout, as on Jadawel's dashboards

- Use an 8-px spacing scale: 8, 16, 24, 32, 48, 64. Sections are separated by
  32–64 px; items inside a section by 8–16 px. Be consistent.
- **Sections:** a level-2 heading, one sentence under it, then the content —
  one idea per section. The preset's scale (32 / 24 / 19 / 16) keeps the steps
  clear; don't enlarge body text to make a point.
- **Cards in a row:** a `column` ('auto', 2–4 columns, `column_gap` 16–24)
  with a `simple_container` `box_style: 'card'` in each column, or a `repeat`
  whose child is a `simple_container` `box_style: 'card'` (the repeat itself
  stays plain). Inside a card: a level-3 heading, one or two lines of text, a
  link with `variant: 'button'` or `'link'`.
- **A hero:** a `simple_container` `box_style: 'tinted'`, `style_width`
  'full-width', padding 48–64: a level-1 heading, one sentence, one or two links
  with `variant: 'button'`. Headings keep the theme's ink colour, so never put
  them on a solid `primary` background.
- **Key facts on a detail page:** a `column` of 3–4 `card` containers, each a
  small `text` label ("Budget") above a level-3 `heading` reading the value.
- **A callout:** a `text` (markdown) with `box_style: 'tinted'` — for "how to
  use this page" or "what happens after you send the form".
- Put related things side by side with a `column` (e.g. `layout_type` '2:1':
  content and a side note in an `outlined` box); columns stack on phones by
  themselves.
- Keep line length readable: text blocks in `style_width` 'medium'.

## 5. The visual system (theme)

Set the theme once, before content; never style elements one by one when the
theme can do it. A new app already starts from the **Jadawel** preset, aligned
for the language of the person who created it — the same look as Jadawel's
dashboards: white cards and tables on a quiet page, 8 px buttons and inputs,
12 px tables and images, a clear type scale, the sage accent for actions.

**Start from a preset** with `update_app_theme(preset=…, content_language=…)`;
it sets colours, fonts, buttons, links, inputs, tables, images, alignment and
direction in one call. Then change only what the brief needs with `settings`
(applied on top, in the same call if you like).

| Preset | Look | Use for |
|---|---|---|
| `jadawel` | sage green on a quiet page (the default) | internal tools, anything that should feel like Jadawel |
| `ocean` | the Jadawel logo blue | product and brand-facing apps |
| `heritage` | deep green and gold on warm paper | government and public services, formal requests |
| `sand` | terracotta and teal on sand | community, hospitality, people-facing apps |
| `stone` | steel navy on cool grey | finance, reports, back-office tools |

- **Content language decides alignment and direction.** `content_language:
  'ar'` aligns headings, text, buttons, images and tables to the right and lays
  the page out right to left (`page_direction: 'rtl'`), whatever language the
  visitor's interface is in; `'en'` does the opposite. Write an Arabic app's
  content in Arabic and pass `'ar'`; never mix alignments by hand.
- **Fonts:** keep `inter`. It now falls back to IBM Plex Sans Arabic (the
  font Jadawel's own interface uses) for Arabic letters, so one family serves
  both scripts. Other fonts: `arial`, `verdana`, `tahoma`, `trebuchet_ms`,
  `times_new_roman`, `georgia`, `garamond`, `courier_new`, `brush_script_mt`.
- **Brand colour:** to match an organisation, start from the closest preset
  and set `primary_color`, `button_background_color`,
  `button_hover_background_color` (a step darker), `button_border_color` and
  `link_text_color` to its colour (`#rrggbbaa`). Keep white text only on dark
  enough colours (4.5:1 contrast); on a light brand colour set
  `button_text_color` to a dark ink.
- **All presets are light, keep pages light.** An element keeps the colours
  it was given one by one: a card's white stays white under any theme, so a
  dark page would leave white blocks. Change the look through the theme and
  the box styles, not by colouring elements.
- **Changing preset later:** `tinted` boxes were mixed from the old primary
  colour; give them `box_style: 'tinted'` again with `update_page_element` so
  they take the new one.
- **Direction on its own:** `settings: {"page_direction": "rtl"}` ('rtl',
  'ltr' or 'auto', which follows each visitor's language) fixes an app's
  direction without touching its look.
- Read the current theme with `get_app_theme` before changing parts of it.

## 6. Data on pages

- `add_page_data_source` with `kind: 'list_rows'` for many rows (optionally a
  `view_id` for filters and sort — build a view for "Open requests" rather than
  showing everything), or `kind: 'get_row'` with `row_id:
  "get('page_parameter.id')"` on a detail page. `shared: true` makes a data
  source available on every page.
- Reading data in formulas:

| Where | Formula |
|---|---|
| a field of a single-row data source | `get('data_source.<id>.field_<field id>')` |
| a field of the current row, inside a `repeat` or a table column | `get('current_record.field_<field id>')` |
| the current row's ID (for links to a detail page) | `get('current_record.id')` |
| a single select's text | add `.value` |
| linked rows' names | add `.*.value` |
| a page parameter | `get('page_parameter.<name>')` |

- **List → detail pattern:** list page with a `repeat` (cards) or table; each
  card has a `link` with `variant: 'button'`, `navigation_type: 'page'`,
  `navigate_to_page_id: <detail page>` and `page_parameters: [{"name": "id",
  "value": "get('current_record.id')"}]`. The detail page has a `get_row` data
  source on `get('page_parameter.id')` and headings/texts reading its fields,
  plus a link back to the list.
- In a table element, a column that opens the detail page is `{"name":
  "Open", "type": "link", "link_name": "'Open'", "variant": "button",
  "navigation_type": "page", "navigate_to_page_id": <id>, "page_parameters":
  [{"name": "id", "value": "get('current_record.id')"}]}`. A text column is
  `{"name": "Title", "type": "text", "value": "get('current_record.field_<id>')"}`;
  other column types: boolean, rating, tags (`values`), image, button.
- Numbers and dates in texts: format them (load the formulas skill for
  `number_format`, `datetime_format`).

## 7. Forms

`add_form_to_page` builds a complete form: the right input per field
(linked records become dropdowns of their table), required fields, a submit
button and a success message. Put a heading and one sentence before it ("We
reply within two working days"). To ask for more fields later, use
`add_fields_to_form`, never a second form. Ask only for what the process needs.

## 8. Limits — say them plainly

- Apps have **no sign-in** yet: every published page and form is public.
  Never put private or sensitive tables on a page; show a filtered view.
- Buttons that run custom actions, and publishing to a domain, are set up by
  the user in the editor.
- Images come from URLs; uploads are done in the editor.

## 9. Before you say it is done

- Every page has one level-1 heading, a clear purpose and a way back.
- The header menu reaches every top-level page; links go where they say.
- Every data element shows real rows (check with `list_page_elements` and the
  table's rows); nothing reads a field that does not exist.
- Theme set: a preset for the content's language (right to left for Arabic),
  only deliberate changes on top, readable contrast.
- Boxes are box styles — cards are `card`, heroes and callouts `tinted` — with
  no one-off colours or radii, and no heading on a solid colour.
- Forms ask only for needed fields and say what happens after submitting.
- Tell the user what you built, page by page, and to preview it.
