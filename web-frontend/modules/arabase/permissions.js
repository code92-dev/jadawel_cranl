import { PermissionManagerType } from '@jadawel/modules/core/permissionManagerTypes'

/**
 * Supplies the VIEWER role's localized name and description (#36).
 *
 * The roles service (`core/services/roles.js`) builds the invite form's and
 * members table's role options without calling the role type's `getName()`;
 * the labels come from permission managers' `getRolesTranslations()`, keyed
 * by role uid — core's `basic` manager covers ADMIN and MEMBER the same way.
 * Without this entry the VIEWER dropdown item renders with an undefined
 * name.
 *
 * Enforcement is server-side (`viewer_role` permission manager in
 * `backend/src/arabase/permissions/`); the backend never lists this manager
 * in a workspace's permission managers, so `hasPermission` is never
 * consulted client-side.
 */
export class ViewerRoleTranslationsPermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'viewer_role_translations'
  }

  getRolesTranslations() {
    const { $i18n: i18n } = this.app

    return {
      VIEWER: {
        name: i18n.t('roles.viewer.name'),
        description: i18n.t('roles.viewer.description'),
      },
    }
  }
}

/**
 * Supplies the GUEST role's localized name and description.
 *
 * A guest is created through the Table access settings page, never through
 * core's invite form, so GUEST is deliberately *not* registered in the `roles`
 * registry: offering it there would let an admin create a member who can see
 * nothing. It still needs a label, because an accepted guest shows up in core's
 * members table with `permissions === 'GUEST'`.
 *
 * Enforcement is server-side (`table_grants` permission manager in
 * `backend/src/arabase/permissions/table_grants.py`).
 */
export class GuestRoleTranslationsPermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'guest_role_translations'
  }

  getRolesTranslations() {
    const { $i18n: i18n } = this.app

    return {
      GUEST: {
        name: i18n.t('roles.guest.name'),
        description: i18n.t('roles.guest.description'),
      },
    }
  }
}

/**
 * Hides from a guest what the backend would refuse anyway.
 *
 * `table_grants` (backend/src/arabase/permissions/table_grants.py) is an
 * allowlist: for a GUEST member it answers every check itself. This mirror only
 * ever *tightens* the UI — it returns `false` for an operation outside the
 * allowlist and defers (returns `undefined`) otherwise, so a bug here can hide
 * a button but can never grant anything. Enforcement stays server-side.
 *
 * The lists are duplicated from the backend deliberately: importing them is not
 * possible across the two runtimes, and the permissions object is keyed by
 * operation name in both.
 */
const GUEST_VIEWER_OPERATIONS = [
  'workspace.read',
  'workspace.list_applications',
  'application.read',
  'database.list_tables',
  'database.table.read',
  'database.table.list_rows',
  'database.table.list_row_names',
  'database.table.list_fields',
  'database.table.field.read',
  'database.table.listen_to_all',
  'database.table.list_views',
  'database.table.read_view_order',
  'database.table.read_row',
  'database.table.read_adjacent_row',
  'database.table.view.read',
  'database.table.view.list_rows',
  'database.table.view.read_row',
  'database.table.view.read_adjacent_row',
  'database.table.view.list_fields',
  'database.table.view.read_field_options',
  'database.table.view.read_default_values',
  'database.table.view.list_filter',
  'database.table.view.filter.read',
  'database.table.view.list_sort',
  'database.table.view.sort.read',
  'database.table.view.list_group_bys',
  'database.table.view.group_by.read',
  'database.table.view.list_aggregations',
  'database.table.view.read_aggregation',
]

const GUEST_EDITOR_OPERATIONS = [
  ...GUEST_VIEWER_OPERATIONS,
  'database.table.create_row',
  'database.table.update_row',
  'database.table.delete_row',
  'database.table.move_row',
  'database.table.read_row_history',
  'database.table.view.create_row',
  'database.table.view.update_row',
  'database.table.view.delete_row',
]

export class TableGrantsPermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'table_grants'
  }

  hasPermission(permissions, operation, context, workspaceId) {
    if (!permissions || !permissions.is_guest) {
      return undefined
    }

    const levels = Object.values(permissions.table_grants || {})
    const allowed = levels.includes('EDITOR')
      ? GUEST_EDITOR_OPERATIONS
      : GUEST_VIEWER_OPERATIONS

    if (!allowed.includes(operation)) {
      return false
    }

    // Inside the allowlist the decision still depends on *which* table the
    // context belongs to, which the frontend cannot resolve reliably. Defer to
    // the other managers and let the backend be the authority.
    return undefined
  }
}
