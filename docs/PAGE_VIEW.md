# The Page view (صفحة)

A fourth view type alongside Grid, Gallery and Form. A **Page** renders an HTML
document that an AI writes over MCP, fed with the view's live rows, and shares on
a public link with the same optional password a form has.

Nothing about it is a special case in core: it registers into
`view_type_registry` from `ArabaseConfig.ready()`, its API mounts itself through
`view_type_registry.api_urls`, and its share UI is core's `ShareViewLink`
reacting to `can_share`. No file under `backend/src/jadawel/` or
`web-frontend/modules/{core,database}/` was edited, so there is no `PATCHES.md`
entry for it.

## Authoring a page

Authoring happens from the user's own AI client through the MCP server that
ships with the fork, or, for staff, through Sanad inside Jadawel (below).

**A new page explains this itself.** Create one and it opens on a setup panel
(`HtmlPageOnboarding.vue`) with the three things needed to get it written:

1. **The endpoint.** The workspace's MCP address, masked like the settings
   screen masks it, with the Claude Desktop config snippet ready to copy. If the
   user has no key for this workspace yet, the panel mints one in place rather
   than sending them to settings to find out how.
2. **The page's number.** The view id, shown large and copyable. It is what
   `get_page_view` and `update_page_view` take, so it is the one thing the
   assistant cannot work without.
3. **A prompt.** Pre-filled with that number and the call order, ending in a line
   for the user to describe what they want.

The panel is for whoever owns the view. A visitor on a public link to an empty
page sees a plain "nothing here yet" instead — the endpoint list behind it needs
an account, and an MCP address is not a visitor's business.

**Or Sanad writes it.** Staff can hand the page to Sanad (سند), the in-app
assistant, from the same panel: *Ask Sanad* opens it with the page's number typed
in. Sanad's `html-pages` skill carries this contract and writes through the view's
own update route, so revisions and the MCP artifact boundary apply the same way
(see `docs/SANAD_AI_ASSISTANT.md`).

The assistant then calls, in order:

- `create_page_view(table_id, name)` — or `list_page_views(table_id)` to find an
  existing one.
- `get_page_view(view_id)` — the current HTML, the fields, a five-row sample of
  real data, **and the runtime contract**.
- `update_page_view(view_id, html=…)` — writes the document.

## How much freedom the assistant has

Total, on how the page looks. The contract opens by saying so: no house
template, no component library to match, no restriction on layout, typography,
colour or motion. A dense dashboard, a printable report, a single number, a
poster — whatever the user asked for.

The constraints that remain are not stylistic, and it is worth being precise
about them so they are not mistaken for design rules:

- The page is **sealed off from the network**, so it must be self-contained.
  Inline the CSS and JS, use inline SVG or `data:` URIs for graphics. Flipping
  on external resources opens an allowlist of CDNs for libraries.
- It must honour `view.dir`, because an RTL layout built with left/right rules
  comes apart in Arabic.
- It is read-only, and it should say so when `view.truncated` is true rather
  than presenting a partial figure as a total.

`get_page_view` returns the contract as tool *output* rather than in a tool
description on purpose: `MCPTool.list` collapses a docstring with
`" ".join(description.split())`, which would flatten the whole spec into one
unreadable line.

| Tool | Purpose |
|---|---|
| `list_page_views` | Page views on a table, with share state and document size |
| `get_page_view` | HTML, fields, row sample, runtime contract |
| `create_page_view` | New page view on a table |
| `update_page_view` | Replace the HTML; also name, row limit, CDN toggle |
| `list_page_view_revisions` | Previous versions, newest first |
| `restore_page_view_revision` | Roll back to one of them |

Every tool goes through `ViewHandler`, so an MCP client has exactly the authority
of the user behind the endpoint — no more — and is confined to that endpoint's
workspace.

## The runtime contract

The canonical text lives in `backend/src/arabase/mcp/page/contract.py`, and the
runtime that implements it is `BOOTSTRAP_SCRIPT` in
`web-frontend/modules/arabase/views/utils/pageDocument.js`. **The two have to
change together.**

```js
window.jadawel.onData(({ fields, rows, view }) => {
  // fields: [{ id, name, type, order }]
  // rows:   [{ id, order, values: { 'Field name': … }, raw: { field_12: … } }]
  // view:   { id, name, count, rowLimit, truncated, locale, dir }
})
```

`onData` fires when the data arrives and again on every refresh. Reading
`window.jadawel.rows` once at load will find it empty.

## Why the page cannot hurt anyone

Storing author-supplied HTML and rendering it on the app's own origin is stored
XSS by design: a script in that document could read the viewer's session token
out of `localStorage` and post every table they can see to an attacker. Upstream
Baserow's `IFrameElement.vue` renders `srcdoc` with no `sandbox` attribute at
all; that is a warning, not a pattern to copy.

Two layers, in order of importance:

**1. The sandbox.** The iframe is rendered
`sandbox="allow-scripts"` and deliberately **without** `allow-same-origin`.
Granting both together would hand the document this origin back and defeat the
point. Without it the document has an opaque origin: no cookies, no
`localStorage`, no `indexedDB`, no reach into the parent DOM, no top-level
navigation, no popups. `postMessage` is the only channel, and the parent
verifies `event.source === iframe.contentWindow` — the origin of an opaque
document is `null`, so checking `event.origin` would be the wrong test.

**2. The policy.** `arabase/views/csp.py` builds a CSP on the server — not in
the browser, so a tampered frontend bundle cannot loosen it — and the client
injects it as the first element in the document's `<head>`. A page that adds its
own CSP can only narrow the result, since multiple policies combine
restrictively.

