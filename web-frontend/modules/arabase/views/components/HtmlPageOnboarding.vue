<template>
  <div class="html-page-onboarding">
    <div class="html-page-onboarding__intro">
      <h2 class="html-page-onboarding__title">
        {{ $t('htmlPageOnboarding.title') }}
      </h2>
      <p class="html-page-onboarding__lead">
        {{ $t('htmlPageOnboarding.lead') }}
      </p>
    </div>

    <!-- 1. Connect ------------------------------------------------------- -->
    <section class="html-page-onboarding__step">
      <div class="html-page-onboarding__step-number">1</div>
      <div class="html-page-onboarding__step-body">
        <h3 class="html-page-onboarding__step-title">
          {{ $t('htmlPageOnboarding.connectTitle') }}
        </h3>

        <div v-if="loading" class="loading"></div>

        <template v-else-if="endpoint">
          <p class="html-page-onboarding__hint">
            {{ $t('htmlPageOnboarding.connectHint') }}
          </p>
          <div class="html-page-onboarding__copy-row">
            <code class="html-page-onboarding__code" dir="ltr">{{
              displayedUrl
            }}</code>
            <a
              v-tooltip="$t('htmlPageOnboarding.copy')"
              class="html-page-onboarding__copy"
              @click="copy(endpointUrl, 'url')"
            >
              <i class="iconoir-copy"></i>
              <Copied ref="copiedUrl"></Copied>
            </a>
          </div>
          <a
            v-if="!reveal"
            class="html-page-onboarding__reveal"
            @click.prevent="reveal = true"
            >{{ $t('htmlPageOnboarding.reveal') }}</a
          >
          <p class="html-page-onboarding__warning">
            {{ $t('htmlPageOnboarding.keyWarning') }}
          </p>

          <p class="html-page-onboarding__hint">
            {{ $t('htmlPageOnboarding.configHint') }}
          </p>
          <div class="html-page-onboarding__copy-row">
            <pre
              class="html-page-onboarding__code html-page-onboarding__code--block"
              dir="ltr"
            ><code>{{ clientConfig }}</code></pre>
            <a
              v-tooltip="$t('htmlPageOnboarding.copy')"
              class="html-page-onboarding__copy"
              @click="copy(realClientConfig, 'config')"
            >
              <i class="iconoir-copy"></i>
              <Copied ref="copiedConfig"></Copied>
            </a>
          </div>
          <a
            class="html-page-onboarding__reveal"
            @click.prevent="openSettings"
            >{{ $t('htmlPageOnboarding.manageKeys') }}</a
          >
        </template>

        <template v-else>
          <p class="html-page-onboarding__hint">
            {{ $t('htmlPageOnboarding.noKeyHint') }}
          </p>
          <Button type="primary" @click="openSettings">
            {{ $t('htmlPageOnboarding.createKey') }}
          </Button>
        </template>
      </div>
    </section>

    <!-- 2. The page's own number ----------------------------------------- -->
    <section class="html-page-onboarding__step">
      <div class="html-page-onboarding__step-number">2</div>
      <div class="html-page-onboarding__step-body">
        <h3 class="html-page-onboarding__step-title">
          {{ $t('htmlPageOnboarding.pageIdTitle') }}
        </h3>
        <p class="html-page-onboarding__hint">
          {{ $t('htmlPageOnboarding.pageIdHint') }}
        </p>
        <div class="html-page-onboarding__copy-row">
          <!--
            Western digits and ltr: the id is a token the assistant has to
            receive verbatim, not a number being read as Arabic prose.
          -->
          <code
            class="html-page-onboarding__code html-page-onboarding__code--id"
            dir="ltr"
            >{{ view.id }}</code
          >
          <a
            v-tooltip="$t('htmlPageOnboarding.copy')"
            class="html-page-onboarding__copy"
            @click="copy(String(view.id), 'id')"
          >
            <i class="iconoir-copy"></i>
            <Copied ref="copiedId"></Copied>
          </a>
        </div>
      </div>
    </section>

    <!-- 3. Ask ----------------------------------------------------------- -->
    <section class="html-page-onboarding__step">
      <div class="html-page-onboarding__step-number">3</div>
      <div class="html-page-onboarding__step-body">
        <h3 class="html-page-onboarding__step-title">
          {{ $t('htmlPageOnboarding.askTitle') }}
        </h3>
        <p class="html-page-onboarding__hint">
          {{ $t('htmlPageOnboarding.askHint') }}
        </p>
        <div class="html-page-onboarding__copy-row">
          <pre
            class="html-page-onboarding__code html-page-onboarding__code--block"
          ><code>{{ prompt }}</code></pre>
          <a
            v-tooltip="$t('htmlPageOnboarding.copy')"
            class="html-page-onboarding__copy"
            @click="copy(prompt, 'prompt')"
          >
            <i class="iconoir-copy"></i>
            <Copied ref="copiedPrompt"></Copied>
          </a>
        </div>
        <p class="html-page-onboarding__footnote">
          {{ $t('htmlPageOnboarding.freedomNote') }}
        </p>
      </div>
    </section>

    <!--
      Mounted only once it is wanted. SettingsModal fetches login options in its
      own `mounted`, and this panel sits on screen for every empty page — always
      rendering it would fire that request at people who never open settings.
    -->
    <SettingsModal v-if="settingsMounted" ref="settingsModal"></SettingsModal>
  </div>
