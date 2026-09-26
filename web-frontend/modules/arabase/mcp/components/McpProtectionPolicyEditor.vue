<template>
  <section class="mcp-protection-editor" aria-live="polite">
    <div v-if="loading" class="loading"></div>
    <template v-else-if="policy">
      <h3>{{ $t('mcpProtection.editTitle') }}</h3>
      <p>{{ $t('mcpProtection.editHelp') }}</p>
      <p
        v-if="readOnly"
        class="mcp-protection-editor__status"
        role="alert"
        data-test-id="protection-read-only"
      >
        {{ $t('mcpProtection.readOnly') }}
      </p>
      <p
        v-if="conflict"
        class="mcp-protection-editor__status"
        role="alert"
        data-test-id="protection-conflict"
      >
        {{ $t('mcpProtection.revisionConflict') }}
        <button
          type="button"
          class="button button--small"
          :disabled="saving"
          @click="reloadPolicy"
        >
          {{ $t('mcpProtection.reloadAndCompare') }}
        </button>
      </p>
      <p
        v-if="policy.lifecycle_status !== 'active'"
        class="mcp-protection-editor__status"
      >
        {{ $t('mcpProtection.protectionSuspended') }}
        <button
          type="button"
          class="button button--small"
          :disabled="saving || readOnly"
          @click="reactivate"
        >
          {{ $t('mcpProtection.reactivate') }}
        </button>
      </p>
      <McpProtectionFieldSelector
        v-model="selectedFields"
        :databases="databases"
        :disabled="readOnly"
        @status="metadataStatus = $event"
      />
      <dl class="mcp-protection-editor__diff" aria-live="polite">
        <div>
          <dt>{{ $t('mcpProtection.addedFields') }}</dt>
          <dd>{{ addedFieldIds.length }}</dd>
        </div>
        <div>
          <dt>{{ $t('mcpProtection.removedFields') }}</dt>
          <dd>{{ removedFieldIds.length }}</dd>
        </div>
        <div>
          <dt>{{ $t('mcpProtection.unchangedFields') }}</dt>
          <dd>{{ unchangedFieldIds.length }}</dd>
        </div>
        <div v-if="unavailableFieldIds.length">
          <dt>{{ $t('mcpProtection.unavailableFields') }}</dt>
          <dd>{{ unavailableFieldIds.length }}</dd>
        </div>
      </dl>
      <section
        v-if="unavailableFieldIds.length"
        class="mcp-protection-editor__unavailable"
        role="status"
        aria-live="polite"
      >
        <h4>{{ $t('mcpProtection.unavailableFields') }}</h4>
        <p>{{ $t('mcpProtection.unavailableFieldsHelp') }}</p>
        <ul>
          <li
            v-for="field in unavailableFields"
            :key="field.id"
            :data-test-id="`unavailable-protected-field-${field.id}`"
          >
            <bdi>
              {{
                field.name ||
                $t('mcpProtection.unavailableField', { id: field.id })
              }}
            </bdi>
            <span>{{ $t('mcpProtection.protectedUntilResolved') }}</span>
          </li>
        </ul>
      </section>
      <label
        v-if="removedFieldIds.length && !readOnly"
        class="mcp-protection-editor__confirm"
      >
        <input v-model="confirmRemoval" type="checkbox" />
        {{ $t('mcpProtection.confirmRemoval') }}
      </label>
      <p v-if="removedFieldIds.length" class="mcp-protection-editor__warning">
        {{ $t('mcpProtection.removalWarning') }}
      </p>
      <Error :error="error"></Error>
      <div class="mcp-protection-flow__actions">
        <button type="button" class="button" @click="$emit('cancel')">
          {{ $t('mcpProtection.cancel') }}
        </button>
        <button
          type="button"
          class="button button--primary"
          :disabled="
            readOnly ||
            saving ||
            metadataStatus.loading ||
            metadataStatus.error ||
            (removedFieldIds.length > 0 && !confirmRemoval)
          "
          @click="save"
        >
          {{ $t('mcpProtection.saveChanges') }}
        </button>
      </div>
    </template>
  </section>
</template>

<script>
import { uuid } from '@jadawel/modules/core/utils/string'
import error from '@jadawel/modules/core/mixins/error'
import McpProtectionFieldSelector from '@jadawel/modules/arabase/mcp/components/McpProtectionFieldSelector'
import ProtectionPolicyService from '@jadawel/modules/arabase/mcp/services/protectionPolicy'
import { protectionErrorMap } from '@jadawel/modules/arabase/mcp/protectionErrors'
import { databasesInWorkspace } from '@jadawel/modules/arabase/mcp/selection'

