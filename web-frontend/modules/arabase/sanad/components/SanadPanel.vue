<template>
  <section class="sanad" :aria-label="$t('sanad.name')">
    <header class="sanad__header">
      <span class="sanad__logo" aria-hidden="true">
        <img :src="avatar" alt="" draggable="false" />
      </span>
      <div class="sanad__heading">
        <h2 class="sanad__title">
          {{ $t('sanad.name') }}
          <span class="sanad__beta">{{ $t('sanad.beta') }}</span>
        </h2>
        <p class="sanad__tagline">{{ $t('sanad.tagline') }}</p>
      </div>
      <div class="sanad__header-actions">
        <button
          type="button"
          class="sanad__icon-button"
          :class="{ 'sanad__icon-button--active': showHistory }"
          :title="$t('sanad.history')"
          :aria-label="$t('sanad.history')"
          :aria-pressed="showHistory ? 'true' : 'false'"
          @click="toggleHistory"
        >
          <i class="iconoir-clock-rotate-right" aria-hidden="true"></i>
        </button>
        <button
          type="button"
          class="sanad__icon-button"
          :title="$t('sanad.newChat')"
          :aria-label="$t('sanad.newChat')"
          @click="startNewChat"
        >
          <i class="iconoir-plus" aria-hidden="true"></i>
        </button>
        <button
          type="button"
          class="sanad__icon-button"
          :title="$t('action.close')"
          :aria-label="$t('action.close')"
          @click="$bus.$emit('toggle-right-sidebar', false)"
        >
          <i class="iconoir-cancel" aria-hidden="true"></i>
        </button>
      </div>
    </header>

    <div v-if="showHistory" class="sanad__history">
      <p class="sanad__section-title">{{ $t('sanad.history') }}</p>
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
            <i class="iconoir-chat-lines" aria-hidden="true"></i>
            <span>{{ item.title || $t('sanad.untitled') }}</span>
          </a>
          <button
            type="button"
            class="sanad__icon-button sanad__icon-button--small"
            :title="$t('action.delete')"
            :aria-label="$t('action.delete')"
            @click="removeChat(item.id)"
          >
            <i class="iconoir-trash" aria-hidden="true"></i>
          </button>
        </li>
      </ul>
    </div>

    <template v-else>
      <div ref="scroller" class="sanad__messages" aria-live="polite">
        <div v-if="!hasMessages" class="sanad__welcome">
          <span class="sanad__welcome-orb" aria-hidden="true">
            <img :src="avatar" alt="" draggable="false" />
          </span>
          <p class="sanad__welcome-title">{{ $t('sanad.welcomeTitle') }}</p>
          <p class="sanad__welcome-text">{{ $t('sanad.welcomeText') }}</p>
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
              v-for="suggestion in suggestions"
              :key="suggestion.key"
              type="button"
              class="sanad__suggestion"
              @click="send($t(suggestion.key))"
            >
              <span class="sanad__suggestion-icon" aria-hidden="true">
                <i :class="suggestion.icon"></i>
              </span>
              <span class="sanad__suggestion-text">{{
                $t(suggestion.key)
              }}</span>
            </button>
          </div>
        </div>

        <article
          v-for="message in messages"
          :key="message.id"
          class="sanad__message"
          :class="`sanad__message--${message.role}`"
        >
          <div v-if="message.role === 'user'" class="sanad__bubble">
            {{ message.content }}
          </div>

          <div
            v-else
            class="sanad__card"
            :class="{
              'sanad__card--pending': message.status === 'pending',
              'sanad__card--error': message.status === 'error',
            }"
          >
            <div class="sanad__card-head">
              <span class="sanad__avatar" aria-hidden="true">
                <img :src="avatar" alt="" draggable="false" />
              </span>
              <span class="sanad__card-name">{{ $t('sanad.name') }}</span>
              <span
                v-if="message.status === 'pending'"
                class="sanad__typing"
                aria-hidden="true"
                ><span></span><span></span><span></span
              ></span>
            </div>

            <details
              v-if="message.actions.length"
              class="sanad__steps"
              :open="stepsOpen(message)"
            >
              <summary class="sanad__steps-summary">
                <i class="iconoir-list" aria-hidden="true"></i>
                {{ $t('sanad.steps', { count: message.actions.length }) }}
                <i
                  class="sanad__steps-chevron iconoir-nav-arrow-down"
                  aria-hidden="true"
                ></i>
              </summary>
              <ul class="sanad__actions">
                <li
                  v-for="(action, index) in message.actions"
                  :key="index"
                  class="sanad__action"
                  :class="{ 'sanad__action--failed': !action.ok }"
                  :title="action.error || ''"
                >
                  <i
                    class="sanad__action-icon"
                    :class="
                      action.ok ? 'iconoir-check' : 'iconoir-warning-circle'
                    "
                    aria-hidden="true"
                  ></i>
                  <span class="sanad__action-label">{{
                    toolLabel(action.tool)
                  }}</span>
                  <nuxt-link
                    v-if="action.ok && actionLink(action)"
                    class="sanad__action-link"
                    :to="actionLink(action)"
                  >
                    {{ $t('sanad.open') }}
                  </nuxt-link>
                </li>
              </ul>
            </details>

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
              class="sanad__decided"
            >
              <i
                :class="call.approved ? 'iconoir-check' : 'iconoir-cancel'"
                aria-hidden="true"
              ></i>
              {{
                call.approved
                  ? $t('sanad.approved', { action: toolLabel(call.tool) })
                  : $t('sanad.declined', { action: toolLabel(call.tool) })
              }}
            </p>

            <p v-if="message.status === 'pending'" class="sanad__thinking">
              <span class="sanad__shimmer">{{ $t('sanad.working') }}</span>
            </p>
            <p v-if="message.status === 'error'" class="sanad__error">
              <i class="iconoir-warning-circle" aria-hidden="true"></i>
              {{ errorText(message.error) }}
            </p>
          </div>
        </article>
      </div>

      <form class="sanad__composer" @submit.prevent="send()">
        <div
          class="sanad__composer-box"
          :class="{ 'sanad__composer-box--disabled': busy || noModel }"
        >
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
            <label v-if="models.length > 1" class="sanad__model-chip">
              <i class="iconoir-cpu" aria-hidden="true"></i>
              <select
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
            </label>
            <span
              v-else-if="models.length === 1"
              class="sanad__model-chip sanad__model-name"
              dir="ltr"
              :title="models[0]"
            >
              <i class="iconoir-cpu" aria-hidden="true"></i>
              {{ models[0] }}
            </span>
            <button
              type="submit"
              class="sanad__send"
              :class="{ 'sanad__send--loading': sending }"
              :disabled="!canSend"
              :title="$t('sanad.send')"
              :aria-label="$t('sanad.send')"
            >
              <i class="iconoir-arrow-up" aria-hidden="true"></i>
            </button>
          </div>
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
import { takeSanadDraft } from '@jadawel/modules/arabase/sanad/utils/askSanad'
import sanadAvatar from '@jadawel/modules/arabase/assets/images/sanad-avatar.webp?url'

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
  'add_fields_to_form',
  'load_skill',
  'list_page_elements',
  'describe_page_element',
  'add_page_element',
  'update_page_element',
  'delete_page_element',
  'add_page_data_source',
  'get_app_theme',
  'update_app_theme',
  'create_dashboard',
  'get_dashboard',
  'add_dashboard_widget',
  'update_dashboard_widget',
  'delete_dashboard_widget',
  'create_page_view',
  'get_page_view',
  'write_page_view',
  'edit_page_view',
  'list_page_view_revisions',
  'restore_page_view_revision',
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
      avatar: sanadAvatar,
      draft: '',
      sending: false,
      deciding: false,
      showHistory: false,
      pollTimer: null,
      suggestions: [
        { key: 'sanad.suggestions.createTable', icon: 'iconoir-table' },
        { key: 'sanad.suggestions.formula', icon: 'iconoir-calculator' },
        { key: 'sanad.suggestions.dashboard', icon: 'iconoir-graph-up' },
        { key: 'sanad.suggestions.summarize', icon: 'iconoir-reports' },
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
    this.$bus.$on('sanad-draft', this.useDraft)
    this.load()
  },
  beforeUnmount() {
    this.$bus.$off('sanad-draft', this.useDraft)
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
      // After the remembered chat, so a new request does not land in it.
      this.useDraft()
    },
    /**
     * Text another screen typed for the user (see askSanad): it starts a new
     * chat, since it is a new request, and waits in the composer to be
     * finished and sent.
     */
    useDraft() {
      const text = takeSanadDraft()
      if (!text) {
        return
      }
      if (this.hasMessages && !this.busy) {
        this.startNewChat()
      }
      this.draft = text
      this.$nextTick(() => {
        const input = this.$refs.input
        if (input) {
          input.focus()
          input.setSelectionRange(text.length, text.length)
        }
      })
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
    /**
     * A short list of steps stays open; a long one folds once the answer is
     * in, so the answer is what the user reads first. While Sanad works the
     * steps stay open: they are the progress.
     */
    stepsOpen(message) {
      return message.status === 'pending' || message.actions.length <= 4
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
      if (refs.dashboard_id) {
        return {
          name: 'dashboard-application',
          params: { dashboardId: refs.dashboard_id },
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
      if (refs.view_id) {
        params.viewId = refs.view_id
      } else if (action.tool === 'create_view' && refs.id) {
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
