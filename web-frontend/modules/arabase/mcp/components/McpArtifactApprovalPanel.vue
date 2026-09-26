<template>
  <div
    v-if="visible && state && state.artifact_state !== 'unmanaged'"
    class="mcp-artifact-approval"
    role="status"
    aria-live="polite"
  >
    <span class="mcp-artifact-approval__label">
      {{ $t('mcpArtifactApproval.label') }}
    </span>
    <span class="mcp-artifact-approval__state">
      {{ stateLabel }}
    </span>
    <dl
      v-if="state.view_configuration"
      class="mcp-artifact-approval__details"
      :aria-label="$t('mcpArtifactApproval.details')"
    >
      <div>
        <dt>{{ $t('mcpArtifactApproval.audienceLabel') }}</dt>
        <dd>
          {{
            state.audience
              ? $t(`mcpArtifactApproval.audiences.${state.audience}`)
              : '—'
          }}
        </dd>
      </div>
      <div>
        <dt>{{ $t('mcpArtifactApproval.endpointLabel') }}</dt>
        <dd>#{{ state.endpoint_id ?? '—' }}</dd>
      </div>
      <div>
        <dt>{{ $t('mcpArtifactApproval.viewLabel') }}</dt>
        <dd>#{{ state.view_id }}</dd>
      </div>
      <div>
        <dt>{{ $t('mcpArtifactApproval.configurationLabel') }}</dt>
        <dd>
          {{
            $t('mcpArtifactApproval.configurationSummary', {
              rows: state.view_configuration.row_limit,
              filters: state.view_configuration.filter_count,
              sorts: state.view_configuration.sort_count,
              groups: state.view_configuration.group_count,
            })
          }}
        </dd>
      </div>
      <div
        v-if="state.manifest?.length"
        class="mcp-artifact-approval__manifest"
      >
        <dt>{{ $t('mcpArtifactApproval.manifestLabel') }}</dt>
        <dd>
          <ul>
            <li v-for="field in state.manifest" :key="field.field_id">
              {{ $t('mcpArtifactApproval.field', { id: field.field_id }) }}
              ·
              {{ $t(`mcpArtifactApproval.provenance.${field.provenance}`) }}
            </li>
          </ul>
        </dd>
      </div>
    </dl>
    <button
      v-if="state.artifact_state === 'pending_approval' && state.draft_id"
      type="button"
      class="button button--small button--primary"
      :disabled="saving"
      :data-test-id="'approve-mcp-artifact'"
      @click="approve"
    >
      {{
        saving
          ? $t('mcpArtifactApproval.approving')
          : $t('mcpArtifactApproval.approve')
      }}
    </button>
  </div>
</template>

<script>
import ArtifactApprovalService from '@jadawel/modules/arabase/mcp/services/artifactApproval'

export default {
  name: 'McpArtifactApprovalPanel',
  props: {
    view: { type: Object, required: true },
    readOnly: { type: Boolean, required: true },
    canUpdate: { type: Boolean, required: true },
  },
  emits: ['approved'],
  data() {
    return {
      state: null,
      saving: false,
    }
  },
  computed: {
    visible() {
      return !this.readOnly && this.canUpdate
    },
    stateLabel() {
      if (!this.state) {
        return ''
      }
      return this.$t(`mcpArtifactApproval.states.${this.state.artifact_state}`)
    },
  },
  watch: {
    'view.id'() {
      this.load()
    },
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      if (!this.visible) {
        this.state = null
        return
      }
      try {
        const { data } = await ArtifactApprovalService(this.$client).fetchState(
          this.view.id
        )
        this.state = data
      } catch {
        // A page without an MCP artifact is the normal path. Keep this panel
        // silent when the state endpoint is unavailable to a read-only user.
        this.state = null
      }
    },
    async approve() {
      if (!this.state?.draft_id) {
        return
      }
      this.saving = true
      try {
        const { data } = await ArtifactApprovalService(
          this.$client
        ).approveDraft(this.state.draft_id)
        this.state = data
        this.$emit('approved')
      } finally {
        this.saving = false
      }
    },
  },
}
</script>
