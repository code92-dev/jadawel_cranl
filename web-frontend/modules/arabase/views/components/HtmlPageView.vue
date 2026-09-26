<template>
  <div class="html-page-view">
    <div v-if="loading" class="html-page-view__state">
      <div class="loading"></div>
    </div>
    <!--
      An empty page means two different things to two different people. To
      whoever owns the view it is a setup screen: the page is authored from
      outside Jadawel, so without the endpoint and the page's number there is no
      way in. To a visitor holding a public link it is just a page that has
      nothing on it yet, and the MCP setup is none of their business — the
      endpoint list behind it needs an account anyway.
    -->
    <HtmlPageOnboarding
      v-else-if="!view.html && !readOnly"
      :database="database"
      :view="view"
    ></HtmlPageOnboarding>
    <div v-else-if="!view.html" class="html-page-view__state">
      <p class="html-page-view__empty-title">
        {{ $t('htmlPageView.emptyTitle') }}
      </p>
      <p class="html-page-view__empty-description">
        {{ $t('htmlPageView.emptyPublicDescription') }}
      </p>
    </div>
    <iframe
      v-else
      ref="frame"
      class="html-page-view__frame"
      :title="view.name"
      :srcdoc="document"
      sandbox="allow-scripts"
      referrerpolicy="no-referrer"
      @load="send"
    ></iframe>
  </div>
</template>

<script>
import { buildPageDocument } from '@jadawel/modules/arabase/views/utils/pageDocument'
import HtmlPageOnboarding from '@jadawel/modules/arabase/views/components/HtmlPageOnboarding'

/**
 * Renders a page view's HTML.
 *
 * The document is untrusted: it is written by an AI over MCP and by anyone who
 * can edit the view. So it is never rendered on this origin. `sandbox` is set
 * to `allow-scripts` and deliberately *not* `allow-same-origin` — the two
 * together would hand the document our origin back, and with it the viewer's
 * session token. Without `allow-same-origin` the frame gets an opaque origin,
 * and `postMessage` is the only channel back to this page.
 *
 * Data therefore reaches the page by message rather than by the page calling
 * the API itself, which is also why the backend's CSP can set
 * `connect-src 'none'`. That closes fetch, XHR, WebSocket and beacons, but not
 * every way out: the frame may still navigate itself to a URL carrying the
 * rows, and WebRTC is outside CSP. So the page must only ever be handed rows
 * its author could already read. Protected MCP values meet that bar only
 * through an approval bound to the exact HTML (`artifact_boundary.py`); do not
 * widen this payload on the assumption that CSP contains it.
 */
