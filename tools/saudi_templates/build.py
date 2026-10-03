"""Build the Saudi Arabic and English editions of upstream templates.

usage: python build.py [map-name ...]   (default: every maps/*.json)

Each maps/<name>.json holds:
  source         upstream template slug in backend/templates
  slug           slug of the Arabic edition; the English one gets "-en"
  ar, en         {"name", "keywords"} of each edition
  money_fields   field names (source spelling) holding amounts in riyals
  scale          multiplier applied to money_fields cell values (optional)
  strings        {"English": "Arabic"} or {"English": ["Arabic", "English"]}
A hooks/<name>.py module with patch(payload, lang) may restructure the export.
"""

import copy
import decimal
import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path

from common import has_letters, transform

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parents[1] / "backend" / "templates"
ARABIC_CATEGORY = ["قوالب عربية", "Arabic templates"]
ENGLISH_CATEGORY = ["English Templates"]
# Latin text that stays Latin in Arabic: emails, domains, URLs, codes, extensions.
LATIN_OK = re.compile(
    r"[\w.+-]+@[\w.-]+|(https?://)?[\w-]+(\.[\w-]+)+(/\S*)?|[A-Z0-9-]+|x\d+"
)
MONEY = {"ar": ("", " ر.س"), "en": ("SAR ", "")}


def load_hook(name):
    path = HERE / "hooks" / f"{name}.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"hook_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scale_value(value, factor, places):
    if value in (None, ""):
        return value
    amount = decimal.Decimal(str(value)) * decimal.Decimal(str(factor))
    # Riyal amounts read best as whole riyals; large ones to the nearest five.
    whole = amount.quantize(decimal.Decimal(1), rounding=decimal.ROUND_HALF_UP)
    if whole >= 100:
        whole = (whole / 5).quantize(decimal.Decimal(1)) * 5
    step = decimal.Decimal(1).scaleb(-places) if places else decimal.Decimal(1)
    return str(whole.quantize(step))


def localize_numbers(export, config, lang):
    money = set(config.get("money_fields", []))
    prefix, suffix = MONEY[lang]
    for app in export:
        if app["type"] != "database":
            continue
        for table in app["tables"]:
            scaled = {}
            for field in table["fields"]:
                if field.get("date_format") == "US":
                    field["date_format"] = "EU"
                if field["name"] in money or (field.get("number_prefix") in ("$", "€")):
                    if "number_prefix" in field or field["type"] == "number":
                        field["number_prefix"] = prefix
                        field["number_suffix"] = suffix
                    if field["type"] == "number" and config.get("scale"):
                        scaled[f"field_{field['id']}"] = field.get(
                            "number_decimal_places", 0
                        )
            for row in table.get("rows", []):
                for key, places in scaled.items():
                    row[key] = scale_value(row.get(key), config["scale"], places)
            scaled_ids = {int(key[6:]) for key in scaled}
            for view in table.get("views", []):
                for flt in _all_filters(view):
                    if (
                        flt.get("field_id") or flt.get("field")
                    ) in scaled_ids and re.fullmatch(
                        r"-?\d+(\.\d+)?", str(flt.get("value", ""))
                    ):
                        flt["value"] = scale_value(flt["value"], config["scale"], 0)


