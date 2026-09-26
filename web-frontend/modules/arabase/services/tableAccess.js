export default (client) => {
  return {
    /** The workspace's guests and the invitations that are still pending. */
    fetchAll(workspaceId) {
      return client.get(`/arabase/workspace/${workspaceId}/table-access/`)
    },
    invite(workspaceId, { email, tables, baseUrl }) {
      return client.post(`/arabase/workspace/${workspaceId}/table-access/`, {
        email,
        tables,
        base_url: baseUrl,
      })
    },
    revoke(workspaceId, workspaceUserId) {
      return client.delete(
        `/arabase/workspace/${workspaceId}/table-access/${workspaceUserId}/`
      )
    },
  }
}
