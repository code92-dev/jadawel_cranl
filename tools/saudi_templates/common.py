"""Shared walkers for localizing bundled templates into Saudi Arabic editions.

The rule throughout: a string is only ever replaced when it is an exact key of
the template's translation map. Formulas are rewritten literal by literal, so
`field('Status')`, `lookup('Units','Name')` and `= 'Overdue'` comparisons stay
consistent with the renamed fields and select options.
"""

import re

LITERAL_RE = re.compile(r"""'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)\"""", re.S)
GET_ARG_RE = re.compile(r"get\(\s*$")
GET_CALL_RE = re.compile(
    r"get\(\s*(['\"])((?:previous_node|current_iteration)\.[^'\"]*)\1\s*\)"
)

TEXT_FIELD_TYPES = {"text", "long_text", "email", "phone_number", "url"}

# Plain (non formula) strings in builder/automation exports that carry UI text.
UI_KEYS = {
    "name",
    "label",
    "value",
    "title",
    "description",
    "text",
    "placeholder",
    "submit_button_label",
    "login_button_label",
    "link_name",
    "default_value",
    "help_text",
    "alt_text",
    "submit_text",
    "submit_action_message",
    "button_load_more_label",
    "option_name_suffix",
    "subject",
    "body",
    "from_name",
    "default_edge_label",
}

# Never touch these, even inside formula objects.
SKIP_KEYS = {
    "sample_data",
    "theme",
    "custom_code",
    "scripts",
    "custom_css",
    # Parameter names are identifiers that formulas reference.
    "query_params",
    "query_parameters",
    "page_parameters",
    "path_params",
}


def has_letters(s):
    return bool(re.search(r"[A-Za-z]", s))


def formula_literals(formula):
    """Yield (start, end, quote, content) for each string literal that is not
    the argument of get()."""

    for m in LITERAL_RE.finditer(formula):
        if GET_ARG_RE.search(formula[: m.start()]):
            continue
        quote = "'" if m.group(1) is not None else '"'
        content = m.group(1) if m.group(1) is not None else m.group(2)
        yield m.start(), m.end(), quote, content


def unescape(content, quote):
    return content.replace("\\" + quote, quote).replace("\\\\", "\\")


def escape(content, quote):
    return content.replace("\\", "\\\\").replace(quote, "\\" + quote)


def rewrite_formula(formula, tr):
    """Replace mapped literals inside a formula; return the new formula."""

    out, pos = [], 0
    for start, end, quote, content in formula_literals(formula):
        raw = unescape(content, quote)
        if raw in tr:
            out.append(formula[pos:start])
            out.append(quote + escape(tr[raw], quote) + quote)
            pos = end
    out.append(formula[pos:])
    return "".join(out)


def is_formula_obj(o):
    return isinstance(o, dict) and "formula" in o and "mode" in o


def transform(export, fn):
    """Walk a template export and pass every translatable string through fn.

    fn(kind, text, ctx) returns the replacement. kind is one of "schema"
    (table/field/view/option names), "data" (row cell text), "ui" (builder and
    automation text) or "literal" (a string literal inside a formula).
    """

    # Webhook payloads and iterator items carry rows keyed by field name, so a
    # path like get('previous_node.5.body.items.0.Status.value') names fields.
    field_names = {
        field["name"]
        for app in export
        if app["type"] == "database"
        for table in app.get("tables", [])
        for field in table["fields"]
    }

    def get_path(match):
        quote, path = match.group(1), match.group(2)
        parts = [
            fn("schema", part, "get path") if part in field_names else part
            for part in path.split(".")
        ]
        return f"get({quote}{'.'.join(parts)}{quote})"

    def formula(f, ctx, ui=False):
        if not isinstance(f, str) or not f:
            return f
        f = GET_CALL_RE.sub(get_path, f)
        out, pos = [], 0
        for start, end, quote, content in formula_literals(f):
            raw = unescape(content, quote)
            # Short codes ("S", "EXP") and intervals ("7 days") are logic.
            if raw in field_names:
                pass  # A field name, however short, must follow its rename.
            elif (
                not has_letters(raw)
                or len(raw) <= (1 if ui else 2)
                or (not ui and re.fullmatch(r"[A-Z0-9-]+", raw))
                or re.fullmatch(r"-?\d+ \w+", raw)
            ):
                continue
            new = fn("literal", raw, ctx)
            if new != raw:
                out.append(f[pos:start])
                out.append(quote + escape(new, quote) + quote)
                pos = end
        out.append(f[pos:])
        return "".join(out)

    for app in export:
        if app["type"] == "database":
            _database(app, fn, formula)
        else:
            app["name"] = fn("ui", app["name"], app["type"])
            _generic(app, fn, formula, app["type"])
    return export


