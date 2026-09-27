<template>
  <section class="sanad" :aria-label="$t('sanad.name')">
    <header class="sanad__header">
      <i class="sanad__logo iconoir-sparks" aria-hidden="true"></i>
      <h2 class="sanad__title">{{ $t('sanad.name') }}</h2>
      <Badge color="cyan" size="small" rounded>{{ $t('sanad.beta') }}</Badge>
      <div class="sanad__header-actions">
        <ButtonIcon
          icon="iconoir-clock-rotate-right"
          :active="showHistory"
          :title="$t('sanad.history')"
          :aria-label="$t('sanad.history')"
          @click="toggleHistory"
        />
        <ButtonIcon
          icon="iconoir-plus"
          :title="$t('sanad.newChat')"
          :aria-label="$t('sanad.newChat')"
          @click="startNewChat"
        />
        <ButtonIcon
          icon="iconoir-cancel"
          :title="$t('action.close')"
          :aria-label="$t('action.close')"
          @click="$bus.$emit('toggle-right-sidebar', false)"
        />
      </div>
    </header>

    <div v-if="showHistory" class="sanad__history">
      <p v-if="chats.length === 0" class="sanad__muted">
        {{ $t('sanad.noHistory') }}
      </p>
      <ul v-else class="sanad__history-list">
        <li
          v-for="item in chats"
          :key="item.id"
          class="sanad__history-item"
          :class="{
            'sanad__history-item--active': chat && chat.id === item.id,
          }"
        >
          <a class="sanad__history-link" @click.prevent="openChat(item.id)">
            {{ item.title || $t('sanad.untitled') }}
          </a>
          <ButtonIcon
            icon="iconoir-trash"
            size="small"
            :title="$t('action.delete')"
            :aria-label="$t('action.delete')"
            @click="removeChat(item.id)"
          />
        </li>
      </ul>
    </div>

    <template v-else>
      <div ref="scroller" class="sanad__messages" aria-live="polite">
        <div v-if="!hasMessages" class="sanad__welcome">
          <i class="sanad__welcome-icon iconoir-sparks" aria-hidden="true"></i>
          <p class="sanad__welcome-title">{{ $t('sanad.welcomeTitle') }}</p>
          <p class="sanad__muted">{{ $t('sanad.welcomeText') }}</p>
          <p v-if="noModel" class="sanad__notice">
            {{ $t('sanad.noModel') }}
            <nuxt-link
              class="sanad__notice-link"
              :to="{ name: 'admin-settings', hash: '#generative-ai' }"
              >{{ $t('sanad.openAISettings') }}</nuxt-link
            >
          </p>
          <div v-else class="sanad__suggestions">
            <button
              v-for="key in suggestionKeys"
              :key="key"
              type="button"
              class="sanad__suggestion"
              @click="send($t(key))"
            >
              {{ $t(key) }}
            </button>
          </div>
        </div>

        <div
          v-for="message in messages"
          :key="message.id"
          class="sanad__message"
          :class="`sanad__message--${message.role}`"
        >
          <div v-if="message.role === 'user'" class="sanad__bubble">
            {{ message.content }}
          </div>

          <template v-else>
            <ul v-if="message.actions.length" class="sanad__actions">
              <li
                v-for="(action, index) in message.actions"
                :key="index"
                class="sanad__action"
                :class="{ 'sanad__action--failed': !action.ok }"
                :title="action.error || ''"
              >
                <i
                  :class="
                    action.ok ? 'iconoir-check' : 'iconoir-warning-circle'
                  "
                  aria-hidden="true"
                ></i>
                <span>{{ toolLabel(action.tool) }}</span>
                <nuxt-link
                  v-if="action.ok && actionLink(action)"
                  class="sanad__action-link"
                  :to="actionLink(action)"
                >
                  {{ $t('sanad.open') }}
                </nuxt-link>
              </li>
            </ul>

            <MarkdownIt
              v-if="message.content"
              class="sanad__answer"
              :content="message.content"
            />

            <div
              v-for="call in waitingApprovals(message)"
              :key="call.tool_call_id"
              class="sanad__approval"
              role="group"
              :aria-label="$t('sanad.approvalTitle')"
            >
              <p class="sanad__approval-title">
                <i class="iconoir-warning-triangle" aria-hidden="true"></i>
                {{ $t('sanad.approvalTitle') }}
              </p>
              <p class="sanad__approval-text">
                {{ toolLabel(call.tool) }}
              </p>
              <code class="sanad__approval-args" dir="ltr">{{
                JSON.stringify(call.arguments)
              }}</code>
            </div>
            <div
              v-if="waitingApprovals(message).length"
              class="sanad__approval-buttons"
            >
              <Button
                :type="approvalLabels(message).type"
                size="small"
                :loading="deciding"
                :disabled="deciding"
                @click="decide(message, true)"
              >
                {{ approvalLabels(message).approve }}
              </Button>
              <Button
                type="secondary"
                size="small"
                :disabled="deciding"
                @click="decide(message, false)"
              >
                {{ approvalLabels(message).decline }}
              </Button>
            </div>

            <p
              v-for="call in decidedApprovals(message)"
              :key="call.tool_call_id"
              class="sanad__muted sanad__decided"
            >
              {{
                call.approved
                  ? $t('sanad.approved', { action: toolLabel(call.tool) })
                  : $t('sanad.declined', { action: toolLabel(call.tool) })
              }}
            </p>

            <p v-if="message.status === 'pending'" class="sanad__thinking">
              <span class="sanad__dots" aria-hidden="true"></span>
              {{ $t('sanad.working') }}
            </p>
            <p v-if="message.status === 'error'" class="sanad__error">
              {{ errorText(message.error) }}
            </p>
          </template>
        </div>
      </div>

      <form class="sanad__composer" @submit.prevent="send()">
        <textarea
          ref="input"
          v-model="draft"
          class="sanad__input"
          rows="2"
          dir="auto"
          :placeholder="$t('sanad.placeholder')"
          :aria-label="$t('sanad.placeholder')"
          :disabled="busy || noModel"
          @keydown.enter.exact.prevent="send()"
        ></textarea>
        <div class="sanad__composer-row">
          <select
            v-if="models.length > 1"
            v-model="model"
            class="sanad__model"
            dir="ltr"
            :aria-label="$t('sanad.model')"
            :title="$t('sanad.model')"
          >
            <option v-for="name in models" :key="name" :value="name">
              {{ name }}
            </option>
          </select>
          <span v-else-if="models.length === 1" class="sanad__model-name">
            {{ models[0] }}
          </span>
          <ButtonIcon
            class="sanad__send"
            icon="iconoir-send"
            tag="button"
            :disabled="!canSend"
            :loading="sending"
            :title="$t('sanad.send')"
            :aria-label="$t('sanad.send')"
            @click="send()"
          />
        </div>
        <p class="sanad__disclaimer">{{ $t('sanad.disclaimer') }}</p>
      </form>
    </template>
  </section>
