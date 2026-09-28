# Application builder redesign — canvas, gallery and themes (2026-09-28)

The application builder ("تطبيق") still looked like upstream: the page edited
in a white box on white, a grey grid of unlabelled icons to add an element, a
bare "+" on an empty page, and published apps in upstream's stock theme — blue
buttons with 4 px corners, square black-bordered tables and inputs, Inter with
no Arabic letters, every alignment on the left. This redesign gives the builder
the same design as the redesigned dashboards (`docs/DASHBOARD_REDESIGN.md`) and
is built the same way: fork stylesheets that restyle core's classes, fork
components, a few logged core patches, and the fork's own data and tests.

It follows the same rules for the identity: white surfaces on a quiet page,
8 px controls and 12 px cards, one accent for actions, state never shown by
colour alone, Western digits. The editor's accent is the interface colour a
workspace picks (`$color-primary-*`), as on the dashboards; a published app's
colours come from its theme.

## The canvas

- **A surface of its own.** The page is edited on a pale surface with a faint
  dot grid, not on the side panel's white.
- **A browser window.** The page sits in a window: a title bar with three dots,
  the page's address in a pill (`/projects/:id` with its parameter fields), the
  "view as" user, rounded corners and a soft shadow. The address always reads
  left to right.
- **Device frames.** Tablet and phone previews get a dark bezel and rounded
  corners. The device switch is one segmented control.
- **Header and footer** are marked by a dashed rule and a pill label.
- **Selection.** Pointing at an element outlines it with a dashed line — only
  the innermost element, so nested containers don't stack outlines. The
  selected element gets a 2 px outline with a soft halo, its name in a pill,
  purple for elements shared by several pages (header, footer) as upstream.
- **A floating toolbar.** Duplicate, select parent, move, drag and delete sit in
  a dark pill, so it reads as the editor's and not part of the page; its
  tooltips match. "Insert above / below" are accent buttons on the outline.
- **Editor UI keeps the interface's direction.** The empty state, name tags,
  toolbar and header/footer labels are drawn inside the page, which now has a
  direction of its own (see _Page direction_); they are pinned to the
  interface's.

### Empty page

A sketch of a finished page (header band, hero, a row of cards), one button to
the gallery and quick starts — Heading, Text, Columns, Table, Form — that
create the element in one click. It still accepts an element dragged in from
the header or the footer, as core's "+" zone did.

## The element gallery

"Add new element" is the dashboards' widget gallery: a search field and the
elements by what they are for — **Text and media**, **Data**, **Layout**,
**Navigation and actions**, **Forms** — each with a preview drawn in the
dashboard tiles' style and one line on when to use it ("Rows as cards: design
one, it repeats for each row"). Previews mirror in Arabic. An element that
cannot go where the gallery was opened is dimmed, with the reason as its
tooltip. A type added upstream later still appears, in core's category with
core's image.

| Section                | Elements                                                                |
| ---------------------- | ----------------------------------------------------------------------- |
| Text and media         | heading, text, image, rating, iframe                                    |
| Data                   | table, repeat                                                           |
| Layout                 | columns, container, multi-page header, multi-page footer                |
| Navigation and actions | menu, link, button                                                      |
| Forms                  | form, text input, choice, checkbox, date, record selector, rating input |

## Themes

### Presets

Theme settings open with **ready-made themes**: complete looks applied in one
click and one request, drawn in their own colours on the card (header, title,
text, button, link, table). Every value stays editable in the tabs below, which
re-read the theme after a preset; "Undo" puts the previous values back.

| Preset              | Look                                                      | For                     |
| ------------------- | --------------------------------------------------------- | ----------------------- |
| **Jadawel** (جداول) | the product's sage on a quiet page — the dashboards' look | the default             |
| **Ocean** (محيط)    | the logo's blue `#0059FC`                                 | brand-facing apps       |
| **Heritage** (تراث) | deep green and gold on warm paper                         | public services         |
| **Sand** (رمال)     | terracotta and teal on sand                               | people-facing apps      |
| **Stone** (حجر)     | steel navy on cool grey                                   | finance and back office |

What a preset sets: the six theme colours; the page colour; Inter for every
text style; a type scale of 32 / 24 / 19 / 16 / 14 / 13 px with bold to medium
weights, headings in ink and body text a step lighter; buttons with 8 px
corners, 10 × 18 px padding and a darker hover and press; links in the accent,
underlined only when pointed at; images with 12 px corners; inputs with 8 px
corners and a fine border; tables as a card — 12 px corners, a quiet tinted
header, row lines and no column lines, 12 × 16 px cells.

Every preset is light, and every primary carries its button text at WCAG AA
(4.5:1) or better (tested). A dark preset was tried and dropped: an element
keeps the colours it was given one by one — a white card stays white — so a
dark page strands every such element as a white block.

