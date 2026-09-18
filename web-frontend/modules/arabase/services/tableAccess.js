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
    /** Replaces the guest's tables; an empty list parks them without access. */
    setTables(workspaceId, workspaceUserId, tables) {
      return client.patch(
        `/arabase/workspace/${workspaceId}/table-access/${workspaceUserId}/`,
        { tables }
      )
    },
    revoke(workspaceId, workspaceUserId) {
      return client.delete(
        `/arabase/workspace/${workspaceId}/table-access/${workspaceUserId}/`
      )
    },
  }
}
