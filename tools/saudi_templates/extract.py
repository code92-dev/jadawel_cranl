"""List the strings of a template that need a translation.

usage: python extract.py <source-slug> [<existing-map.json>]
Prints a JSON object {kind: {text: context}} of strings with no mapping yet.
"""

import copy
import json
import sys
from pathlib import Path

from common import has_letters, transform

TEMPLATES = Path(__file__).resolve().parents[2] / "backend" / "templates"


def main():
    slug = sys.argv[1]
    known = {}
    if len(sys.argv) > 2 and Path(sys.argv[2]).exists():
        known = json.loads(Path(sys.argv[2]).read_text())["strings"]
    export = json.loads((TEMPLATES / f"{slug}.json").read_text())["export"]
    found = {"schema": {}, "ui": {}, "literal": {}, "data": {}}

    def fn(kind, text, ctx):
        if has_letters(text) and text not in known:
            found[kind].setdefault(text, ctx)
        return text

    transform(copy.deepcopy(export), fn)
    seen = set()
    for kind in ("schema", "ui", "literal", "data"):
        for text in list(found[kind]):
            if text in seen:
                del found[kind][text]
            seen.add(text)
    json.dump(found, sys.stdout, ensure_ascii=False, indent=1)
    print()


main()