</template>

<script>
import MarkdownIt from '@jadawel/modules/core/components/MarkdownIt'
import SanadService from '@jadawel/modules/arabase/services/sanad'
import { notifyIf } from '@jadawel/modules/core/utils/error'

const POLL_INTERVAL = 1500
const MODEL_STORAGE_KEY = 'jadawel.sanad.model'
const CHAT_STORAGE_KEY = 'jadawel.sanad.chat'
// Every tool and error code with a translation under `sanad.tools` and
// `sanad.errors`; anything newer falls back to its raw name or a generic text.
const KNOWN_TOOLS = new Set([
  'list_databases',
  'create_database',
  'list_tables',
  'get_table_schema',
  'create_table',
  'update_table',
  'delete_table',
  'create_fields',
  'update_fields',
  'delete_fields',
  'list_table_rows',
  'create_rows',
  'update_rows',
  'delete_rows',
  'list_views',
  'create_view',
  'delete_view',
  'add_view_filter',
  'add_view_sort',
  'list_applications',
  'create_automation',
  'create_workflow',
  'describe_automation_step',
  'get_workflow',
  'get_workflow_runs',
  'add_automation_step',
  'update_automation_step',
  'delete_automation_step',
  'publish_workflow',
  'create_builder_application',
  'list_pages',
  'create_page',
  'delete_page',
  'add_page_content',
  'add_table_to_page',
  'add_form_to_page',
])
const KNOWN_ERRORS = new Set([
  'SANAD_ERROR_MODEL_FAILED',
  'SANAD_ERROR_TOO_MANY_STEPS',
  'SANAD_ERROR_TIMED_OUT',
  'SANAD_ERROR_NOT_ALLOWED',
])

