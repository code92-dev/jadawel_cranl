<template>
  <div class="workflow-start">
    <div class="workflow-start__inner">
      <div class="workflow-start__intro">
        <span class="workflow-start__badge" aria-hidden="true">
          <i class="iconoir-flash"></i>
        </span>
        <h2 class="workflow-start__title">
          {{ $t('workflowStart.title') }}
        </h2>
        <p class="workflow-start__subtitle">
          {{
            readOnly
              ? $t('workflowStart.readOnly')
              : $t('workflowStart.subtitle')
          }}
        </p>
      </div>

      <section class="workflow-start__section">
        <h3 class="workflow-start__section-title">
          <i class="iconoir-magic-wand"></i>
          {{ $t('workflowStart.recipes') }}
        </h3>
        <div
          v-for="section in recipeSections"
          :key="section.category"
          class="workflow-start__group"
        >
          <h4 class="workflow-start__group-title">
            {{ $t(`automationRecipes.categories.${section.category}`) }}
          </h4>
          <div class="workflow-start__recipes">
            <button
              v-for="recipe in section.recipes"
              :key="recipe.key"
              type="button"
              class="recipe-card"
              :disabled="readOnly || busy !== null"
              @click="$emit('recipe', recipe)"
            >
              <span class="recipe-card__flow" aria-hidden="true">
                <template
                  v-for="(step, index) in recipeFlow(recipe)"
                  :key="index"
                >
                  <i
                    v-if="index > 0"
                    class="iconoir-arrow-right recipe-card__arrow"
                  ></i>
                  <span
                    class="step-chip"
                    :class="`step-chip--${step.entry.tone}`"
                  >
                    <img
                      v-if="step.entry.image"
                      :src="step.entry.image"
                      alt=""
                    />
                    <i v-else :class="step.entry.icon"></i>
                  </span>
                  <!-- The steps a loop runs for each item, framed. -->
                  <span v-if="step.children.length" class="recipe-card__loop">
                    <span
                      v-for="(child, childIndex) in step.children"
                      :key="childIndex"
                      class="step-chip"
                      :class="`step-chip--${child.tone}`"
                    >
                      <img v-if="child.image" :src="child.image" alt="" />
                      <i v-else :class="child.icon"></i>
                    </span>
                  </span>
                </template>
                <span v-if="busy === recipe.key" class="recipe-card__loading">
                  <span class="loading"></span>
                </span>
              </span>
              <span class="recipe-card__name">{{
                $t(`automationRecipes.recipes.${recipe.key}.name`)
              }}</span>
              <span class="recipe-card__description">{{
                $t(`automationRecipes.recipes.${recipe.key}.description`)
              }}</span>
              <span class="recipe-card__meta">{{
                stepCount(recipeTypes(recipe).length)
              }}</span>
            </button>
          </div>
        </div>
      </section>

      <section class="workflow-start__section">
        <h3 class="workflow-start__section-title">
          <i class="iconoir-flash"></i>
          {{ $t('workflowStart.events') }}
        </h3>
        <div
          v-for="section in triggerSections"
          :key="section.category"
          class="workflow-start__group"
        >
          <h4 class="workflow-start__group-title">
            {{ $t(`automationSteps.triggerCategories.${section.category}`) }}
          </h4>
          <div class="workflow-start__events">
            <button
              v-for="nodeType in section.nodeTypes"
              :key="nodeType.getType()"
              type="button"
              class="event-card"
              :disabled="readOnly || busy !== null"
              @click="$emit('add-trigger', nodeType.getType())"
            >
              <span
                class="step-chip step-chip--large"
                :class="`step-chip--${section.tone}`"
                aria-hidden="true"
              >
                <img
                  v-if="entryOf(nodeType).image"
                  :src="entryOf(nodeType).image"
                  alt=""
                />
                <i v-else :class="entryOf(nodeType).icon"></i>
              </span>
              <span class="event-card__text">
                <span class="event-card__name">{{ nameOf(nodeType) }}</span>
                <span class="event-card__description">{{
                  descriptionOf(nodeType)
                }}</span>
              </span>
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import {
  counted,
  stepDescription,
  stepEntry,
  stepName,
  stepSections,
} from '@jadawel/modules/arabase/automation/stepCatalog'
import {
  recipeSections,
  recipeTypes,
} from '@jadawel/modules/arabase/automation/recipes'

/**
 * An empty workflow: recipes that build a whole working flow in one click, and
 * every event that can start one, grouped by what sets it off. Replaces core's
 * "Choose an event…" list.
 */
export default {
  name: 'WorkflowStart',
  props: {
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
    // The recipe being built, while it is.
    busy: {
      type: String,
      required: false,
      default: null,
    },
  },
  emits: ['recipe', 'add-trigger'],
  computed: {
    recipeSections() {
      return recipeSections(this.$registry)
    },
    triggerSections() {
      const triggers = this.$registry
        .getOrderedList('node')
        .filter((nodeType) => nodeType.isTrigger)
      return stepSections(triggers, { trigger: true })
    },
  },
  methods: {
    entryOf(nodeType) {
      return stepEntry(nodeType)
    },
    nameOf(nodeType) {
      return stepName(this, nodeType)
    },
    stepCount(count) {
      return counted(this, 'workflowStart.steps', count)
    },
    descriptionOf(nodeType) {
      return stepDescription(this, nodeType)
    },
    recipeTypes(recipe) {
      return recipeTypes(recipe)
    },
    /** The recipe as chips: each step, with the steps inside a loop. */
    recipeFlow(recipe) {
      const entry = (type) => stepEntry(this.$registry.get('node', type))
      return [recipe.trigger, ...recipe.steps].map((step) => {
        const { type, children = [] } =
          typeof step === 'string' ? { type: step } : step
        return { entry: entry(type), children: children.map(entry) }
      })
    },
  },
}
</script>
