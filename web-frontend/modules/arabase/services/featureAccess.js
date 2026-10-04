/** Who may use automations, applications and Sanad (arabase.feature_access). */
export default (client) => {
  return {
    fetchAll() {
      return client.get('/arabase/admin/feature-access/')
    },
    setEveryone(feature, everyone) {
      return client.patch(`/arabase/admin/feature-access/${feature}/`, {
        everyone,
      })
    },
    addGrants(feature, emails) {
      return client.post(`/arabase/admin/feature-access/${feature}/grants/`, {
        emails,
      })
    },
    removeGrant(feature, grantId) {
      return client.delete(
        `/arabase/admin/feature-access/${feature}/grants/${grantId}/`
      )
    },
  }
}