export default {
  name: 'McpProtectionPolicyEditor',
  components: { McpProtectionFieldSelector },
  mixins: [error],
  props: {
    endpoint: { type: Object, required: true },
    applications: { type: Array, required: true },
  },
  emits: ['cancel', 'saved'],
  data() {
    return {
      policy: null,
      selectedFields: [],
      loading: true,
      saving: false,
      confirmRemoval: false,
      idempotencyKey: uuid(),
      metadataStatus: { loading: false, error: false },
      conflict: false,
      readOnly: false,
    }
  },
  computed: {
    databases() {
      return databasesInWorkspace(this.applications, this.endpoint.workspace_id)
    },
    removedFieldIds() {
      const selected = new Set(this.selectedFields.map((field) => field.id))
      return (this.policy?.fields || [])
        .map((field) => field.id)
        .filter((fieldId) => !selected.has(fieldId))
    },
    addedFieldIds() {
      const existing = new Set(
        (this.policy?.fields || []).map((field) => field.id)
      )
      return this.selectedFields
        .map((field) => field.id)
        .filter((fieldId) => !existing.has(fieldId))
    },
    unchangedFieldIds() {
      const existing = new Set(
        (this.policy?.fields || []).map((field) => field.id)
      )
      return this.selectedFields
        .map((field) => field.id)
        .filter((fieldId) => existing.has(fieldId))
    },
    unavailableFieldIds() {
      return (this.policy?.fields || [])
        .filter((field) => !field.name || !field.table || !field.database)
        .map((field) => field.id)
    },
    unavailableFields() {
      const unavailable = new Set(this.unavailableFieldIds)
      return (this.policy?.fields || []).filter((field) =>
        unavailable.has(field.id)
      )
    },
  },
  async mounted() {
    await this.loadPolicy()
  },
  methods: {
    async loadPolicy() {
      this.loading = true
      this.hideError()
      try {
        const { data } = await ProtectionPolicyService(
          this.$client
        ).fetchPolicy(this.endpoint.id)
        this.policy = data
        this.selectedFields = data.fields.map((field) => ({
          id: field.id,
          name: field.name,
          type: field.type,
          table: field.table,
          database: field.database,
        }))
        this.conflict = false
      } catch (loadError) {
        if (
          loadError?.response?.status === 403 ||
          loadError?.response?.status === 401 ||
          loadError?.response?.status === 404
        ) {
          this.readOnly = true
        } else {
          this.handleError(loadError, 'endpoint')
        }
      } finally {
        this.loading = false
      }
    },
    async save() {
      if (
        this.readOnly ||
        this.metadataStatus.loading ||
        this.metadataStatus.error
      ) {
        return
      }
      this.saving = true
      this.hideError()
      try {
        const { data } = await ProtectionPolicyService(
          this.$client
        ).replacePolicy(
          this.endpoint.id,
          {
            protected_field_ids: this.selectedFields.map((field) => field.id),
            expected_revision: this.policy.revision,
            confirm_remove_field_ids: this.removedFieldIds,
          },
          this.idempotencyKey
        )
        this.idempotencyKey = uuid()
        this.conflict = false
        this.$emit('saved', data)
      } catch (saveError) {
        this.policyWriteFailed(saveError, protectionErrorMap(this.$t))
      } finally {
        this.saving = false
      }
    },
    async reactivate() {
      if (this.readOnly) return
      this.saving = true
      this.hideError()
      try {
        const { data } = await ProtectionPolicyService(
          this.$client
        ).reactivatePolicy(this.endpoint.id, this.policy.revision)
        this.$emit('saved', data)
      } catch (reactivationError) {
        this.policyWriteFailed(reactivationError, protectionErrorMap(this.$t))
      } finally {
        this.saving = false
      }
    },
    /**
     * Shared failure handling for save and reactivate: a 409 revision
     * conflict shows the conflict notice, lost permission switches to
     * read-only and anything else goes through the error mixin with the
     * optional map. A 409 `MCP_PROTECTION_NOT_READY` from reactivation is not
     * a conflict: reloading would not help, so it goes to the error mixin,
     * which explains why protection stays paused.
     */
    policyWriteFailed(error, errorMap = null) {
      const status = error?.response?.status
      const code = error?.response?.data?.error
      if (status === 409 && code !== 'MCP_PROTECTION_NOT_READY') {
        this.conflict = true
      } else if (status === 401 || status === 403) {
        this.readOnly = true
      } else {
        this.handleError(error, 'endpoint', errorMap)
      }
    },
    async reloadPolicy() {
      await this.loadPolicy()
      this.confirmRemoval = false
    },
  },
}
</script>