export default {
  name: 'SanadPanel',
  components: { MarkdownIt },
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      chat: null,
      chats: [],
      models: [],
      model: '',
      noModel: false,
      draft: '',
      sending: false,
      deciding: false,
      showHistory: false,
      pollTimer: null,
      suggestionKeys: [
        'sanad.suggestions.createTable',
        'sanad.suggestions.formula',
        'sanad.suggestions.summarize',
      ],
    }
  },
  computed: {
    messages() {
      return this.chat ? this.chat.messages : []
    },
    hasMessages() {
      return this.messages.length > 0
    },
    busy() {
      return this.messages.some((message) =>
        ['pending', 'awaiting_approval'].includes(message.status)
      )
    },
    canSend() {
      return (
        !this.busy && !this.sending && !this.noModel && this.draft.trim() !== ''
      )
    },
  },
  watch: {
    'workspace.id'() {
      this.reset()
      this.load()
    },
  },
  mounted() {
    this.load()
  },
  beforeUnmount() {
    this.stopPolling()
  },
  methods: {
    service() {
      return SanadService(this.$client)
    },
    reset() {
      this.stopPolling()
      this.chat = null
      this.chats = []
      this.showHistory = false
    },
    async load() {
      try {
        const { data } = await this.service().fetchModels(this.workspace.id)
        this.models = data.models
        this.noModel = data.models.length === 0
        const remembered = localStorage.getItem(MODEL_STORAGE_KEY)
        this.model = this.models.includes(remembered)
          ? remembered
          : this.models[0] || ''
        const chatId = parseInt(
          localStorage.getItem(`${CHAT_STORAGE_KEY}.${this.workspace.id}`)
        )
        if (chatId) {
          await this.openChat(chatId)
        }
      } catch (error) {
        notifyIf(error, 'sanad')
      }
    },
    remember(chatId) {
      const key = `${CHAT_STORAGE_KEY}.${this.workspace.id}`
      if (chatId) {
        localStorage.setItem(key, chatId)
      } else {
        localStorage.removeItem(key)
      }
    },
    async openChat(chatId) {
      try {
        const { data } = await this.service().fetchChat(chatId)
        this.chat = data
        this.remember(data.id)
        this.showHistory = false
        this.afterUpdate()
      } catch (error) {
        // A remembered chat that was deleted meanwhile starts a fresh one.
        this.chat = null
        this.remember(null)
      }
    },
    async toggleHistory() {
      this.showHistory = !this.showHistory
      if (this.showHistory) {
        try {
          const { data } = await this.service().fetchChats(this.workspace.id)
          this.chats = data
        } catch (error) {
          notifyIf(error, 'sanad')
        }
      }
    },
    startNewChat() {
      this.stopPolling()
      this.chat = null
      this.remember(null)
      this.showHistory = false
      this.$nextTick(() => this.$refs.input && this.$refs.input.focus())
    },
    async removeChat(chatId) {
      try {
        await this.service().deleteChat(chatId)
        this.chats = this.chats.filter((item) => item.id !== chatId)
        if (this.chat && this.chat.id === chatId) {
          this.startNewChat()
          this.showHistory = true
        }
      } catch (error) {
        notifyIf(error, 'sanad')
      }
    },
    currentContext() {
      const params = this.$route.params || {}
      const toId = (value) => (value ? parseInt(value) || null : null)
      return { table_id: toId(params.tableId), view_id: toId(params.viewId) }
    },
    async send(text) {
      const content = (text ?? this.draft).trim()
      if (!content || this.busy || this.sending || this.noModel) {
        return
      }
      this.sending = true
      try {
        if (!this.chat) {
          const { data } = await this.service().createChat(this.workspace.id)
          this.chat = data
          this.remember(data.id)
        }
        if (this.model) {
          localStorage.setItem(MODEL_STORAGE_KEY, this.model)
        }
        await this.service().sendMessage(
          this.chat.id,
          content,
          this.model,
          this.currentContext()
        )
        this.draft = ''
        await this.refresh()
      } catch (error) {
        notifyIf(error, 'sanad')
      } finally {
        this.sending = false
      }
    },
    async decide(message, approved) {
      this.deciding = true
      try {
        await this.service().decide(
          this.chat.id,
          this.waitingApprovals(message).map((call) => ({
            tool_call_id: call.tool_call_id,
            approved,
          }))
        )
        await this.refresh()
      } catch (error) {
        notifyIf(error, 'sanad')
      } finally {
        this.deciding = false
      }
    },
    async refresh() {
      if (!this.chat) {
        return
      }
      const { data } = await this.service().fetchChat(this.chat.id)
      if (this.chat && this.chat.id === data.id) {
        this.chat = data
        this.afterUpdate()
      }
    },
    afterUpdate() {
      this.stopPolling()
      if (this.messages.some((message) => message.status === 'pending')) {
        this.pollTimer = setTimeout(() => {
          this.refresh().catch((error) => notifyIf(error, 'sanad'))
        }, POLL_INTERVAL)
      }
      this.$nextTick(() => {
        const scroller = this.$refs.scroller
        if (scroller) {
          scroller.scrollTop = scroller.scrollHeight
        }
      })
    },
    stopPolling() {
      clearTimeout(this.pollTimer)
      this.pollTimer = null
    },
    waitingApprovals(message) {
      if (message.status !== 'awaiting_approval') {
        return []
      }
      return message.approvals.filter((call) => !('approved' in call))
    },
    decidedApprovals(message) {
      return message.approvals.filter((call) => 'approved' in call)
    },
    toolLabel(tool) {
      return KNOWN_TOOLS.has(tool) ? this.$t(`sanad.tools.${tool}`) : tool
    },
    errorText(code) {
      return this.$t(
        KNOWN_ERRORS.has(code) ? `sanad.errors.${code}` : 'sanad.errors.generic'
      )
    },
    /** Where "Open" goes for something an action created or changed. */
    actionLink(action) {
      const refs = action.refs || {}
      if (refs.automation_id && refs.workflow_id) {
        return {
          name: 'automation-workflow',
          params: {
            automationId: refs.automation_id,
            workflowId: refs.workflow_id,
          },
        }
      }
      if (refs.application_id && refs.page_id) {
        return {
          name: 'builder-page',
          params: { builderId: refs.application_id, pageId: refs.page_id },
        }
      }
      const tableId =
        refs.table_id ||
        (['create_table', 'update_table'].includes(action.tool) && refs.id)
      if (!tableId || !refs.database_id) {
        return null
      }
      const params = { databaseId: refs.database_id, tableId }
      if (action.tool === 'create_view' && refs.id) {
        params.viewId = refs.id
      }
      return { name: 'database-table', params }
    },
    /** Publishing reads as "Publish / Not now"; everything else deletes. */
    approvalLabels(message) {
      const publishing = this.waitingApprovals(message).some(
        (call) => call.tool === 'publish_workflow'
      )
      return publishing
        ? {
            type: 'primary',
            approve: this.$t('sanad.approvePublish'),
            decline: this.$t('sanad.declinePublish'),
          }
        : {
            type: 'danger',
            approve: this.$t('sanad.approve'),
            decline: this.$t('sanad.decline'),
          }
    },
  },
}
</script>
