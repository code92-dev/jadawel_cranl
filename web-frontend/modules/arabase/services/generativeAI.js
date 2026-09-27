/** Admin-managed AI provider keys (arabase.generative_ai). */
export default (client) => {
  return {
    fetchProviders() {
      return client.get('/arabase/admin/generative-ai/')
    },
    /** Only the given values change; a blank `api_key` keeps the saved one. */
    updateProvider(provider, values) {
      return client.patch(`/arabase/admin/generative-ai/${provider}/`, values)
    },
    resetProvider(provider) {
      return client.delete(`/arabase/admin/generative-ai/${provider}/`)
    },
  }
}
