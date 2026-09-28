<template>
  <div class="step-gallery">
    <div class="step-gallery__search">
      <i class="iconoir-search"></i>
      <input
        ref="search"
        v-model="search"
        type="text"
        class="step-gallery__search-input"
        :placeholder="$t('automationSteps.search')"
        @keydown.enter.prevent="selectFirst"
      />
    </div>
    <!-- Every category one click away, however long the list below. -->
    <div v-if="!search && sections.length > 1" class="step-gallery__jumps">
      <button
        v-for="section in sections"
        :key="section.category"
        type="button"
        class="step-gallery__jump"
        @click="jump(section.category)"
      >
        <span
          class="step-gallery__jump-dot"
          :class="`step-chip--${section.tone}`"
        ></span>
        {{ categoryName(section.category) }}
      </button>
    </div>
    <div ref="sections" class="step-gallery__sections">
      <section
        v-for="section in sections"
        :key="section.category"
        :data-category="section.category"
        class="step-gallery__section"
      >
        <h4 class="step-gallery__section-title">
          {{ categoryName(section.category) }}
        </h4>
        <button
          v-for="nodeType in section.nodeTypes"
          :key="nodeType.getType()"
          type="button"
          class="step-gallery__item"
          @click="$emit('select', nodeType.getType())"
        >
          <span
            class="step-chip"
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
          <span class="step-gallery__text">
            <span class="step-gallery__name">{{ nameOf(nodeType) }}</span>
            <span class="step-gallery__description">{{
              descriptionOf(nodeType)
            }}</span>
          </span>
        </button>
      </section>
      <p v-if="sections.length === 0" class="step-gallery__empty">
        {{ $t('automationSteps.noResults') }}
      </p>
    </div>
  </div>
</template>

<script>
import {
  stepDescription,
  stepEntry,
  stepName,
  stepSections,
} from '@jadawel/modules/arabase/automation/stepCatalog'

/**
 * Every step that can be added (or every event that can start the workflow),
 * grouped by what it is for, with a plain-language name and one line on when
 * to use it. Replaces core's flat list of service names.
 */
export default {
  name: 'StepGallery',
  props: {
    nodeTypes: {
      type: Array,
      required: true,
    },
    trigger: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['select'],
  data() {
    return { search: '' }
  },
  computed: {
    sections() {
      return stepSections(this.nodeTypes, {
        trigger: this.trigger,
        search: this.search,
        describe: (type) => [this.nameOf(type), this.descriptionOf(type)],
      })
    },
  },
  methods: {
    categoryName(category) {
      return this.$t(
        `automationSteps.${this.trigger ? 'triggerCategories' : 'categories'}.${category}`
      )
    },
    jump(category) {
      const list = this.$refs.sections
      const section = list?.querySelector(`[data-category="${category}"]`)
      if (section) {
        list.scrollTop = section.offsetTop
      }
    },
    entryOf(nodeType) {
      return stepEntry(nodeType)
    },
    nameOf(nodeType) {
      return stepName(this, nodeType)
    },
    descriptionOf(nodeType) {
      return stepDescription(this, nodeType)
    },
    selectFirst() {
      const first = this.sections[0]?.nodeTypes[0]
      if (first) {
        this.$emit('select', first.getType())
      }
    },
    focus() {
      this.$refs.search?.focus()
    },
  },
}
</script>
