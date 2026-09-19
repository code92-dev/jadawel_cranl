"""Build an interactive HTML node explorer from graft/.graph/wiring.json.

Writes .scratch/graft-vis/index.html (self-contained: the graph is embedded).

    python3 .scratch/graft-vis/build.py
"""

from __future__ import annotations

import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "graft", ".graph", "wiring.json")
OUT = os.path.join(ROOT, ".scratch", "graft-vis", "index.html")

KINDS = ["file", "class", "method", "function", "type"]
RELS = ["contains", "calls", "imports", "extends", "references"]
SPAN_RE = re.compile(r"L(\d+)-L(\d+)")


def parse_span(span: str | None) -> tuple[int, int]:
    if not span:
        return (-1, -1)
    m = SPAN_RE.match(span)
    if not m:
        return (-1, -1)
    return (int(m.group(1)), int(m.group(2)))


def main() -> int:
    print(f"reading {SRC} ...", flush=True)
    with open(SRC) as fh:
        graph = json.load(fh)

    nodes = graph["nodes"]
    edges = graph["edges"]
    meta = graph["meta"]

    files: list[str] = []
    file_ix: dict[str, int] = {}
    names: list[str] = []
    name_ix: dict[str, int] = {}
    syms: list[list[int]] = []          # [nameIdx, fileIdx, kindIdx, start, end]
    node_sym: dict[str, int] = {}       # node id -> symbol index
    node_file: dict[str, int] = {}      # node id -> file index

    for n in nodes:
        path = n["path"]
        fi = file_ix.get(path)
        if fi is None:
            fi = len(files)
            file_ix[path] = fi
            files.append(path)
        node_file[n["id"]] = fi
        if n["kind"] == "file":
            continue
        nm = n["name"]
        ni = name_ix.get(nm)
        if ni is None:
            ni = len(names)
            name_ix[nm] = ni
            names.append(nm)
        start, end = parse_span(n.get("span"))
        node_sym[n["id"]] = len(syms)
        syms.append([ni, fi, KINDS.index(n["kind"]), start, end])

    flinks: collections.Counter[tuple[int, int]] = collections.Counter()
    slinks: list[list[int]] = []
    for e in edges:
        rel = e["relation"]
        if rel == "contains":
            continue
        sf = node_file.get(e["source"])
        tf = node_file.get(e["target"])
        if sf is None or tf is None:
            continue
        if sf != tf:
            flinks[(sf, tf)] += 1  # file graph is cross-file only
        s = node_sym.get(e["source"])
        t = node_sym.get(e["target"])
        if s is not None and t is not None:
            slinks.append([s, t, RELS.index(rel)])

    # Degree tables, used for hotspot ranking and node sizing in the browser.
    sym_in = [0] * len(syms)
    sym_out = [0] * len(syms)
    for s, t, _r in slinks:
        sym_out[s] += 1
        sym_in[t] += 1
    file_in = [0] * len(files)
    file_out = [0] * len(files)
    for (a, b), w in flinks.items():
        file_out[a] += w
        file_in[b] += w

    payload = {
        "meta": {
            "nodes": meta["nodeCount"],
            "edges": meta["edgeCount"],
            "files": len(files),
            "symbols": len(syms),
            "languages": meta["languages"],
            "scopes": [s["prefix"] for s in meta.get("scopes", [])],
            "generated": None,
        },
        "kinds": KINDS,
        "rels": RELS,
        "files": files,
        "names": names,
        "syms": syms,
        "symsIn": sym_in,
        "symsOut": sym_out,
        "filesIn": file_in,
        "filesOut": file_out,
        "flinks": [[a, b, w] for (a, b), w in flinks.items()],
        "slinks": slinks,
    }

    body = json.dumps(payload, separators=(",", ":"))
    shell = os.path.join(os.path.dirname(os.path.abspath(__file__)), "explorer.html")
    with open(shell) as fh:
        html = fh.read()
    html = html.replace("/*__GRAFT_DATA__*/null", body)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write(html)

    print(f"files={len(files)} symbols={len(syms)} names={len(names)}")
    print(f"flinks={len(flinks)} slinks={len(slinks)}")
    print(f"data={len(body)/1e6:.2f} MB  html={len(html)/1e6:.2f} MB -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
