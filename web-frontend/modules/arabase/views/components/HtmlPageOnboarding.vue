<template>
  <div class="html-page-onboarding">
    <div class="html-page-onboarding__intro">
      <h2 class="html-page-onboarding__title">
        {{ $t('htmlPageOnboarding.title') }}
      </h2>
      <p class="html-page-onboarding__lead">
        {{
          $t(
            canAskSanad
              ? 'htmlPageOnboarding.leadWithSanad'
              : 'htmlPageOnboarding.lead'
          )
        }}
      </p>
    </div>

    <!--
      Sanad writes a page from inside Jadawel, with nothing to connect. Only
      staff can use Sanad (see ArabasePlugin), so only they see the offer.
    -->
    <section v-if="canAskSanad" class="html-page-onboarding__sanad">
      <div class="html-page-onboarding__sanad-text">
        <h3 class="html-page-onboarding__step-title">
          <i class="iconoir-sparks" aria-hidden="true"></i>
          {{ $t('htmlPageOnboarding.sanadTitle') }}
        </h3>
        <p class="html-page-onboarding__sanad-hint">
          {{ $t('htmlPageOnboarding.sanadHint') }}
        </p>
      </div>
      <Button type="primary" icon="iconoir-sparks" @click="openSanad">
        {{ $t('htmlPageOnboarding.sanadButton') }}
      </Button>
    </section>
    <p v-if="canAskSanad" class="html-page-onboarding__hint">
      {{ $t('htmlPageOnboarding.sanadOr') }}
    </p>

    <section class="html-page-onboarding__ask">
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
    </section>

    <!--
      The prompt only works for someone whose assistant can reach this
      workspace, so without an endpoint the way to make one comes right after
      it, opening the MCP setup directly.
    -->
    <div v-if="loading" class="loading"></div>
    <section
      v-else-if="!endpoint"
      class="html-page-onboarding__setup"
      role="note"
    >
      <i class="iconoir-plug-type-a" aria-hidden="true"></i>
      <div class="html-page-onboarding__setup-text">
        <p class="html-page-onboarding__setup-title">
          {{ $t('htmlPageOnboarding.mcpMissingTitle') }}
        </p>
        <p class="html-page-onboarding__setup-hint">
          {{ $t('htmlPageOnboarding.mcpMissingHint') }}
        </p>
      </div>
      <Button type="secondary" icon="iconoir-settings" @click="openSettings">
        {{ $t('htmlPageOnboarding.mcpSetup') }}
      </Button>
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
import { askSanad } from '@jadawel/modules/arabase/sanad/utils/askSanad'

/**
 * What a Page view shows before anything has been written into it.
 *
 * Shown to whoever can edit the page (HtmlPageView). An empty page is a dead
 * end unless it explains the way in: everyone gets a prompt for their own
 * assistant over MCP, carrying this page's number, and administrators also get
 * Sanad, which needs nothing set up. When the user has no MCP endpoint for this
 * workspace, the prompt is followed by a button straight into the MCP setup,
 * since without one the prompt cannot work.
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
    canAskSanad() {
      return this.$store.getters['auth/isStaff']
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
    openSanad() {
      askSanad(
        this.$bus,
        this.$t('htmlPageOnboarding.sanadDraft', { viewId: this.view.id })
      )
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
