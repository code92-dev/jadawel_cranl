<template>
  <!-- Jadawel fork: a card of the element gallery, with a preview and when to
  use the element. -->
  <div class="element-gallery__item">
    <button
      v-tooltip="disabled ? isDisallowedReason : null"
      type="button"
      class="element-gallery__card"
      :class="{ 'element-gallery__card--disabled': disabled }"
      :aria-disabled="disabled"
      @click.stop="onClick"
    >
      <span class="element-gallery__preview">
        <img :src="entry.tile" alt="" width="120" height="72" />
        <span v-if="loading" class="element-gallery__loading">
          <span class="loading"></span>
        </span>
      </span>
      <span class="element-gallery__name">{{ elementType.name }}</span>
      <span class="element-gallery__description">{{ description }}</span>
    </button>
    <component
      :is="disallowedClickModal[0]"
      v-if="disallowedClickModal !== null"
      ref="deactivatedClickModal"
      v-bind="disallowedClickModal[1]"
      :name="elementType.name"
      :workspace="workspace"
    ></component>
  </div>
</template>

<script>
import {
  ELEMENT_GALLERY,
  galleryEntry,
} from '@jadawel/modules/arabase/builder/elementGallery'

export default {
  name: 'AddElementCard',
  props: {
    elementType: {
      type: Object,
      required: true,
    },
    workspace: {
      type: Object,
      required: true,
    },
    builder: {
      type: Object,
      required: true,
    },
    page: {
      type: Object,
      required: true,
    },
    placeInContainer: {
      type: String,
      required: false,
      default: undefined,
    },
    parentElement: {
      type: Object,
      required: false,
      default: undefined,
    },
    beforeElement: {
      type: Object,
      required: false,
      default: undefined,
    },
    pagePlace: {
      type: String,
      required: false,
      default: undefined,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['click'],
  computed: {
    entry() {
      return galleryEntry(this.elementType)
    },
    description() {
      const type = this.elementType.getType()
      return ELEMENT_GALLERY[type]
        ? this.$t(`elementGallery.elements.${type}`)
        : this.elementType.description
    },
    disallowedClickModal() {
      return this.elementType.getDeactivatedClickModal({
        workspace: this.workspace,
      })
    },
    isDisallowedReason() {
      return this.elementType.isDisallowedReason({
        workspace: this.workspace,
        builder: this.builder,
        page: this.page,
        placeInContainer: this.placeInContainer,
        parentElement: this.parentElement,
        beforeElement: this.beforeElement,
        pagePlace: this.pagePlace,
      })
    },
    disabled() {
      return !!this.isDisallowedReason
    },
  },
  methods: {
    onClick(event) {
      if (this.disallowedClickModal !== null) {
        this.$refs.deactivatedClickModal.show()
      } else if (!this.disabled) {
        this.$emit('click', event)
      }
    },
  },
}
</script>
