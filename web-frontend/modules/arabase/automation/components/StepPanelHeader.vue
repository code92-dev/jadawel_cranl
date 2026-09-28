<template>
  <div class="step-panel-header" :class="`step-panel-header--${entry.tone}`">
    <span
      class="step-chip step-chip--large"
      :class="`step-chip--${entry.tone}`"
      aria-hidden="true"
    >
      <img v-if="entry.image" :src="entry.image" alt="" />
      <i v-else :class="entry.icon"></i>
    </span>
    <div class="step-panel-header__text">
      <div class="step-panel-header__eyebrow">
        {{
          nodeType.isTrigger
            ? $t('stepPanel.trigger')
            : $t('stepPanel.step', { number: step?.number || '', total })
        }}
        ·
        {{
          $t(
            `automationSteps.${
              nodeType.isTrigger ? 'triggerCategories' : 'categories'
            }.${entry.category}`
          )
        }}
      </div>
      <div class="step-panel-header__name">{{ name }}</div>
      <div class="step-panel-header__description">{{ description }}</div>
      <div
        class="step-panel-header__status"
        :class="{ 'step-panel-header__status--setup': needsSetup }"
      >
        <i
          :class="
            needsSetup ? 'iconoir-warning-circle' : 'iconoir-check-circle'
          "
        ></i>
        {{
          needsSetup
            ? errorMessage || $t('stepPanel.needsSetup')
            : $t('stepPanel.ready')
        }}
      </div>
    </div>
  </div>
</template>

<script>
import {
  stepDescription,
  stepEntry,
  stepName,
  workflowReadiness,
} from '@jadawel/modules/arabase/automation/stepCatalog'

/**
 * The top of a step's settings: which step this is ("Step 2 of 4 · Records"),
 * what it does in plain words, and whether it still needs setting up — with
 * the reason, taken from the step's own validation.
 */
export default {
  name: 'StepPanelHeader',
  props: {
    node: {
      type: Object,
      required: true,
    },
    workflow: {
      type: Object,
      required: true,
    },
  },
  computed: {
    nodeType() {
      return this.$registry.get('node', this.node.type)
    },
    entry() {
      return stepEntry(this.nodeType)
    },
    readiness() {
      return workflowReadiness(this.workflow, this.$registry)
    },
    step() {
      return this.readiness.steps.find((step) => step.node.id === this.node.id)
    },
    total() {
      return this.readiness.total
    },
    name() {
      return stepName(this, this.nodeType)
    },
    description() {
      return stepDescription(this, this.nodeType)
    },
    needsSetup() {
      return Boolean(this.step?.needsSetup)
    },
    errorMessage() {
      try {
        return this.nodeType.getErrorMessage({
          service: this.node.service,
          node: this.node,
        })
      } catch (error) {
        return ''
      }
    },
  },
}
</script>