The load-bearing directive is `connect-src 'none'`. The page is handed real row
data, so what actually matters is that it cannot send that data anywhere:
`fetch`, `XHR`, `WebSocket`, `EventSource` and `sendBeacon` are all dead, and
`form-action 'none'` closes the form route. `'unsafe-inline'` and `'unsafe-eval'`
*are* granted — the whole document is untrusted by construction, so nonces would
protect nothing, and with the network sealed off `eval` buys an attacker nothing
while buying templating libraries a lot.

### Verified, not assumed

A page whose document deliberately tries to escape was run through the real
pipeline in Chrome. Watching the network rather than the return values, **no
request left the frame**:

| Attempt | Result |
|---|---|
| `localStorage`, `document.cookie`, `parent.document`, `top.location` | throw `SecurityError` |
| `fetch()` to a remote host | throws `TypeError` |
| `<img>` beacon | blocked (`img-src data: blob:`) |
| `window.open` | returns `null` |
| `form.submit()` to a remote host | returns normally, **no POST is sent** |
| `navigator.sendBeacon` | returns `true`, **nothing is sent** |
| `new WebSocket(...)` | constructs, **never connects** |
| `window.origin` | `"null"` — the opaque origin, as intended |

The last three are worth remembering before someone reports them as a hole.
`sendBeacon` returns `true` because the request was *queued*, and a `WebSocket`
constructor never throws for a policy violation; in both cases `connect-src
'none'` stops the request afterwards, and `form-action 'none'` does the same for
the form. Judging these by their return value gives the wrong answer — check the
network panel.

### The external-resources toggle

Off by default. Turning it on adds an allowlist of CDN hosts to `script-src`,
`style-src` and `font-src`, and widens `img-src` to `https:`.

`connect-src` stays `'none'` even then, so a CDN script still cannot POST the
rows out. The honest residual risk is the image beacon: with `img-src https:` a
script can encode data into an `<img>` URL. There is no way to allow CDN assets
without opening something a beacon fits through, which is why the toggle is off
by default and the UI states the cost before you flip it.

The allowlist is `JADAWEL_PAGE_VIEW_EXTERNAL_HOSTS` (see
`docs/CONFIGURATION.md`), read from the environment at call time.

## Three traps in the bridge

All three were found by opening the page in a browser, and none of them failed a
test or logged an error — worth knowing before changing `HtmlPageView.vue` or
`pageDocument.js`.

1. **Post plain data, never store state.** `payload` is assembled from the row
   store, and object-valued cells — file, select, link_row — come out as Vue
   reactive Proxies. Chrome's `postMessage` refuses to structured-clone a Proxy
   and throws `DataCloneError`, so *every* send failed and the page just sat
   there. Scalar cells stay plain, so a fixture of text and number columns will
   not reproduce it. Hence the `JSON.parse(JSON.stringify(...))` in `send()`.
   Note that Node's `structuredClone` reads through Proxies happily, so the unit
   test asserts the payload is not reactive rather than that cloning succeeds.
2. **The public page is server-rendered.** The frame can finish loading, and
   post its `ready`, before Vue hydrates and the component starts listening. So
   `mounted()` pushes data once itself; waiting only on `ready` or `@load`
   leaves the page on its placeholders forever.
3. **Measure height on `<body>`, not `<html>`.** The root element is stretched
   to the frame's own height, so measuring it hands the parent back the size it
   just set — the frame keeps its initial height with the content crammed in the
   top. `<body>` is content-sized and says what the document actually needs.

## Fields, rows and limits

- A newly created page starts with **every** field in its feed — it is code
  written against the row shape, and hiding fields by default is friction. This
  happens once, in `view_created`.
- A field added **later** follows core's caution in `prepare_field_options`: on a
  public view, or once anything is hidden, a new field arrives hidden. A column
  added next month does not become public on its own.
- `row_limit` (default 200, max 1000) bounds the feed. `truncated` tells the page
  when it is only seeing part of the table, so it can say so rather than present
  a partial total as the real one.
- `html` is capped at 512 KB.
- The last 20 versions of the HTML are kept. AI authoring makes a destructive
  overwrite a normal-looking tool call, so the recovery path is one tool call
  rather than a database restore.

## What it does not do

- One page renders **one view's** rows. An AI can read other tables over MCP and
  bake the results in, but the live feed is this view only.
- No realtime push on the public link. Rows load when the page opens, plus a
  manual refresh; `when_shared_publicly_requires_realtime_events` is `False`.
- The page is read-only. Writing rows back from an AI-authored document is a much
  larger trust decision and is not part of this.

## Where things live

| | |
|---|---|
| Model, view type, CSP, revisions | `backend/src/arabase/views/` |
| Row feed endpoints | `backend/src/arabase/api/html_page/` |
| MCP tools and the contract | `backend/src/arabase/mcp/page/` |
| Migration | `backend/src/arabase/migrations/0006_html_page_view.py` |
| View type, components, store | `web-frontend/modules/arabase/views/` |
| Document assembly (the security-critical part) | `web-frontend/modules/arabase/views/utils/pageDocument.js` |
| Public page | `web-frontend/modules/arabase/pages/publicPageView.vue`, route `/public/page/:slug` |
| Tests | `backend/tests/arabase/test_html_page_{view,mcp}.py`, `web-frontend/test/unit/arabase/htmlPage*.spec.js` |
