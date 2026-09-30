# My dashboards (لوحاتي)

A personal page where each user collects dashboards in one place: dashboards
from their own workspaces, and anyone's dashboard by its public link, on this
server or on another Jadawel server. It opens from the user menu, directly
above "My settings" (إعداداتي), at `/my-dashboards`.

## What the user sees

- **A card gallery.** Each card sketches its dashboard's real layout (widget
  types and sizes on the 12-column board, no data, so the gallery loads
  nothing per card), with its name and where it comes from: the workspace's
  name, "Shared link" (رابط عام) for a link on this server, or the other
  server's host. Cards can be dragged into any order and removed; removing a
  card never touches the dashboard.
- **A card opens the dashboard full size** (`/my-dashboards/<id>`), read-only,
  rendered by the same widgets as the dashboard itself.
- **A card that cannot be opened says why:** the password changed (the user
  enters the new one on the card or the opened page), the dashboard is no
  longer available (link revoked or replaced, dashboard deleted, access lost),
  or the other server is not responding.

## Adding a dashboard

1. **From the user's workspaces** — the "Add dashboard" dialog lists every
   dashboard of every workspace the user may list, and a dashboard's own header
   has "Add to My dashboards". Adding one twice keeps the one card.
2. **By link** — the user pastes a public dashboard link
   (`…/public/dashboard/<slug>`, or its `/auth` page). A password-protected link
   asks for its password before the dashboard is added. The dashboard may be
   the user's own or anyone else's.

## Access rules

Every read is checked when it happens, so the page never shows more than the
user could open another way.

| Source                 | Read as                                                                                             | Stops working when                                                                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Workspace              | The user, with their own permissions, as inside the workspace                                       | The user leaves the workspace or loses read access; the dashboard is trashed                                           |
| Link on this server    | A visitor of the link: the same payload and the same field allow-list as `/public/dashboard/<slug>` | The link is revoked or rotated; the dashboard is trashed; the owner changes, adds or removes the password (asks again) |
| Link on another server | A visitor of that server's link, fetched by this server                                             | That server answers 404 (revoked or rotated) or refuses the stored password                                            |

### Passwords

- **This server:** the password is checked once and **never stored**. The card
  keeps the link's password _hash_ as it was when the user was let in
  (`SavedDashboard.granted_password`); access lasts while the hash still
  matches, so any change of password asks the user again.
- **Another server:** that server only hands out a share token, which it
  expires (after 7 days by default). So the password is kept **sealed** —
  encrypted with a key derived from `SECRET_KEY` (`arabase/sealing.py`), like
  the admin AI keys — and used only to get a new token when the old one is
  refused. The user is asked again only when the owner changes the password.
  Rotating `SECRET_KEY` makes the sealed passwords unreadable; the cards then
  ask for them again.
- Password guesses through this page are throttled like the link's own prompt:
  `JADAWEL_DASHBOARD_AUTH_RATE` (default `10/hour`), per user and per link.

### Links on other servers

This server calls the other one's anonymous public-dashboard API
(`/api/arabase/public/dashboard/<slug>/`, `…/auth/`, `…/dispatch/<id>/`) on the
user's behalf, so the other server needs nothing new, and its owner's password,
rotation and revocation keep working. The requests follow the webhook outbound
rules: private, loopback and link-local addresses are refused unless
`JADAWEL_WEBHOOKS_ALLOW_PRIVATE_ADDRESS` is set, and
`JADAWEL_WEBHOOKS_IP_BLACKLIST`/`_WHITELIST` and
`JADAWEL_WEBHOOKS_URL_REGEX_BLACKLIST` apply. Redirects are not followed,
answers are limited to 5 MB, and a server silent for 10 seconds counts as
unreachable. Such a link must be `https`, since its password travels with it.

Known limits:

- The other server's API is assumed to be served on the same origin as its
  links (`https://host/api/…`), as the all-in-one image does.
- The other server throttles password attempts per caller IP, and every user
  here shares this server's IP: many wrong guesses on one of its links can
  briefly lock that link for everyone here.
- A widget of a type this server does not know (from a newer server) is left
  out of the board; the rest of the dashboard still shows.

## Where it lives

| Part                                                     | Path                                                                                                 |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Model, access rules, remote client                       | `backend/src/arabase/saved_dashboards/`                                                              |
| API (`/api/arabase/my-dashboards/…`)                     | `backend/src/arabase/api/saved_dashboards/`                                                          |
| Sealing helper                                           | `backend/src/arabase/sealing.py`                                                                     |
| Page, full-size view, routes                             | `web-frontend/modules/arabase/pages/myDashboard{s,}.vue`, `routes.js`                                |
| Cards, dialogs, menu item, header button, `saved/` store | `web-frontend/modules/arabase/savedDashboards/`                                                      |
| Tests                                                    | `backend/tests/arabase/test_my_dashboards.py`, `web-frontend/test/unit/arabase/myDashboards.spec.js` |

The menu entry needs one core hook, `getUserContextComponentsBeforeSettings`,
logged in `PATCHES.md`.
