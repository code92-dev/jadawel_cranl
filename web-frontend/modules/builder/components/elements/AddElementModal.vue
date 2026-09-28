<template>
  <!-- Jadawel fork: the element gallery (modules/arabase/builder/elementGallery.js). -->
  <Modal ref="modal" wide class="add-element-modal">
    <div class="element-gallery">
      <div class="element-gallery__header">
        <div class="element-gallery__heading">
          <h2 class="element-gallery__title">
            {{ $t('addElementModal.title') }}
          </h2>
          <p class="element-gallery__subtitle">
            {{ $t('elementGallery.subtitle') }}
          </p>
        </div>
        <FormInput
          ref="search"
          v-model="search"
          class="element-gallery__search"
          :placeholder="$t('elementGallery.search')"
          icon-left="iconoir-search"
        />
      </div>
      <section
        v-for="section in sections"
        :key="section.category"
        class="element-gallery__section"
      >
        <h3 class="element-gallery__section-title">
          {{ $t(`elementGallery.category.${section.category}`) }}
        </h3>
        <div class="element-gallery__grid">
          <AddElementCard
            v-for="elementType in section.elementTypes"
            :key="elementType.getType()"
            :element-type="elementType"
            :loading="addingElementType === elementType.getType()"
            :workspace="workspace"
            :builder="builder"
            :page="page"
            :place-in-container="placeInContainer"
            :parent-element="parentElement"
            :before-element="beforeElement"
            :page-place="pagePlace"
            @click="addElement(elementType)"
          />
        </div>
      </section>
      <div v-if="sections.length === 0" class="element-gallery__empty">
        <i class="iconoir-search"></i>
        {{ $t('elementGallery.noResults') }}
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@jadawel/modules/core/mixins/modal'
import AddElementCard from '@jadawel/modules/builder/components/elements/AddElementCard'
import {
  ELEMENT_GALLERY,
  gallerySections,
} from '@jadawel/modules/arabase/builder/elementGallery'
import { notifyIf } from '@jadawel/modules/core/utils/error'
import { mapActions } from 'vuex'
import { PAGE_PLACES } from '@jadawel/modules/builder/enums'

export default {
  name: 'AddElementModal',
  components: { AddElementCard },
  mixins: [modal],
  inject: ['workspace', 'builder', 'currentPage'],
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
  emits: ['element-added'],
  data() {
    return {
      search: '',
      placeInContainer: null,
      beforeId: null,
      parentElementId: null,
      pagePlace: null,
      addingElementType: null,
    }
  },
  computed: {
    sections() {
      return gallerySections(Object.values(this.$registry.getAll('element')), {
        search: this.search,
        describe: (type) =>
          ELEMENT_GALLERY[type.getType()]
            ? this.$t(`elementGallery.elements.${type.getType()}`)
            : '',
      })
    },
    sharedPage() {
      return this.$store.getters['page/getSharedPage'](this.builder)
    },
    parentElement() {
      if (this.parentElementId) {
        return this.$store.getters['element/getElementByIdInPages'](
          [this.currentPage, this.sharedPage],
          this.parentElementId
        )
      }
      return null
    },
    beforeElement() {
      if (this.beforeId) {
        return this.$store.getters['element/getElementByIdInPages'](
          [this.currentPage, this.sharedPage],
          this.beforeId
        )
      }
      return null
    },
  },
  methods: {
    ...mapActions({
      actionCreateElement: 'element/create',
    }),

    async show(
      { placeInContainer, beforeId, parentElementId, pagePlace } = {},
      ...args
    ) {
      this.placeInContainer = placeInContainer
      this.beforeId = beforeId
      this.parentElementId = parentElementId
      this.pagePlace = pagePlace
      modal.methods.show.bind(this)(...args)

      await this.$nextTick()
      // Let's focus search input
      this.$refs.search.focus()
    },

    async addElement(elementType) {
      this.addingElementType = elementType.getType()

      let beforeId = this.beforeId
      let destinationPage

      if (this.parentElementId) {
        // The page must be the same as the parent one
        destinationPage =
          this.parentElement.page_id === this.currentPage.id
            ? this.currentPage
            : this.sharedPage
      } else {
        // The page is forced by the element type page place
        destinationPage =
          elementType.getPagePlace() === PAGE_PLACES.CONTENT
            ? this.currentPage
            : this.sharedPage
        // If the before element doesn't belong to the same page we must ignore it
        if (
          this.beforeElement &&
          this.beforeElement.page_id !== destinationPage.id
        ) {
          beforeId = null
        }
      }

      try {
        await this.actionCreateElement({
          builder: this.builder,
          page: destinationPage,
          elementType: elementType.getType(),
          beforeId,
          values: {
            parent_element_id: this.parentElementId,
            place_in_container: this.placeInContainer,
          },
        })

        this.$emit('element-added')
        this.hide()
      } catch (error) {
        notifyIf(error)
      }
      this.addingElementType = null
    },
  },
}
</script>
