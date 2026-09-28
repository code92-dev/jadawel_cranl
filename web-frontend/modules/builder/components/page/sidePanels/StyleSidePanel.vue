<template>
  <div v-if="elementType && element">
    <!-- Jadawel fork: card, tinted and outlined boxes in one click. -->
    <ElementQuickStyles
      v-if="hasQuickStyles"
      :element="element"
      :theme="builder.theme"
      :disabled="!canUpdate"
      @apply="applyQuickStyle"
    />
    <component
      :is="elementType.styleFormComponent"
      ref="panelForm"
      :key="`${element.id}-${revision}`"
      :element="element"
      :parent-element="parentElement"
      :default-values="defaultValues"
      @values-changed="onChange($event)"
    ></component>
  </div>
</template>

<script>
import elementSidePanel from '@jadawel/modules/builder/mixins/elementSidePanel'
import ElementQuickStyles from '@jadawel/modules/arabase/builder/components/ElementQuickStyles'
import { QUICK_STYLE_ELEMENTS } from '@jadawel/modules/arabase/builder/elementQuickStyles'

export default {
  name: 'StyleSidePanel',
  components: { ElementQuickStyles },
  mixins: [elementSidePanel],
  data() {
    // Jadawel fork: bumped after a quick style, so the form below, which
    // copies the element's values when it is created, shows the new ones.
    return { revision: 0 }
  },
  computed: {
    hasQuickStyles() {
      return QUICK_STYLE_ELEMENTS.includes(this.element.type)
    },
    canUpdate() {
      return this.$hasPermission(
        'builder.page.element.update',
        this.element,
        this.workspace.id
      )
    },
  },
  methods: {
    async applyQuickStyle(values) {
      await this.onChange(values)
      this.revision++
    },
  },
}
</script>