**Content language.** A preset is applied for the language the app's content
is written in: _Arabic_ aligns headings, text, buttons, images and tables to
the right and lays the page out right to left; _English_ the other way.
Switching the language of an app that still matches a preset re-applies it.

**New apps** start from the Jadawel preset, aligned for the language of the
person who creates them (`arabase/builder/signals.py`, on
`application_created`). Duplicates, imports and template installs keep the
theme they were made with.

The presets live in `backend/src/arabase/builder/theme_presets.py`; the
frontend reads the same data from
`web-frontend/modules/arabase/builder/themePresets.json`, generated from it
(`PYTHONPATH=src python -m arabase.builder.theme_presets > …`). A backend test
fails when the two drift.

### Page direction

Theme → Page has a new **Direction**: _Automatic_ (upstream's behaviour — the
page follows each visitor's interface language), _Right to left_ or _Left to
right_. Automatic laid an English app out right to left for an Arabic visitor,
with its punctuation on the wrong side; an app now says what it is written in.
It is a new theme property, `page_direction` (migration `builder.0071`,
default `auto`, so existing apps don't change), read as `--page-direction` by
`.page`. Dropdowns and menus a page opens are drawn outside it and still follow
the visitor's language.

### Arabic in Inter

Inter has no Arabic letters, and upstream wrote the font stack as
`"Inter","sans-serif"` — a quoted generic is a font called "sans-serif", which
does not exist — so Arabic text in an app fell back to whatever the system had.
Sans-serif families now fall back to IBM Plex Sans Arabic, the face the app
already ships for its own interface, then to the real generic family:
`"Inter","IBM Plex Sans Arabic",sans-serif`. One family serves both scripts,
as in the rest of Jadawel.

### Box styles

A container's Style panel (container, columns, repeat, form) opens with four
box styles in one click: **Plain** (upstream's defaults), **Card** (the
theme's surface, a 1 px border in the theme's border colour, 12 px corners,
24 px padding), **Tinted** (8 % of the primary colour, no border) and
**Outlined**. They set the element's ordinary `style_*` values, so every field
below stays editable; the one an element still matches is marked.

## Published elements

`builder_elements.scss` adds what a theme cannot express, reading the app's own
theme variables so it works with any theme: a table row under the pointer is
tinted with the accent; table cells use tabular figures; buttons and inputs
get a focus ring in their colour and short transitions; links place their
underline below the descenders; headings balance their lines and paragraphs
avoid orphans.

## Sanad

- `update_app_theme` takes `preset` (`jadawel`, `ocean`, `heritage`, `sand`,
  `stone`) and `content_language` (`ar`, `en`); `settings` apply on top.
- `add_page_element` and `update_page_element` take `box_style` (`card`,
  `tinted`, `outlined`, `plain`), computed from the app's theme by
  `arabase/builder/box_styles.py` exactly as the Style panel computes them, so
  a card Sanad builds shows as "Card" in the editor. Explicit `style_*`
  settings win over it.
- The app-builder skill starts every app from a preset for its content
  language and keeps Inter for Arabic. It lists the elements in the gallery's
  groups and lays pages out as the dashboards do: sections of a level-2
  heading and a sentence, rows of `card` boxes, a `tinted` hero (headings keep
  the theme's ink, so never on a solid primary background), key facts as small
  cards on detail pages, `tinted` callouts. It keeps pages light and changes
  the look through the theme and box styles, not one-off colours.

## Where the code is

| Piece                                                    | Path                                                                                                          |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Canvas, chrome, gallery, empty page, presets, box styles | `web-frontend/modules/arabase/assets/scss/builder_canvas.scss`                                                |
| Published element finish, page direction                 | `web-frontend/modules/arabase/assets/scss/builder_elements.scss`                                              |
| Gallery sections and previews                            | `web-frontend/modules/arabase/builder/elementGallery.js`, `assets/images/elements/`                           |
| Presets, box styles                                      | `web-frontend/modules/arabase/builder/{themePresets,elementQuickStyles}.js`                                   |
| Components                                               | `web-frontend/modules/arabase/builder/components/`                                                            |
| Core components patched                                  | see `PATCHES.md`, "Application builder redesign"                                                              |
| Presets, box styles, new-app theme                       | `backend/src/arabase/builder/`                                                                                |
| Tests                                                    | `backend/tests/arabase/test_builder_{theme_presets,box_styles}.py`; `web-frontend/test/unit/arabase/builder/` |

## Not done

- **Section templates** (a hero, a row of cards, a stats row inserted as a set
  of elements) would make pages quicker to build than element by element.
- **A theme-aware surface colour** for element backgrounds: element colours
  are hex values or the six theme colours, so a card cannot follow a later
  change of theme, which is also what rules out a dark preset.
- **Key numbers on pages** like the dashboards' — a builder element type of its
  own.
- **The riyal sign** is not substituted in app content: text on a published
  page is the author's, unlike a dashboard's unit settings.
