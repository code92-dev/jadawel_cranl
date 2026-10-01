<template>
  <Modal ref="modal" class="sample-data-modal">
    <h2 class="box__title">{{ title }}</h2>
    <div class="sample-data-modal__sub-title">
      {{ $t('simulateDispatch.sampleDataModalSubTitle') }}
      <Button
        type="secondary"
        icon="iconoir-copy simulate-dispatch-node__button-icon"
        @click="copyToClipboard"
      >
        {{ $t('simulateDispatch.sampleDataCopy') }}
      </Button>
    </div>
    <Tabs v-if="hasHtmlTab" header-no-padding content-no-x-padding>
      <Tab title="JSON">
        <div class="sample-data-modal__code">
          <pre><code>{{ sampleData }}</code></pre>
        </div>
      </Tab>
      <Tab title="HTML">
        <iframe
          v-if="sampleDataHtml"
          class="sample-data-modal__html-preview"
          sandbox=""
          :srcdoc="sandboxedSampleDataHtml"
          :title="title"
        ></iframe>
        <div v-else class="sample-data-modal__notice">
          {{ $t('simulateDispatch.noHtmlContent') }}
        </div>
      </Tab>
    </Tabs>
    <div v-else class="sample-data-modal__code">
      <pre><code>{{ sampleData }}</code></pre>
    </div>
  </Modal>
</template>

<script>
import modal from '@jadawel/modules/core/mixins/modal'
import { notifyIf } from '@jadawel/modules/core/utils/error'

// Prepended to the HTML preview. The iframe's empty sandbox already blocks
// scripts, forms and navigation; this policy additionally stops the document
// from loading anything remote, so a tracking pixel in a received email cannot
// report when, and from which address, the sample was previewed.
const SAMPLE_DATA_HTML_CSP =
  '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; font-src data:">'

export default {
  name: 'SampleDataModal',
  mixins: [modal],
  props: {
    sampleData: {
      type: null,
      required: true,
    },
    /**
     * The content type of the sample data. When it's 'html', the modal
     * shows a JSON and an HTML tab instead of only the JSON payload.
     */
    contentType: {
      type: String,
      required: false,
      default: 'json',
    },
    /**
     * The HTML document rendered in the HTML tab when the content type is
     * 'html'. It's rendered in a fully sandboxed iframe because the content
     * is untrusted (e.g. a received email).
     */
    sampleDataHtml: {
      type: String,
      required: false,
      default: null,
    },
    title: {
      type: String,
      required: true,
    },
  },
  computed: {
    hasHtmlTab() {
      return this.contentType === 'html'
    },
    sandboxedSampleDataHtml() {
      return this.sampleDataHtml
        ? `${SAMPLE_DATA_HTML_CSP}${this.sampleDataHtml}`
        : null
    },
  },
  methods: {
    async copyToClipboard() {
      try {
        await navigator.clipboard.writeText(
          JSON.stringify(this.sampleData, null, 2)
        )
        this.$store.dispatch('toast/success', {
          title: this.$t('simulateDispatch.sampleDataCopied'),
        })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
</script>
