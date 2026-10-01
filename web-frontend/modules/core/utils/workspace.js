/**
 * Fetches the workspaces and applications of the authenticated user if that hasn't
 * happened yet, and selects the provided workspace if it exists. Shared by the
 * `workspacesAndApplications` middleware and the pages that fetch them without
 * blocking the navigation, so that the workspace of the route is selected
 * regardless of which page loaded them first.
 *
 * Both lists come from independent endpoints, so they are requested together;
 * the workspace is selected once its list has arrived.
 */
export const fetchWorkspacesAndApplications = async (nuxtApp, workspaceId) => {
  const store = nuxtApp.$store

  const loadWorkspaces = async () => {
    if (!store.getters['workspace/isLoaded']) {
      await store.dispatch('workspace/fetchAll')

      const workspaces = store.getters['workspace/getAll']
      const workspaceExists =
        workspaces.find((w) => w.id === workspaceId) !== undefined

      if (workspaceExists) {
        try {
          await store.dispatch('workspace/selectById', workspaceId)
        } catch {}
      }
    }
  }

  await Promise.all([
    loadWorkspaces(),
    store.getters['application/isLoaded']
      ? Promise.resolve()
      : store.dispatch('application/fetchAll'),
  ])
}
