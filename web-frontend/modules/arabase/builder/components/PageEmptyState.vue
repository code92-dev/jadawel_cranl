<template>
  <div
    class="page-empty"
    :class="{
      'page-empty--drag-active': isValidDropTarget,
      'page-empty--drag-over': isDragOver,
    }"
    @dragenter="onDragEnter"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <div class="page-empty__sketch" aria-hidden="true">
      <span class="page-empty__band">
        <span class="page-empty__logo"></span>
        <span class="page-empty__nav"></span>
        <span class="page-empty__nav"></span>
        <span class="page-empty__nav"></span>
      </span>
      <span class="page-empty__hero">
        <span class="page-empty__title"></span>
        <span class="page-empty__line"></span>
        <span class="page-empty__button"></span>
      </span>
      <span class="page-empty__cards">
        <span class="page-empty__card"></span>
        <span class="page-empty__card"></span>
        <span class="page-empty__card"></span>
      </span>
    </div>
    <h2 class="page-empty__heading">{{ $t('pageEmpty.title') }}</h2>
    <p class="page-empty__text">{{ $t('pageEmpty.text') }}</p>
    <Button
      type="primary"
      size="large"
      icon="iconoir-plus"
      @click="$emit('add-element')"
      >{{ $t('pageEmpty.addElement') }}</Button
    >
    <div class="page-empty__starts">
      <span class="page-empty__starts-label">{{
        $t('pageEmpty.quickStart')
      }}</span>
      <button
        v-for="start in starts"
        :key="start.type"
        type="button"
        class="page-empty__start"
        :disabled="creating !== null"
        @click="create(start.type)"
      >
        <span v-if="creating === start.type" class="loading"></span>
        <i v-else :class="start.icon"></i>
        {{ start.name }}
      </button>
    </div>
  </div>
</template>

<script>
import { inject } from 'vue'
import { useDropElementTarget } from '@jadawel/modules/builder/composables/useDropElementTarget'
import { notifyIf } from '@jadawel/modules/core/utils/error'

// What most pages start with, in the order they are usually added.
const QUICK_STARTS = ['heading', 'text', 'column', 'table', 'form_container']

/**
 * A page with no elements yet: a sketch of a finished page, one button to the
 * element gallery and the few elements most pages start with, created in one
 * click. Replaces core's bare "+" zone; like it, it accepts an element dragged
 * in from the header or the footer.
 */
export default {
  name: 'PageEmptyState',
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  emits: ['add-element'],
  setup(props) {
    return {
      builder: inject('builder'),
      ...useDropElementTarget({ parentElement: null, page: props.page }),
    }
  },
  data() {
    return { creating: null }
  },
  computed: {
    starts() {
      return QUICK_STARTS.filter((type) =>
        this.$registry.exists('element', type)
      )
        .map((type) => this.$registry.get('element', type))
        .map((elementType) => ({
          type: elementType.getType(),
          name: elementType.name,
          icon: elementType.iconClass,
        }))
    },
  },
  methods: {
    async create(type) {
      this.creating = type
      try {
        await this.$store.dispatch('element/create', {
          builder: this.builder,
          page: this.page,
          elementType: type,
        })
      } catch (error) {
        notifyIf(error)
      }
      this.creating = null
    },
  },
}
</script>
