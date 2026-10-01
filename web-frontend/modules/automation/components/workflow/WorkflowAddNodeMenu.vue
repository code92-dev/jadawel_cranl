<template>
  <!-- Jadawel fork: steps grouped by purpose, in plain words
  (modules/arabase/automation/stepCatalog.js). -->
  <StepGallery
    :node-types="nodeTypes"
    :trigger="editingTriggerNode"
    @select="onChange"
  />
</template>

<script>
import context from '@jadawel/modules/core/mixins/context'
import StepGallery from '@jadawel/modules/arabase/automation/components/StepGallery'

export default {
  name: 'WorkflowNodeContext',
  components: { StepGallery },
  mixins: [context],
  props: {
    node: {
      type: Object,
      required: false,
      default: () => null,
    },
    onlyTrigger: {
      type: Boolean,
      required: false,
      default: () => false,
    },
  },
  emits: ['change'],
  computed: {
    editingTriggerNode() {
      return this.onlyTrigger
    },
    /**
     * Returns an array of node types that can be listed in the context.
     * If we are offering the option to replace an existing node's type,
     * then we will omit `this.node.type` from the array, and then present
     * other nodes of the same 'category' (i.e. trigger or action). If we
     * aren't replacing an existing node, then we will show all node types
     * for a single category (i.e. trigger or action), depending on whether
     * there is a trigger or not.
     */
    nodeTypes() {
      return this.$registry
        .getOrderedList('node')
        .filter(
          (nodeType) =>
            nodeType.isEnabled() &&
            this.node?.type !== nodeType.type &&
            (this.editingTriggerNode
              ? nodeType.isTrigger
              : nodeType.isWorkflowAction)
        )
    },
  },
  methods: {
    onChange(nodeType) {
      this.$emit('change', nodeType)
    },
  },
}
</script>
