# Kanban grouping dropdown release — 2026-09-06

## Bug and root cause

User report with a screenshot: on the kanban board's empty state ("choose a
single select field to group the board by"), the dropdown rendered ~40 px wide
and truncated every field name to a single character.

The chain: `.kanban-view__empty` is a column flexbox with `align-items:
center`, so children shrink to fit instead of stretching. The core `Dropdown`
has no intrinsic width, and its label span is an ellipsis with
`min-inline-size: 0`, which reduces the flex item's automatic minimum to zero —
the control collapsed to its icons. The absolutely positioned options panel
(`.dropdown__items`, inset-inline: 0) inherited the same collapsed width.

The `small` prop passed to `<Dropdown>` in the empty state was also dead: the
rewritten core Dropdown accepts only `size: regular|large` and no
`.dropdown--small` class exists. It rendered as a stray HTML attribute.

## Fix

`0ac3513` — `fix(kanban): stop the grouping dropdown collapsing in the empty
state`. Scoped rule in `modules/arabase/assets/scss/kanban.scss`:

```scss
.kanban-view__empty .dropdown {
  inline-size: 240px;
}
```

plus removal of the dead `small` prop from
`modules/arabase/kanban/components/KanbanView.vue`.

## Local verification

- Stylelint, ESLint (run from `web-frontend` with the Nuxt-generated config)
  and Prettier all pass on both files; `test/unit/arabase/kanban.spec.js`
  passes 6/6.
- Behaviour exercised in the local dev stack (the `jadawel_cranl-row-coloring`
  worktree served on :3000, fix applied there for hot reload): the dropdown
  measures exactly 240 px, the options panel follows at 240 px, searching "أ"
  shows the option «الحالة» untruncated, and selecting it groups the board into
  the four expected stacks («جديد», «قيد التنفيذ», «منجز», «بدون قيمة»).

## Release

- Publish all-in-one image run `34058494524` published
  `ghcr.io/code92-dev/jadawel_cranl:2.3.4-kanban-grouping-dropdown`, digest
  `sha256:b17643feb1d24daa98921b7de1dc1cc35c6d01cb77b62558f8f16a73b5a5089d`,
  built from `0ac3513` (run headSha verified). Anonymous GHCR pull returned the
  same digest, so CranL needs no registry credentials.
- Deployment pin `e4d328e` — `chore(deploy): pin kanban grouping dropdown
  image` — updates `ARG JADAWEL_IMAGE` to that digest.
- Release CI run `34058923663` on `e4d328e`: all seven gates passed, including
  Arabic locale parity (strict) and backend smoke + fork hygiene. The run for
  `0ac3513` (`34058485879`) was cancelled by the pin push under the workflow's
  concurrency group; its equivalent gates re-ran green on `e4d328e`.

## Production verification

CranL (`jadawel-org`, `8ff2d656-4fde-4513-adf3-6b9c20434867`, custom domain
`app.jadawl.site`) deployed `e4d328e` in 1m 4s, followed by **Actions →
Reload** (the digest-only `FROM` change does not swap running workers by
itself) and a CDN **Purge Cache**.

- `/_health/` returns HTTP 200 `OK`; `/login` returns 200.
- The served stylesheet `/_nuxt/entry.3Q4eo8_H.css` contains
  `.kanban-view__empty .dropdown{inline-size:240px}` — the running container is
  unambiguously the new image, since `kanban.scss` is registered as a global
  stylesheet (`nuxt.options.css`) and lands in the entry chunk.

## Limits

The production kanban empty state was not exercised in an authenticated
session (no production credentials from this machine); the served-CSS check
above is the proof that the fix ships. Any user opening a kanban view whose
grouping field is unset sees the dropdown at full width.

Local-only leftovers, intentionally not deployed: a test workspace «اختبار
كانبان» with user `kanban-fix-test@example.com` on the local dev stack, and a
duplicate of the fix in the `jadawel_cranl-row-coloring` worktree (cleaned up
after this release).
