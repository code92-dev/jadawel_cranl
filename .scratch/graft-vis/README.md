# graft-vis — visual explorer for the graft graph

`graft/` holds the repo's context graph as markdown wiring cards plus
`graft/.graph/wiring.json` (37,984 nodes, 79,210 edges). Those are great for an
agent and unreadable for a human, so this turns them into an interactive
node-link map.

```bash
python3 .scratch/graft-vis/build.py     # reads ../../graft/.graph/wiring.json
node    .scratch/graft-vis/smoke.mjs    # optional: walks every file/dir view
open    .scratch/graft-vis/index.html   # or serve it, the graph is embedded
```

`build.py` reads `explorer.html`, injects a compacted copy of the graph in place
of the `/*__GRAFT_DATA__*/null` placeholder, and writes `index.html` (~2.2 MB,
self-contained, no network, no dependencies). Re-run it after `graft build`.

## Levels

| view | nodes | edges |
| --- | --- | --- |
| directory | child dirs of the current path, sized by symbol count | file-level links rolled up |
| files | files in the current dir, sized by degree | aggregated cross-file calls/imports |
| symbols | a file's symbols plus linked symbols from elsewhere | individual `calls` / `imports` / `extends` / `references` |

Click selects and shows the detail panel (path, span, callers, callees), double
click drills in, breadcrumbs and `↑ up` walk back, `⤢ fit` reframes. Wheel zooms,
drag pans. Greys labelled `↗ …` are dependency targets outside the current
directory, so a subtree that only depends outward still shows its wiring.

Views are deep-linkable: `#dir=backend/src/jadawel`, `#files=web-frontend/modules/core`,
`#sym=backend/src/jadawel/core/mixins.py`.

## Notes

- `plugins/` renders empty. The graph only covers scopes with a marker file
  (`backend/`, `web-frontend/`, `e2e-tests/`, `integrations/zapier`), and
  `plugins/` has none.
- Dense views are capped and ranked by degree (900 files, 800 own symbols,
  260 linked symbols) so the browser never has to lay out 38k nodes at once; the
  status line says when a cap is in effect.
- Layout is a Barnes-Hut force simulation that cools to a stop, so the picture is
  stable after a couple of seconds. `smoke.mjs` stubs the DOM and builds every
  one of the 4,169 file views and every directory view to catch exceptions.
