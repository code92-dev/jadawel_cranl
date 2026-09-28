<template>
  <Modal ref="modal" wide>
    <div class="widget-gallery">
      <div class="widget-gallery__header">
        <h2 class="widget-gallery__title">{{ $t('widgetGallery.title') }}</h2>
        <p class="widget-gallery__subtitle">
          {{ $t('widgetGallery.subtitle') }}
        </p>
      </div>
      <section
        v-for="section in sections"
        :key="section.category"
        class="widget-gallery__section"
      >
        <h3 class="widget-gallery__section-title">
          {{ $t(`widgetGallery.category.${section.category}`) }}
        </h3>
        <div class="widget-gallery__grid">
          <button
            v-for="variation in section.variations"
            :key="variation.key"
            type="button"
            class="widget-gallery__card"
            :disabled="creating"
            @click="select(variation)"
          >
            <span class="widget-gallery__preview">
              <img
                :src="variation.createWidgetImage"
                alt=""
                width="120"
                height="72"
              />
            </span>
            <span class="widget-gallery__name">{{ variation.name }}</span>
            <span
              v-if="variation.description"
              class="widget-gallery__description"
              >{{ variation.description }}</span
            >
          </button>
        </div>
      </section>
    </div>
  </Modal>
</template>

<script>
import modal from '@jadawel/modules/core/mixins/modal'
import { WIDGET_CATEGORIES } from '@jadawel/modules/arabase/dashboard/widgetTypes'

/**
 * The "add a widget" gallery: every widget variation, grouped by what it is
 * for — numbers, charts, lists, text — with a preview and one line on when to
 * use it. Replaces core's `CreateWidgetModal`, a flat row of unlabelled tiles.
 *
 * Emits the chosen variation with the size it should be created at, so a key
 * number arrives as a quarter-width card and a list as a wide one rather than
 * every widget spanning the full row.
 */
export default {
  name: 'WidgetGalleryModal',
  mixins: [modal],
  props: {
    dashboard: {
      type: Object,
      required: true,
    },
    creating: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['select'],
  computed: {
    variations() {
      return this.$registry
        .getOrderedList('dashboardWidget')
        .filter((type) => type.isAvailable(this.dashboard.workspace?.id))
        .flatMap((type) =>
          type.variations.map((variation, index) => ({
            ...variation,
            key: `${type.getType()}-${index}`,
            category: variation.category || type.category || 'numbers',
            size: variation.size || type.defaultSize || null,
          }))
        )
    },
    sections() {
      const known = WIDGET_CATEGORIES.map((category) => ({
        category,
        variations: this.variations.filter((v) => v.category === category),
      }))
      return known.filter((section) => section.variations.length > 0)
    },
  },
  methods: {
    select(variation) {
      this.$emit('select', variation)
      this.hide()
    },
  },
}
</script>
