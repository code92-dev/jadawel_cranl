import addPublicAuthTokenHeader from '@jadawel/modules/database/utils/publicView'

/**
 * The page view's data feed.
 *
 * Not paginated on purpose — the backend caps the response at the view's
 * `row_limit` and reports `truncated` when there was more. A page reads its
 * whole dataset at once, so paging would only push complexity into every
 * AI-authored document.
 */
export default (client) => {
  return {
    /**
     * @param {number|string} viewId The view's id, or its slug on a public page
     *   (the public serializer exposes the slug as the view's id).
     */
    fetchRows({ viewId, publicUrl = false, publicAuthToken = null }) {
      const config = { params: new URLSearchParams() }

      if (publicAuthToken) {
        addPublicAuthTokenHeader(config, publicAuthToken)
      }

      const suffix = publicUrl ? 'public/rows/' : ''
      return client.get(`/database/views/html-page/${viewId}/${suffix}`, config)
    },
  }
}
