<template>
  <form class="mcp-protection-flow" @submit.prevent="submit">
    <ol
      class="mcp-protection-flow__steps"
      :aria-label="$t('mcpProtection.steps')"
    >
      <li :aria-current="step === 1 ? 'step' : undefined">
        {{ $t('mcpProtection.detailsStep') }}
      </li>
      <li :aria-current="step === 2 ? 'step' : undefined">
        {{ $t('mcpProtection.fieldsStep') }}
      </li>
      <li :aria-current="step === 3 ? 'step' : undefined">
        {{ $t('mcpProtection.reviewStep') }}
      </li>
    </ol>

    <section v-if="step === 1" class="mcp-protection-flow__panel">
      <label>
        <span>{{ $t('mcpEndpointForm.nameLabel') }}</span>
        <input v-model.trim="name" data-test-id="endpoint-name" required />
      </label>
      <label>
        <span>{{ $t('mcpEndpointForm.workspaceLabel') }}</span>
        <select
          v-model.number="workspaceId"
          data-test-id="workspace-id"
          required
          @change="resetPolicySelection"
        >
          <option disabled value="">
            {{ $t('mcpProtection.chooseWorkspace') }}
          </option>
          <option
            v-for="workspace in workspaces"
            :key="workspace.id"
            :value="workspace.id"
          >
            {{ workspace.name }}
          </option>
        </select>
      </label>
      <button
        type="button"
        class="button button--primary"
        data-test-id="next-details"
        :disabled="!name || !workspaceId"
        @click="step = 2"
      >
        {{ $t('mcpProtection.next') }}
      </button>
    </section>

    <section v-else-if="step === 2" class="mcp-protection-flow__panel">
      <McpProtectionFieldSelector
        v-model="selectedFields"
        :databases="databases"
        @status="metadataStatus = $event"
      />
      <p
        v-if="metadataStatus.loading || metadataStatus.error"
        class="mcp-protection-flow__metadata-warning"
        role="alert"
      >
        {{
          metadataStatus.loading
            ? $t('mcpProtection.fieldsLoading')
            : $t('mcpProtection.fieldsLoadRetryBeforeSave')
        }}
      </p>
      <div class="mcp-protection-flow__actions">
        <button type="button" class="button" @click="step = 1">
          {{ $t('mcpProtection.back') }}
        </button>
        <button
          type="button"
          class="button button--primary"
          data-test-id="next-fields"
          :disabled="metadataStatus.loading || metadataStatus.error"
          @click="step = 3"
        >
          {{ $t('mcpProtection.review') }}
        </button>
      </div>
    </section>

    <section v-else class="mcp-protection-flow__panel">
      <McpProtectionReview
        :name="name"
        :workspace-name="workspaceName"
        :fields="selectedFields"
        :confirm-empty-policy="confirmEmptyPolicy"
        @update:confirm-empty-policy="confirmEmptyPolicy = $event"
      />
      <Error :error="error"></Error>
      <div class="mcp-protection-flow__actions">
        <button type="button" class="button" @click="step = 2">
          {{ $t('mcpProtection.back') }}
        </button>
        <button
          type="button"
          class="button button--primary"
          data-test-id="create-protected-endpoint"
          :disabled="!canCreate"
          @click="create"
        >
          {{ $t('mcpEndpointSettings.createEndpoint') }}
        </button>
      </div>
    </section>
  </form>
</template>

<script>
import { uuid } from '@jadawel/modules/core/utils/string'
import error from '@jadawel/modules/core/mixins/error'
import McpProtectionFieldSelector from '@jadawel/modules/arabase/mcp/components/McpProtectionFieldSelector'
import McpProtectionReview from '@jadawel/modules/arabase/mcp/components/McpProtectionReview'
import ProtectionPolicyService from '@jadawel/modules/arabase/mcp/services/protectionPolicy'
import { protectionErrorMap } from '@jadawel/modules/arabase/mcp/protectionErrors'
import { databasesInWorkspace } from '@jadawel/modules/arabase/mcp/selection'

export default {
  name: 'McpProtectionFlow',
  components: { McpProtectionFieldSelector, McpProtectionReview },
  mixins: [error],
  props: {
    workspaces: { type: Array, required: true },
    applications: { type: Array, required: true },
  },
  emits: ['created'],
  data() {
    return {
      step: 1,
      name: '',
      workspaceId: '',
      selectedFields: [],
      confirmEmptyPolicy: false,
      loading: false,
      idempotencyKey: uuid(),
      metadataStatus: { loading: false, error: false },
    }
  },
  computed: {
    databases() {
      return databasesInWorkspace(this.applications, this.workspaceId)
    },
    workspaceName() {
      return (
        this.workspaces.find((workspace) => workspace.id === this.workspaceId)
          ?.name || ''
      )
    },
    canCreate() {
      return !(
        this.loading ||
        this.metadataStatus.loading ||
        this.metadataStatus.error ||
        (!this.selectedFields.length && !this.confirmEmptyPolicy)
      )
    },
  },
  methods: {
    /** Implicit submission (Enter in an input) may only create from the review step. */
    submit() {
      if (this.step !== 3 || !this.canCreate) return
      return this.create()
    },
    resetPolicySelection() {
      this.selectedFields = []
      this.confirmEmptyPolicy = false
    },
    async create() {
      if (!this.selectedFields.length && !this.confirmEmptyPolicy) return
      this.loading = true
      this.hideError()
      try {
        const { data } = await ProtectionPolicyService(
          this.$client
        ).createEndpoint(
          {
            name: this.name,
            workspace_id: this.workspaceId,
            protected_field_ids: this.selectedFields.map((field) => field.id),
            confirm_empty_policy: this.confirmEmptyPolicy,
          },
          this.idempotencyKey
        )
        this.$emit('created', data)
      } catch (error) {
        this.handleError(error, 'endpoint', protectionErrorMap(this.$t))
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
