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
- `add_page_element`, `update_page_element`, `delete_page_element` (approval)
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

1. `create_builder_application`, then `update_app_theme` (section 5).
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
text: '0', '1'…) and `before_element_id`.

**Formula settings.** Texts, labels, URLs and values are formulas. At the top
level of `settings`, plain text is taken literally, so `"value": "Our
projects"` works. Inside lists and objects, the formula ones are table column
`value`/`link_name`, page parameter `value` and `navigate_to_url`: quote text
`'Open'`, read data with `get('…')`, combine with `concat()`. A menu item's
`name` is plain text — write `"name": "الرئيسية"`, never `"'الرئيسية'"`.

| Type | Key settings |
|---|---|
| `heading` | `value`, `level` 1–6 (one level 1 per page) |
| `text` | `value`, `format` 'plain' or 'markdown' (lists, bold, links) |
| `link` | `value` (label), `variant` 'link' or 'button', `navigation_type` 'page' + `navigate_to_page_id` + `page_parameters` [{`name`, `value`}], or 'custom' + `navigate_to_url`; `target` 'self'/'blank' |
| `image` | `image_source_type` 'url', `image_url`, `alt_text` (always) |
| `column` | `column_amount` 1–6, `layout_type` 'auto', '1:2', '2:1', '1:3', '3:1', '1:1:2', '2:1:1', '1:2:1'; `column_gap` (px), `alignment` 'top'/'center'/'bottom' |
| `simple_container` | a box; style it as a card |
| `repeat` | `data_source_id`, `items_per_page`; a card grid is `orientation` 'horizontal' with `items_per_row` {"desktop": 3, "tablet": 2, "smartphone": 1}, `horizontal_gap`, `vertical_gap` (px); its children form the card |
| `table` | `data_source_id`, `items_per_page`, `fields` (columns) — or use `add_table_to_page` |
| `header` / `footer` | `share_type` 'all', 'only' or 'except' with `pages`; placed on the shared page for you |
| `menu` | `orientation`, `alignment`, `menu_items` [{`type` 'link', `name`, `variant`, `navigation_type`, `navigate_to_page_id` or `navigate_to_url`, `target`}] |
| `iframe` | `source_type` 'url' + `url`, or 'embed' + `embed`; `height` |
| `rating` | `value`, `max_value`, `rating_style` 'star'/'heart'/… |
| `button` | runs actions the user adds in the editor; for navigation use a `link` with `variant: 'button'` |

**Box styles** apply to every element: `style_padding_top/bottom/left/right`,
`style_margin_top/bottom/left/right` (px), `style_border_<side>_size`,
`style_border_<side>_color`, `style_border_radius`, `style_background`
'none'/'color' with `style_background_color`, `style_background_radius`,
`style_width` 'full', 'full-width', 'normal', 'medium', 'small'. Colours are
`#rrggbbaa` or a theme name: 'primary', 'secondary', 'border', 'success',
'warning', 'error', 'transparent'.

**Layout rules.**
- Use an 8-px spacing scale: 8, 16, 24, 32, 48, 64. Sections are separated by
  32–64 px; items inside a section by 8–16 px. Be consistent.
- One idea per section: heading, one or two sentences, the content.
- Put related things side by side with a `column` (e.g. `layout_type` '2:1':
  content and a side note); stack everything on small screens automatically.
- Cards: a `simple_container` or a `repeat` item with `style_background`
  'color', a light background, `style_border_radius` 8–12,
  `style_padding_*` 16–24.
- A hero: `style_width` 'full-width' container with the primary colour as
  background, heading level 1, one line of text, a link with `variant: 'button'`.
- Keep line length readable: text blocks in `style_width` 'medium'.

## 5. The visual system (theme)

Set the theme once, before content; never style elements one by one when the
theme can do it. Read it with `get_app_theme`; change it with
`update_app_theme` using its property names.

- **Colour:** `primary_color` (brand, buttons, links), `secondary_color`
  (accents), `border_color`, `main_success_color`, `main_warning_color`,
  `main_error_color`, `page_background_color`. Colours are `#rrggbbaa`. Text
  must contrast with its background (at least 4.5:1): dark text on light
  backgrounds, white text only on dark primaries.
- **Palettes that work:**
  - Government / trust: primary `#0f5132ff`, secondary `#c9a227ff`, page `#f7f7f5ff`
  - Corporate teal: primary `#0f766eff`, secondary `#f59e0bff`, page `#f8fafcff`
  - Finance navy: primary `#1e3a8aff`, secondary `#0ea5e9ff`, page `#ffffffff`
  - Health / calm: primary `#0e7490ff`, secondary `#22c55eff`, page `#f0fdfaff`
- **Type:** fonts are `inter`, `arial`, `verdana`, `tahoma`, `trebuchet_ms`,
  `times_new_roman`, `georgia`, `garamond`, `courier_new`, `brush_script_mt`.
  **Inter has no Arabic letters: for Arabic apps use `tahoma` (or `arial`)
  for `body_font_family`, every `heading_N_font_family`, `button_font_family`,
  `link_font_family`, `label_font_family`, `input_font_family` and
  `table_header_font_family`.** A clear scale: `heading_1_font_size` 30,
  `heading_2_font_size` 22, `heading_3_font_size` 18, `body_font_size` 15.
- **Arabic alignment:** alignment is physical. For Arabic content set
  `body_text_alignment`, `heading_N_text_alignment`, `link_text_alignment`,
  `button_alignment`, `button_text_alignment`, `image_alignment`,
  `table_header_text_alignment` and `table_cell_alignment` to 'right' (keep
  'center' where you want it); otherwise buttons and images sit on the left.
- **Buttons and inputs:** `button_border_radius` 6–8,
  `button_vertical_padding` 10, `button_horizontal_padding` 20,
  `input_border_radius` equal to the buttons'. Consistent radii make an app
  feel designed.
- **Tables:** `table_header_background_color` a light tint of the primary,
  `table_cell_alternate_background_color` a very light grey for zebra rows.

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
- Theme set: Arabic fonts and right alignment for Arabic content, consistent
  radii and spacing, readable contrast.
- Forms ask only for needed fields and say what happens after submitting.
- Tell the user what you built, page by page, and to preview it.