def _database(app, fn, formula):
    app["name"] = fn("schema", app["name"], "database")
    for table in app.get("tables", []):
        tctx = table["name"]
        text_fields = {}
        for field in table["fields"]:
            fctx = f"{tctx}.{field['name']}"
            if field["type"] in TEXT_FIELD_TYPES:
                text_fields[f"field_{field['id']}"] = fctx
            field["name"] = fn("schema", field["name"], tctx)
            if field.get("description"):
                field["description"] = fn("ui", field["description"], fctx)
            for opt in field.get("select_options") or []:
                opt["value"] = fn("schema", opt["value"], fctx + " (option)")
            if field.get("formula"):
                field["formula"] = formula(field["formula"], fctx + " (formula)")
            for key in ("through_field_name", "target_field_name"):
                if field.get(key):
                    field[key] = fn("schema", field[key], fctx)
            if field["type"] == "text" and field.get("text_default"):
                field["text_default"] = fn("data", field["text_default"], fctx)
        table["name"] = fn("schema", table["name"], "table")
        for view in table.get("views", []):
            vctx = f"{tctx} view"
            for key in (
                "name",
                "title",
                "description",
                "submit_text",
                "submit_action_message",
            ):
                if view.get(key):
                    view[key] = fn("schema" if key == "name" else "ui", view[key], vctx)
            fo = view.get("field_options")
            if isinstance(fo, dict):
                fo = fo.values()
            for opt in fo or []:
                for key in ("name", "description"):
                    if opt.get(key):
                        opt[key] = fn("ui", opt[key], vctx + " form")
            _filters(view, fn, vctx)
        for row in table.get("rows", []):
            for key, fctx in text_fields.items():
                if isinstance(row.get(key), str) and row[key].strip():
                    row[key] = fn("data", row[key], fctx)


def _filters(o, fn, ctx):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "filters" and isinstance(v, list):
                for flt in v:
                    val = flt.get("value")
                    if isinstance(val, str) and has_letters(val) and "?" not in val:
                        flt["value"] = fn("data", val, ctx + " filter")
            else:
                _filters(v, fn, ctx)
    elif isinstance(o, list):
        for v in o:
            _filters(v, fn, ctx)


def _generic(o, fn, formula, ctx):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k in SKIP_KEYS:
                continue
            if is_formula_obj(v):
                v["formula"] = formula(v["formula"], f"{ctx}.{k}", ui=True)
            elif isinstance(v, str):
                if k in UI_KEYS and has_letters(v):
                    new = v if "get(" in v else fn("ui", v, f"{ctx}.{k}")
                    if new == v and ("'" in v or '"' in v):
                        new = formula(v, f"{ctx}.{k}", ui=True)
                    o[k] = new
            else:
                _generic(
                    v,
                    fn,
                    formula,
                    ctx
                    if k.isdigit()
                    else (
                        k
                        if k
                        in (
                            "pages",
                            "elements",
                            "workflows",
                            "nodes",
                            "data_sources",
                            "workflow_actions",
                        )
                        else ctx
                    ),
                )
    elif isinstance(o, list):
        for v in o:
            _generic(v, fn, formula, ctx)


def all_ids(o, key="id"):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key and isinstance(v, int):
                yield v
            else:
                yield from all_ids(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from all_ids(v, key)


def find_table(payload, name):
    for app in payload["export"]:
        for table in app.get("tables", []):
            if table["name"] == name:
                return table
    raise KeyError(name)


def add_field(payload, table, spec, values=None):
    """Append a field to a table; values maps row id -> cell value."""

    field = {"id": max(all_ids(payload["export"])) + 1, "primary": False}
    field["order"] = max(f["order"] for f in table["fields"]) + 1
    field.update(spec)
    table["fields"].append(field)
    for row in table.get("rows", []):
        if values and row["id"] in values:
            row[f"field_{field['id']}"] = values[row["id"]]
    return field


def formula_field(name, formula, decimals=2, suffix="", prefix=""):
    return {
        "type": "formula",
        "name": name,
        "error": None,
        "date_format": None,
        "date_include_time": None,
        "date_time_format": None,
        "number_decimal_places": decimals,
        "number_prefix": prefix,
        "number_suffix": suffix,
        "formula": formula,
        "formula_type": "number",
    }


def saudi_vat_number(seed):
    digits = "".join(str((seed * 7919 + i * 104729) % 10) for i in range(13))
    return f"3{digits}3"


def slack_to_email(app, to_formula, subject_formula, body_formula=None):
    """Turn every Slack step of an automation into an email step.

    Slack needs a bot token per workspace; the automation's SMTP integration is
    what Saudi teams already have. The email step copies the sender settings of
    an existing SMTP step and keeps the Slack text as its body.
    """

    smtp = next(i for i in app["integrations"] if i["type"] == "smtp")
    app["integrations"] = [i for i in app["integrations"] if i["type"] != "slack_bot"]
    template = next(
        n["service"]
        for w in app["workflows"]
        for n in w["nodes"]
        if n["type"] == "smtp_email"
    )
    converted = []
    for workflow in app["workflows"]:
        for node in workflow["nodes"]:
            if node["type"] != "slack_write_message":
                continue
            text = node["service"]["text"]
            service = {
                k: v
                for k, v in template.items()
                if k
                not in ("id", "subject", "body", "to_emails", "cc_emails", "bcc_emails")
            }
            empty = {**text, "formula": ""}
            service.update(
                id=node["service"]["id"],
                integration_id=smtp["id"],
                sample_data=None,
                to_emails={**text, "formula": to_formula},
                cc_emails=dict(empty),
                bcc_emails=dict(empty),
                subject={**text, "formula": subject_formula},
                body={**text, "formula": body_formula or text["formula"]},
                body_type="plain",
            )
            node["type"] = "smtp_email"
            node["service"] = service
            converted.append(node)
    return converted


def clear_sample_data(payload):
    for app in payload["export"]:
        for workflow in app.get("workflows", []):
            for node in workflow["nodes"]:
                node["service"]["sample_data"] = None
