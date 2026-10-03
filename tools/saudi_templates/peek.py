"""Print a template's tables with select options and links resolved.

usage: python peek.py <slug> [table-name ...] [--rows N]
"""

import json
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "backend" / "templates"

args = sys.argv[1:]
limit = 40
if "--rows" in args:
    i = args.index("--rows")
    limit = int(args[i + 1])
    del args[i : i + 2]
slug, wanted = args[0], set(args[1:])
payload = json.loads((TEMPLATES / f"{slug}.json").read_text())
tables = {
    t["id"]: t
    for a in payload["export"]
    if a["type"] == "database"
    for t in a["tables"]
}


def primary(table, row_id):
    pk = next(f for f in table["fields"] if f.get("primary"))
    row = next((r for r in table.get("rows", []) if r["id"] == row_id), None)
    return row.get(f"field_{pk['id']}") if row else row_id


for table in tables.values():
    if wanted and table["name"] not in wanted:
        continue
    print(f"== {table['name']} ({len(table.get('rows', []))} rows)")
    print("   fields:", ", ".join(f"{f['name']}<{f['type']}>" for f in table["fields"]))
    for row in table.get("rows", [])[:limit]:
        out = []
        for f in table["fields"]:
            v = row.get(f"field_{f['id']}")
            if f["type"] in ("single_select", "multiple_select"):
                opts = {o["id"]: o["value"] for o in f.get("select_options", [])}
                v = [opts.get(x) for x in v] if isinstance(v, list) else opts.get(v)
            elif f["type"] == "link_row" and f.get("link_row_table_id") in tables:
                v = [primary(tables[f["link_row_table_id"]], x) for x in v or []]
            elif f["type"] == "file":
                v = [x.get("visible_name") for x in v or []]
            if v not in (None, "", [], False):
                out.append(f"{f['name']}={v}")
        print("   ", " | ".join(map(str, out))[:600])
