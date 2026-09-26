import ArtifactApprovalService from '@jadawel/modules/arabase/mcp/services/artifactApproval'

/**
 * A source edit on a managed MCP page is a new candidate, never a direct
 * write. The state endpoint is content-blind and provides only the stable
 * endpoint/manifest needed to submit the draft.
 *
 * Returns true when the edit was submitted as a draft, and false when the page
 * is unmanaged (or has no endpoint) so the caller must save it directly.
 */
export async function submitSourceEditAsDraft(client, view, values) {
  const service = ArtifactApprovalService(client)
  const { data: state } = await service.fetchState(view.id)
  if (state.artifact_state === 'unmanaged' || state.endpoint_id === null) {
    return false
  }
  await service.createDraft({
    endpoint_id: state.endpoint_id,
    view_id: view.id,
    html: values.html,
    protected_field_ids: state.protected_field_ids || [],
    audience: state.audience || 'authenticated',
    pending_view_values: Object.fromEntries(
      Object.entries(values).filter(([key]) => key !== 'html')
    ),
  })
  return true
}
