<template>
  <div
    :class="[
      'menu-element__wrapper',
      `menu-element__wrapper--${menuElementAlignment}`,
    ]"
    :style="{ '--alignment': menuAlignment }"
  >
    <template v-if="useCompactMenu">
      <div
        v-if="isEditMode && isCompactMenuOpen"
        class="menu-element__compact-menu-editor-overlay"
        @click.stop
        @mousedown.stop
      />

      <div
        class="menu-element__compact-menu-trigger"
        :style="{
          ...getStyleOverride('burger'),
        }"
      >
        <ABIcon
          :id="compactTriggerId"
          ref="compactTrigger"
          icon="iconoir-menu"
          :class="'menu-element__compact-menu-trigger-icon'"
          is-button
          :aria-label="$t('menuElement.openCompactMenu')"
          :aria-expanded="isCompactMenuOpen ? 'true' : 'false'"
          :aria-controls="isCompactMenuOpen ? compactPanelId : null"
          @click.stop="toggleCompactMenu"
        />
      </div>

      <div
        v-if="isCompactMenuOpen"
        :id="compactPanelId"
        ref="compactPanel"
        role="dialog"
        :aria-label="$t('menuElement.compactMenuLabel')"
        v-click-outside="closeCompactMenu"
        :class="compactPanelClasses"
        :style="{
          ...getStyleOverride('menu'),
          '--alignment': 'flex-start',
        }"
        tabindex="-1"
        @keydown.escape="onPanelEscape"
        @mousedown.stop
        @dragstart.prevent.stop
      >
        <ABIcon
          icon="iconoir-cancel"
          class="menu-element__compact-menu-close"
          is-button
          :aria-label="$t('menuElement.closeCompactMenu')"
          @click="closeCompactMenu({ restoreFocus: false })"
        />
        <div
          v-for="item in element.menu_items"
          :key="item.id"
          :class="`menu-element__menu-item-${item.type}`"
        >
          <MenuItem :menu-item="item" :element="element" />
        </div>

        <div v-if="!element.menu_items.length" class="element--no-value">
          {{ $t('menuElement.missingValue') }}
        </div>
      </div>
    </template>

    <div
      v-else
      :class="menuContainerClasses"
      :style="{ '--alignment': menuAlignment, ...getStyleOverride('menu') }"
    >
      <div
        v-for="item in element.menu_items"
        :key="item.id"
        :class="`menu-element__menu-item-${item.type}`"
      >
        <MenuItem :menu-item="item" :element="element" />
      </div>

      <div v-if="!element.menu_items.length" class="element--no-value">
        {{ $t('menuElement.missingValue') }}
      </div>
    </div>
  </div>
</template>

<script>
import element from '@jadawel/modules/builder/mixins/element'
import { HORIZONTAL_ALIGNMENTS } from '@jadawel/modules/builder/enums'
import MenuItem from '@jadawel/modules/builder/components/elements/components/MenuItem.vue'

/**
 * @typedef MenuElement
 * @property {Array}  menu_items Array of Menu items
 */

export default {
  name: 'MenuElement',
  components: { MenuItem },
  mixins: [element],
  inject: {
    setPagePreviewLocked: {
      default: null,
    },
  },
  data() {
    return {
      compactMenuOpen: false,
      compactPanelId: `menu-element-compact-panel-${this.element.id}`,
      compactTriggerId: `menu-element-compact-trigger-${this.element.id}`,
    }
  },
  computed: {
    compactPanelClasses() {
      return [
        'menu-element__container',
        'menu-element__container--vertical',
        'menu-element__container--compact',
      ]
    },
    menuContainerClasses() {
      return [
        'menu-element__container',
        `menu-element__container--${this.element.orientation}`,
      ]
    },
    menuAlignment() {
      const alignmentsCSS = {
        [HORIZONTAL_ALIGNMENTS.LEFT]: 'flex-start',
        [HORIZONTAL_ALIGNMENTS.CENTER]: 'center',
        [HORIZONTAL_ALIGNMENTS.RIGHT]: 'flex-end',
      }
      return alignmentsCSS[this.menuElementAlignment]
    },
    menuElementAlignment() {
      return this.element.alignment || HORIZONTAL_ALIGNMENTS.LEFT
    },
    useCompactMenu() {
      const deviceType =
        this.$store.getters['page/getDeviceTypeSelected'] || 'desktop'
      return this.element.variant?.[deviceType] === 'compact'
    },
    isCompactMenuOpen() {
      if (this.isEditMode) {
        return this.element._.compactMenuOpen
      }
      return this.compactMenuOpen
    },
  },
  watch: {
    isCompactMenuOpen(isOpen) {
      this.setCompactMenuPreviewLock(this.isEditMode && isOpen)
      if (isOpen) {
        this.$nextTick(() => {
          // Move focus into the panel when it opens so keyboard users are
          // not left behind on the trigger.
          this.$refs.compactPanel?.focus()
        })
      }
    },
  },
  beforeUnmount() {
    this.setCompactMenuPreviewLock(false)
    this.resetEditorCompactMenu()
  },
  methods: {
    toggleCompactMenu() {
      if (this.isEditMode) {
        return
      }
      this.compactMenuOpen = !this.compactMenuOpen
    },
    closeCompactMenu({ restoreFocus = true } = {}) {
      if (this.isEditMode) {
        return
      }
      this.compactMenuOpen = false
      if (restoreFocus) {
        this.$nextTick(() => {
          // Return focus to the trigger so keyboard users keep their place.
          this.$refs.compactTrigger?.$el?.focus()
        })
      }
    },
    onPanelEscape() {
      this.closeCompactMenu()
    },
    setCompactMenuPreviewLock(locked) {
      // the setPagePreviewLocked is not provided in public mode
      this.setPagePreviewLocked?.(locked)
    },
    resetEditorCompactMenu() {
      if (!this.isEditMode) {
        return
      }

      this.$store.dispatch('element/forceUpdate', {
        builder: this.builder,
        page: this.elementPage,
        element: this.element,
        values: {
          _: {
            ...this.element._,
            compactMenuOpen: false,
          },
        },
      })
    },
  },
}
</script>
