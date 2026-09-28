<template>
  <div
    v-if="readiness.total > 0"
    class="workflow-overview"
    :class="{ 'workflow-overview--ready': allReady }"
  >
    <span
      class="workflow-overview__meter"
      :style="{ '--progress': `${progress}%` }"
      role="img"
      :aria-label="statusText"
    >
      <i :class="allReady ? 'iconoir-check' : 'iconoir-tools'"></i>
    </span>
    <span class="workflow-overview__status">{{ statusText }}</span>
    <span class="workflow-overview__steps">
      <template v-for="(step, index) in readiness.steps" :key="step.node.id">
        <i
          v-if="index > 0"
          class="iconoir-nav-arrow-right workflow-overview__arrow"
          aria-hidden="true"
        ></i>
        <button
          v-tooltip="labelOf(step)"
          type="button"
          class="step-chip workflow-overview__step"
          :class="[
            `step-chip--${step.tone}`,
            {
              'workflow-overview__step--selected': step.node.id === selectedId,
              'workflow-overview__step--setup': step.needsSetup,
            },
          ]"
          :aria-label="labelOf(step)"
          @click="$emit('select', step.node.id)"
        >
          <img v-if="step.image" :src="step.image" alt="" />
          <i v-else :class="step.icon"></i>
        </button>
      </template>
    </span>
    <Button
      v-if="readiness.next"
      type="secondary"
      size="small"
      icon="iconoir-arrow-right"
      class="workflow-overview__next"
      @click="$emit('select', readiness.next.node.id)"
      >{{ $t('workflowOverview.setUpNext') }}</Button
    >
  </div>
</template>

<script>
import {
  counted,
  workflowReadiness,
} from '@jadawel/modules/arabase/automation/stepCatalog'

/**
 * A floating bar over the canvas: how many steps are set up, the workflow as a
 * row of step icons (a dot marks each one that still needs setting up; any of
 * them opens that step), and the way to the next step to finish.
 */
export default {
  name: 'WorkflowOverview',
  props: {
    workflow: {
      type: Object,
      required: true,
    },
    automation: {
      type: Object,
      required: true,
    },
    selectedId: {
      type: [Number, String],
      required: false,
      default: null,
    },
  },
  emits: ['select'],
  computed: {
    readiness() {
      return workflowReadiness(this.workflow, this.$registry)
    },
    allReady() {
      return this.readiness.ready === this.readiness.total
    },
    progress() {
      const { ready, total } = this.readiness
      return total ? Math.round((ready / total) * 100) : 0
    },
    statusText() {
      const { ready, total } = this.readiness
      return this.allReady
        ? counted(this, 'workflowOverview.allReady', total)
        : this.$t('workflowOverview.progress', { ready, total })
    },
  },
  methods: {
    labelOf(step) {
      const label = step.nodeType.getLabel({
        automation: this.automation,
        node: step.node,
      })
      return step.needsSetup
        ? this.$t('workflowOverview.needsSetup', { label })
        : label
    },
  },
}
</script>
