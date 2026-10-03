# Saudi template editions

Builds the Arabic (`saudi-*`) and English (`saudi-*-en`) editions of fifteen
upstream templates into `backend/templates/`. The upstream JSON stays untouched;
everything an edition changes lives here, so an upstream template update is
picked up by rebuilding.

```
cd tools/saudi_templates
python3 build.py              # every map
python3 build.py restaurant   # one map
python3 extract.py <source-slug> [maps/<name>.json]   # strings still unmapped
python3 peek.py <slug> [table ...] [--rows N]          # rows with links resolved
```

`backend/tests/arabase/test_saudi_templates.py` imports and installs every
edition; run it after a rebuild.

## How a map works

`maps/<name>.json` names the `source` slug, the edition `slug`, the `ar` / `en`
names and keywords, and `strings`: `{"English": "Arabic"}` or
`{"English": ["Arabic", "Saudi English"]}`. A string is replaced only when it
is an exact key, wherever it appears — table, field, option, view and page
names, cell text, and string literals inside formulas. One map per template
keeps a renamed field, the `field('…')` that reads it and the `= '…'` that
compares with its option in step.

Other keys:

- `include` — maps whose strings this one reuses (the same staff appear in
  several templates).
- `Table::Field` keys — a field name that differs per table.
- `cells` — `{table: {field: {primary value: text}}}` for long cells such as
  descriptions, keyed by the row's primary value in the source.
- `money_fields`, `scale` — amounts converted to riyals and rounded; filters on
  those fields scale with them.
- `domains` — sample email and URL domains to replace before translating.
- `phone_fields` — text fields holding phone numbers; `phone_number` fields are
  always replaced by Saudi mobile numbers.

`hooks/<name>.py` may define `before(payload, lang)` (source names) and
`patch(payload, lang)` (translated names) for structural changes: the Saudi
working calendar, added VAT fields, Slack steps turned into email steps, or the
automation the leave template gains.

## What the build never touches

Formula literals that are logic: one- and two-letter codes and upper-case ID
prefixes in database formulas (`EXP`, `CL`) unless they name a field, date
intervals (`'7 days'`), date formats, page paths, query-parameter names,
`get('data_source…')` paths, and the `text` / `choice` / `rating` question
types the compliance app routes on. `leftovers/<slug>.json` lists the
Latin-only strings left in each Arabic edition after a build; the expected
ones are emails, URLs, brand names, codes and HTML markup.
