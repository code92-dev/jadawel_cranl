export default (client) => ({
  createDraft(values) {
    return client.post('/arabase/mcp/protection/artifacts/drafts/', values)
  },
  fetchState(viewId) {
    return client.get(`/arabase/mcp/protection/artifacts/views/${viewId}/`)
  },
  approveDraft(draftId) {
    return client.post(
      `/arabase/mcp/protection/artifacts/drafts/${draftId}/approve/`
    )
  },
})
