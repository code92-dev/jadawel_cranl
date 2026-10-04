# Feature access (إتاحة المزايا) — who may use automations, applications and Sanad

Three features started out limited to instance administrators (staff):
automations (الأتمتة), the application builder (التطبيقات) and Sanad (سند), the
AI assistant. An administrator now decides who else uses each one, from
**Admin → Settings → Feature access**:

- **Available to everyone** opens the feature to every user.
- **Invited users** grants it to email addresses while it is not open to everyone.
  An address without an account yet is covered as soon as an account is created
  with it; the list marks such addresses "No account yet".

Staff always keep every feature. With nothing configured — the state after the
upgrade — the three features stay staff-only, exactly as before.

## What a feature covers

| Feature      | Without access                                                                                           | With access                                   |
| ------------ | -------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `automation` | "Automation" is not offered in "Add new"; `POST /api/applications/workspace/<id>/` with that type, or installing a template that contains one → 403 | Create automations                            |
| `builder`    | "Application" is not offered in "Add new"; the same API call, or installing a template that contains one → 403 | Create applications                           |
| `sanad`      | No Sanad in the workspace tools menu or right sidebar, no "Ask Sanad" box; every Sanad endpoint → 403   | Use Sanad in the workspaces the user belongs to |

The gate is on **creating**, as it was when these were staff-only. Automations and
applications that already exist in a workspace stay with its members whoever made
them: they still list, open and edit them under their workspace role. Duplicating
an existing one or importing a workspace export is not gated either.

Templates: the catalog includes automation and application templates
(docs/SAUDI_TEMPLATES.md). Installing one is refused before the install job is
queued (`InstallTemplateJobType.prepare_values`), so the user sees "Not
available" at once; the template picker still lists them. A template chosen on the
sign-up page is installed into the new account's workspace without the check, so
that sign-up never fails over it.

Sanad creates automations and applications through the same handler, so opening
Sanad to a user does not open the other two: its `create_automation` and
`create_builder_application` tools fail for a user without those features.
Setting a workspace's monthly Sanad allowance stays staff-only.

## How it works

- **Data.** `arabase.feature_access.models`: `FeatureAccess` (one row per feature
  once an administrator touches it; `everyone`) and `FeatureAccessGrant`
  (`feature`, `email` normalized to lower case, `granted_by`). Migration
  `arabase/0024_feature_access`. A grant names an address, not an account: if a
  user changes their email, the grant stays with the old address.
- **Rule.** `arabase.feature_access.handler.has_feature(user, feature)`: staff, or
  `everyone`, or a grant for the user's normalized email.
- **Frontend.** `FeatureAccessUserDataType` adds `arabase_features`
  (`{"automation": bool, "builder": bool, "sanad": bool}`) to the login and
  token-refresh responses. `hasFeature(store, feature)` in
  `web-frontend/modules/arabase/featureAccess/featureAccess.js` reads it; the
  builder and automation `canBeCreated()` read the same key directly, since core
  modules do not import `arabase`. Without the key (an older backend), staff keep
  the features.
- **Live updates.** A change is pushed at once to the signed-in users it affects
  through core's `user_data_updated` realtime event, so menus update without a
  reload: opening a feature to everyone goes to all users; closing it goes to
  active non-staff users without a grant; adding or removing a grant goes to the
  account with that address.
- **Creation check.** Core's `CoreHandler.create_application` sends
  `before_application_created` after its permission check, and the template
  install job sends it once per application type in the template (core patches,
  see `PATCHES.md`); `refuse_ungranted_application` raises `FeatureNotGranted`, a
  `FeatureDisabledException`, which every API view maps to `ERROR_FEATURE_DISABLED`
  (403).

## Admin API

All under `/api/arabase/admin/feature-access/`, staff only (`IsAdminUser`); every
response is the whole list, `{"features": [{"feature", "everyone", "grants":
[{"id", "email", "created_on", "user": null | {"id", "name", "is_staff",
"is_active"}}]}]}`.

| Method   | Path                            | Body                     |
| -------- | ------------------------------- | ------------------------ |
| `GET`    | `/`                             |                          |
| `PATCH`  | `/<feature>/`                   | `{"everyone": true}`     |
| `POST`   | `/<feature>/grants/`            | `{"emails": ["a@b.sa"]}` (1–100) |
| `DELETE` | `/<feature>/grants/<grant_id>/` |                          |

Unknown feature → 404 `ERROR_FEATURE_DOES_NOT_EXIST`; a grant of another feature
→ 404 `ERROR_FEATURE_GRANT_DOES_NOT_EXIST`.

## Not included

- **No email is sent.** "Invite" records the address; the person sees the feature
  the next time they are signed in (at once, if they already are). An address
  without an account still needs a way to sign up: an open sign-up page or a
  workspace invitation.
- Grants are not removed when an account is deleted; remove them from the list.

## Removal

Dropping the feature means reverting the code; the two tables can stay or be
dropped by reversing `0024_feature_access`. Nothing else stores data for it.

## Tests

- `backend/tests/arabase/test_feature_access.py` — the rule, the admin API
  (staff, member, anonymous, invalid input), login payload, realtime messages,
  creation refusal and Sanad.
- `web-frontend/test/unit/arabase/featureAccess.spec.js` — `hasFeature`,
  `canBeCreated()`, the Sanad hooks and the settings component.
- E2E: `createBuilder` and `createAutomation` grant the feature first
  (`e2e-tests/fixtures/featureAccess.ts`); `createApplication.spec.ts` still
  asserts a new user is not offered either.
