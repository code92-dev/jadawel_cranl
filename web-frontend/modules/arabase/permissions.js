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
