import { WorkspaceSettingsPageType } from '@jadawel/modules/core/workspaceSettingsPageTypes'

/**
 * The "Table access" tab next to Members and Invites.
 *
 * Guests are invited from here rather than from the members invite form on
 * purpose: a guest without tables can see nothing, so the table picker is part
 * of the invitation rather than a follow-up step. Gated on the same permission
 * as the invites tab, because inviting a guest *is* a workspace invitation.
 */
export class TableAccessWorkspaceSettingsPageType extends WorkspaceSettingsPageType {
  static getType() {
    return 'table-access'
  }

  getName() {
    const { $i18n: i18n } = this.app
    return i18n.t('tableAccess.tabTitle')
  }

  hasPermission(workspace) {
    return this.app.$hasPermission(
      'workspace.list_invitations',
      workspace,
      workspace.id
    )
  }

  getRoute(workspace) {
    return {
      name: 'settings-table-access',
      params: {
        workspaceId: workspace.id,
      },
    }
  }
}