def _all_filters(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "filters" and isinstance(v, list):
                yield from v
            else:
                yield from _all_filters(v)
    elif isinstance(o, list):
        for v in o:
            yield from _all_filters(v)


def saudi_phone(value, mobile=True):
    """Deterministically turn any phone number into a Saudi one."""

    digest = hashlib.sha256(str(value).encode()).hexdigest()
    digits = "".join(str(int(c, 16) % 10) for c in digest[:8])
    if mobile:
        return f"+966 5{digits[0]} {digits[1:4]} {digits[4:8]}"
    return f"+966 11 {digits[1:4]} {digits[4:8]}"


def localize_phones(export, config):
    extra = set(config.get("phone_fields", []))
    for app in export:
        if app["type"] != "database":
            continue
        for table in app["tables"]:
            keys = [
                f"field_{f['id']}"
                for f in table["fields"]
                if f["type"] == "phone_number" or f["name"] in extra
            ]
            for row in table.get("rows", []):
                for key in keys:
                    if row.get(key):
                        row[key] = saudi_phone(row[key])


def replace_domains(export, config):
    """Point sample URLs and emails at the edition's own domains."""

    domains = config.get("domains", {})
    if not domains:
        return
    for app in export:
        if app["type"] != "database":
            continue
        for table in app["tables"]:
            keys = [
                f"field_{f['id']}"
                for f in table["fields"]
                if f["type"] in ("url", "email", "text", "long_text")
            ]
            for row in table.get("rows", []):
                for key in keys:
                    value = row.get(key)
                    if isinstance(value, str):
                        for old, new in domains.items():
                            value = value.replace(old, new)
                        row[key] = value


def apply_cells(export, config, lang):
    """Overwrite cells picked by (table, field, primary value), source names."""

    cells = config.get("cells", {})
    for app in export:
        if app["type"] != "database":
            continue
        for table in app["tables"]:
            wanted = cells.get(table["name"])
            if not wanted:
                continue
            ids = {f["name"]: f"field_{f['id']}" for f in table["fields"]}
            pk = next(f"field_{f['id']}" for f in table["fields"] if f.get("primary"))
            for field_name, by_primary in wanted.items():
                for row in table.get("rows", []):
                    value = by_primary.get(str(row.get(pk)))
                    if value is None:
                        continue
                    if isinstance(value, list):
                        value = value[0] if lang == "ar" else value[1]
                    elif lang == "en":
                        # A plain string is the Arabic text; English keeps the source.
                        continue
                    row[ids[field_name]] = value


def _theme_presets():
    path = (
        HERE.parents[1] / "backend" / "src" / "arabase" / "builder" / "theme_presets.py"
    )
    spec = importlib.util.spec_from_file_location("theme_presets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flip_alignments(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k.endswith("alignment") and v in ("left", "right"):
                o[k] = "right" if v == "left" else "left"
            else:
                _flip_alignments(v)
    elif isinstance(o, list):
        for v in o:
            _flip_alignments(v)


def localize_builder(export, lang):
    """Lay builder apps out in the edition's direction (Arabic: right to left)."""

    values = _theme_presets().language_values(lang)
    for app in export:
        if app["type"] != "builder":
            continue
        app.setdefault("theme", {}).update(values)
        if lang == "ar":
            for page in app.get("pages", []) + [app.get("login_page") or {}]:
                _flip_alignments(page.get("elements", []))


def check_unique_names(export, slug):
    for app in export:
        if app["type"] != "database":
            continue
        names = [t["name"] for t in app["tables"]]
        assert len(names) == len(set(names)), (slug, "duplicate table", names)
        for table in app["tables"]:
            names = [f["name"] for f in table["fields"]]
            dupes = {n for n in names if names.count(n) > 1}
            assert not dupes, (slug, table["name"], "duplicate fields", dupes)


def build(name):
    config = json.loads((HERE / "maps" / f"{name}.json").read_text())
    source = json.loads((TEMPLATES / f"{config['source']}.json").read_text())
    hook = load_hook(name)
    strings = {}
    for included in config.get("include", []):
        strings.update(
            json.loads((HERE / "maps" / f"{included}.json").read_text())["strings"]
        )
    strings.update(config["strings"])
    tr = {
        "ar": {k: v[0] if isinstance(v, list) else v for k, v in strings.items()},
        "en": {k: v[1] for k, v in strings.items() if isinstance(v, list)},
    }
    for lang in ("ar", "en"):
        payload = copy.deepcopy(source)
        if hook and hasattr(hook, "before"):
            hook.before(payload, lang)
        apply_cells(payload["export"], config, lang)
        replace_domains(payload["export"], config)
        localize_numbers(payload["export"], config, lang)
        localize_phones(payload["export"], config)
        localize_builder(payload["export"], lang)
        table = tr[lang]
        transform(
            payload["export"],
            lambda kind, text, ctx: table.get(f"{ctx}::{text}", table.get(text, text)),
        )
        if hook and hasattr(hook, "patch"):
            hook.patch(payload, lang)
        check_unique_names(payload["export"], name)
        meta = config[lang]
        payload["name"] = meta["name"]
        payload["keywords"] = meta["keywords"]
        if meta.get("icon") or config.get("icon"):
            payload["icon"] = meta.get("icon") or config["icon"]
        payload["categories"] = (
            ARABIC_CATEGORY if lang == "ar" else ENGLISH_CATEGORY
        ) + [c for c in source["categories"] if not c.startswith("🔥")]
        slug = config["slug"] + ("" if lang == "ar" else "-en")
        ordered = {
            "jadawel_template_version": payload.get("jadawel_template_version", 1),
            "name": payload["name"],
            "icon": payload["icon"],
            "keywords": payload["keywords"],
            "categories": payload["categories"],
        }
        if payload.get("open_application") is not None:
            ordered["open_application"] = payload["open_application"]
        ordered["export"] = payload["export"]
        (TEMPLATES / f"{slug}.json").write_text(
            json.dumps(ordered, ensure_ascii=False, indent=2) + "\n"
        )
        files = TEMPLATES / f"{config['source']}.zip"
        if files.exists():
            copy_used_files(files, TEMPLATES / f"{slug}.zip", ordered["export"])
        if lang == "ar":
            report_leftovers(slug, payload["export"])


def copy_used_files(source, target, export):
    """Copy the template's file archive, keeping only files the export uses."""

    text = json.dumps(export, ensure_ascii=False)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(
        target, "w", zipfile.ZIP_DEFLATED
    ) as dst:
        for info in src.infolist():
            if info.filename in text:
                dst.writestr(info, src.read(info.filename))


def report_leftovers(slug, export):
    """Print Latin-only strings left in the Arabic edition."""

    left = {}

    def fn(kind, text, ctx):
        if (
            has_letters(text)
            and not re.search(r"[؀-ۿ]", text)
            and not LATIN_OK.fullmatch(text)
        ):
            left.setdefault(kind, {}).setdefault(text, ctx)
        return text

    transform(copy.deepcopy(export), fn)
    total = sum(len(v) for v in left.values())
    print(f"{slug}: {total} Latin-only strings left")
    leftover_file = HERE / "leftovers" / f"{slug}.json"
    leftover_file.unlink(missing_ok=True)
    if total:
        (HERE / "leftovers").mkdir(exist_ok=True)
        (HERE / "leftovers" / f"{slug}.json").write_text(
            json.dumps(left, ensure_ascii=False, indent=1)
        )


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(p.stem for p in (HERE / "maps").glob("*.json"))
    for name in names:
        build(name)