export default {
  name: 'HtmlPageView',
  components: { HtmlPageOnboarding },
  props: {
    database: { type: Object, required: true },
    table: { type: Object, required: true },
    view: { type: Object, required: true },
    fields: { type: Array, required: true },
    readOnly: { type: Boolean, required: false, default: false },
    storePrefix: { type: String, required: false, default: '' },
  },
  computed: {
    storeKey() {
      return this.storePrefix + 'view/html_page/'
    },
    loading() {
      return (
        this.$store.getters[this.storeKey + 'getLoading'] &&
        !this.$store.getters[this.storeKey + 'getLoaded']
      )
    },
    rows() {
      return this.$store.getters[this.storeKey + 'getRows']
    },
    document() {
      return buildPageDocument(
        this.view.html,
        this.view.content_security_policy
      )
    },
    visibleFields() {
      // The backend already withholds hidden fields from the feed; mirroring
      // that here keeps the `fields` array the page reads consistent with the
      // keys that actually appear on its rows.
      const fieldOptions = this.view.field_options || {}
      return this.fields
        .filter((field) => !fieldOptions[field.id]?.hidden)
        .map((field) => ({
          id: field.id,
          name: field.name,
          type: field.type,
          order: fieldOptions[field.id]?.order ?? 0,
        }))
        .sort((a, b) => a.order - b.order || a.id - b.id)
    },
    payload() {
      return {
        fields: this.visibleFields,
        rows: this.rows.map((row) => this.serializeRow(row)),
        view: {
          id: this.view.id,
          name: this.view.name,
          count: this.$store.getters[this.storeKey + 'getCount'],
          rowLimit: this.$store.getters[this.storeKey + 'getRowLimit'],
          truncated: this.$store.getters[this.storeKey + 'getTruncated'],
          locale: this.$i18n.locale,
          // `<html dir>` is the source of truth for direction in this fork —
          // the arabase plugin sets it from the active locale, and ChartWidget
          // reads it the same way. `$i18n.localeProperties` is undefined in the
          // Options API here, so reading `.dir` off it silently pinned every
          // page to `ltr`, Arabic ones included. `$i18n.locale` is still
          // referenced so this recomputes when the language changes.
          dir:
            (this.$i18n.locale && typeof document !== 'undefined'
              ? document.documentElement.dir
              : '') || 'ltr',
        },
      }
    },
  },
  watch: {
    payload() {
      this.send()
    },
  },
  mounted() {
    window.addEventListener('message', this.onMessage)
    // The public page is server-rendered, so the frame is in the HTML the
    // browser parses: it can finish loading — and post its `ready` — before Vue
    // hydrates and the listener above exists. Waiting for `ready` or for `load`
    // would then wait forever and the page would sit on its placeholders. So
    // push once here too; the frame's own listener is installed by the time its
    // document has loaded, and a duplicate delivery is harmless.
    this.send()
  },
  beforeUnmount() {
    window.removeEventListener('message', this.onMessage)
  },
  methods: {
    /**
     * Turn `{ id, order, field_1: … }` into the shape documented in the runtime
     * contract: values keyed by field name, with the raw `field_<id>` keys kept
     * for the case where two fields share a name.
     */
    serializeRow(row) {
      const values = {}
      const raw = {}
      this.visibleFields.forEach((field) => {
        const key = `field_${field.id}`
        raw[key] = row[key] ?? null
        values[field.name] = row[key] ?? null
      })
      return { id: row.id, order: row.order, values, raw }
    },
    onMessage(event) {
      const frame = this.$refs.frame
      // The frame's origin is opaque, so identity is established by comparing
      // the source window, not by checking event.origin.
      if (!frame || event.source !== frame.contentWindow) {
        return
      }

      const message = event.data
      if (!message || typeof message !== 'object') {
        return
      }

      if (message.type === 'jadawel:ready') {
        this.send()
      } else if (message.type === 'jadawel:height') {
        this.applyHeight(message.height)
      }
    },
    applyHeight(height) {
      const frame = this.$refs.frame
      if (!frame || typeof height !== 'number' || !isFinite(height)) {
        return
      }
      // Bounded: a page that reports a runaway height should not be able to
      // stretch the app's layout indefinitely.
      frame.style.height = `${Math.min(Math.max(height, 120), 20000)}px`
    },
    /**
     * Also bound to the frame's `load` event, which covers the case where the
     * frame loaded before we started listening.
     */
    send() {
      const frame = this.$refs.frame
      if (!frame || !frame.contentWindow) {
        return
      }
      frame.contentWindow.postMessage(
        // Serialised to plain data first. `payload` is assembled from store
        // state, so its objects are Vue reactive Proxies, and postMessage runs
        // the structured clone algorithm, which throws DataCloneError on a
        // Proxy. Posting it directly fails on every call — and because the
        // failure is a throw rather than a rejected message, the page simply
        // never receives anything. The feed is JSON from the API to begin with,
        // so a round trip costs nothing and loses nothing.
        {
          type: 'jadawel:data',
          payload: JSON.parse(JSON.stringify(this.payload)),
        },
        // The frame has an opaque origin, so '*' is the only target that can
        // ever match. The payload is data this viewer can already see.
        '*'
      )
    },
  },
}
</script>
