<template>
  <Expandable card class="margin-top-2">
    <template #header="{ toggle, expanded }">
      <div class="mcp-endpoint__head">
        <div class="mcp-endpoint__name">
          <Editable
            ref="rename"
            :value="endpoint.name"
            @change="
              updateEndpoint(
                endpoint,
                { name: $event.value },
                { name: $event.oldValue }
              )
            "
          ></Editable>
        </div>
        <a
          ref="contextLink"
          class="mcp-endpoint__more"
          @click.prevent="
            $refs.context.toggle($refs.contextLink, 'bottom', 'right', 4)
          "
        >
          <i class="jadawel-icon-more-horizontal"></i>
        </a>
        <Context ref="context" overflow-scroll max-height-if-outside-viewport>
          <ul class="context__menu">
            <li class="context__menu-item">
              <a class="context__menu-item-link" @click="enableRename()">
                <i class="context__menu-item-icon iconoir-edit-pencil"></i>
                {{ $t('action.rename') }}
              </a>
            </li>
            <li class="context__menu-item">
              <a
                :class="{
                  'context__menu-item-link--loading': deleteLoading,
                }"
                class="context__menu-item-link"
                @click.prevent="deleteEndpoint(endpoint)"
              >
                <i class="context__menu-item-icon iconoir-bin"></i>
                {{ $t('action.delete') }}
              </a>
            </li>
          </ul>
        </Context>
      </div>
      <div class="mcp-endpoint__meta">
        <div class="mcp-endpoint__workspace">
          {{ workspace.name }}
        </div>
        <div class="mcp-endpoint__toggle">
          <a @click="toggle">
            {{ $t('mcpEndpoint.detailLabel')
            }}<i
              :class="
                expanded ? 'iconoir-nav-arrow-down' : 'iconoir-nav-arrow-right'
              "
            />
          </a>
        </div>
      </div>
    </template>
    <p class="margin-bottom-2">
      {{ $t('mcpEndpoint.endpointURLIntro') }}
    </p>
    <div class="mcp-endpoint__link margin-bottom-1">
      <div class="mcp-endpoint__box">
        {{ endpointUrl }}
      </div>
      <a
        v-tooltip="$t('mcpEndpoint.copyURL')"
        class="mcp-endpoint__link-action"
        @click="copyShareUrlToClipboard()"
      >
        <i class="iconoir-copy" />
        <Copied ref="copied"></Copied>
      </a>
    </div>
    <div class="flex">
      <a v-if="!reveal" href="#" @click.prevent="reveal = true">{{
        $t('mcpEndpoint.reveal')
      }}</a>
      <div class="mcp-endpoint__warning margin-bottom-1">
        {{ $t('mcpEndpoint.warning') }}
      </div>
    </div>
    <h3 class="mcp-endpoint__setup-title">
      {{ $t('mcpEndpoint.setupPromptTitle') }}
    </h3>
    <MarkdownIt
      class="mcp-endpoint__instructions margin-bottom-1"
      :content="$t('mcpEndpoint.setupPromptInstructions')"
    ></MarkdownIt>
    <div class="mcp-endpoint__prompt-row">
      <pre class="mcp-endpoint__prompt"><code class="mcp-endpoint__code">{{
          $t('mcpEndpoint.setupPrompt', { endpointUrl })
        }}</code></pre>
      <a
        v-tooltip="$t('mcpEndpoint.copyPrompt')"
        class="mcp-endpoint__prompt-action"
        @click.prevent="copyPromptToClipboard()"
      >
        <i class="iconoir-copy" />
        <Copied ref="promptCopied"></Copied>
      </a>
    </div>
    <a v-if="!reveal" href="#" @click.prevent="reveal = true">{{
      $t('mcpEndpoint.reveal')
    }}</a>
  </Expandable>
</template>

<script>
import McpEndpointService from '@jadawel/modules/core/services/mcpEndpoint'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import { copyToClipboard } from '@jadawel/modules/database/utils/clipboard'

export default {
  name: 'McpEndpoint',
  props: {
    endpoint: {
      type: Object,
      required: true,
    },
  },
  emits: ['deleted'],
  data() {
    return {
      reveal: false,
      deleteLoading: false,
    }
  },
  computed: {
    endpointUrl() {
      const key = this.reveal ? this.endpoint.key : '•••••••'
      return this.getEndpointUrl(key)
    },
    workspace() {
      return this.$store.getters['workspace/get'](this.endpoint.workspace_id)
    },
  },
  methods: {
    getEndpointUrl(key) {
      const backendUrl = this.$config.public.publicBackendUrl.replace(
        /\/+$/,
        ''
      )
      return `${backendUrl}/mcp/${key}/sse`
    },
    copyShareUrlToClipboard() {
      copyToClipboard(this.getEndpointUrl(this.endpoint.key))
      this.$refs.copied.show()
    },
    copyPromptToClipboard() {
      const endpointUrl = this.getEndpointUrl(this.endpoint.key)
      const prompt = this.$t('mcpEndpoint.setupPrompt', { endpointUrl })
      copyToClipboard(prompt)
      this.$refs.promptCopied.show()
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async updateEndpoint(endpoint, values, old) {
      Object.assign(endpoint, values)

      try {
        await McpEndpointService(this.$client).update(endpoint.id, values)
      } catch (error) {
        Object.assign(endpoint, old)
        notifyIf(error)
      }
    },
    async deleteEndpoint(endpoint) {
      if (this.deleteLoading) {
        return
      }

      this.deleteLoading = true

      try {
        await McpEndpointService(this.$client).delete(endpoint.id)
        this.deleteLoading = false
        this.$emit('deleted')
      } catch (error) {
        this.deleteLoading = false
        notifyIf(error)
      }
    },
  },
}
</script>