</template>

<script>
import McpEndpointService from '@jadawel/modules/core/services/mcpEndpoint'
import SettingsModal from '@jadawel/modules/core/components/settings/SettingsModal'
import { copyToClipboard } from '@jadawel/modules/database/utils/clipboard'

/**
 * What a Page view shows before anything has been written into it.
 *
 * A page is authored from outside Jadawel, so an empty one is a dead end unless
 * it explains the way in: which MCP endpoint to connect to, which page the
 * assistant should write to, and a prompt to start from. Everything here is
 * reused from the MCP endpoint settings screen — the same URL shape, the same
 * masked key — so the two never drift apart.
 */
export default {
  name: 'HtmlPageOnboarding',
  components: { SettingsModal },
  props: {
    database: { type: Object, required: true },
    view: { type: Object, required: true },
  },
  data() {
    return {
      loading: true,
      reveal: false,
      endpoints: [],
      settingsMounted: false,
    }
  },
  computed: {
    workspaceId() {
      return this.database.workspace.id
    },
    /**
     * An endpoint is per user and per workspace, so only one belonging to this
     * workspace can read this table.
     */
    endpoint() {
      return this.endpoints.find((e) => e.workspace_id === this.workspaceId)
    },
    endpointUrl() {
      return this.buildUrl(this.endpoint ? this.endpoint.key : '')
    },
    displayedUrl() {
      // Masked by default, exactly as the settings screen does it: the key is a
      // credential and this view is often on a shared screen.
      return this.buildUrl(this.reveal ? this.endpoint.key : '•••••••')
    },
    clientConfig() {
      return this.buildConfig(this.displayedUrl)
    },
    realClientConfig() {
      return this.buildConfig(this.endpointUrl)
    },
    prompt() {
      return this.$t('htmlPageOnboarding.promptTemplate', {
        viewId: this.view.id,
        table: this.view.name,
      })
    },
  },
  async mounted() {
    await this.fetchEndpoints()
  },
  methods: {
    buildUrl(key) {
      const backendUrl = this.$config.public.publicBackendUrl.replace(
        /\/+$/,
        ''
      )
      return `${backendUrl}/mcp/${key}/sse`
    },
    buildConfig(url) {
      return `{
  "mcpServers": {
    "Jadawel MCP": {
      "command": "npx",
      "args": ["mcp-remote", "${url}"]
    }
  }
}`
    },
    async fetchEndpoints() {
      this.loading = true
      try {
        const { data } = await McpEndpointService(this.$client).fetchAll()
        this.endpoints = data
      } catch (error) {
        // Not fatal: steps 2 and 3 are still useful to someone who has already
        // connected, so the panel degrades to "create a key" rather than to an
        // error page.
        this.endpoints = []
      } finally {
        this.loading = false
      }
    },
    async openSettings() {
      // Also the "no key yet" button: do not mint a legacy empty endpoint from
      // this onboarding shortcut. Every creation path must use the protected
      // three-step flow, including the explicit zero-policy confirmation and
      // field review.
      this.settingsMounted = true
      await this.$nextTick()
      this.$refs.settingsModal.show('mcp-endpoint')
    },
    copy(value, ref) {
      copyToClipboard(value)
      const target =
        this.$refs[`copied${ref.charAt(0).toUpperCase()}${ref.slice(1)}`]
      if (target) {
        target.show()
      }
    },
  },
}
</script>
