import { StoreItemLookupError } from '@jadawel/modules/core/errors'

/**
 * Selects the workflow's automation and its workspace before the page renders.
 * The route names no workspace, and the sidebar renders before the page loads
 * its data, so without this the server renders the sidebar without the
 * workspace and the browser renders it with one: a hydration mismatch.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  const { $store, $i18n } = useNuxtApp()

  const automationId = parseInt(to.params.automationId)
  const workflowId = parseInt(to.params.workflowId)

  try {
    const automation = await $store.dispatch(
      'application/selectById',
      automationId
    )

    await $store.dispatch('workspace/selectById', automation.workspace.id)

    await $store.dispatch('automationWorkflow/selectById', {
      automation,
      workflowId,
    })
  } catch (e) {
    if (e.response === undefined && !(e instanceof StoreItemLookupError)) {
      throw e
    }

    throw createError({
      statusCode: 404,
      message: $i18n.t('automationWorkflow.notFound'),
    })
  }
})
