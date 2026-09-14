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
        v-click-outside="closeCompactMenuOnClickOutside"
        role="dialog"
        :aria-label="$t('menuElement.compactMenuLabel')"
        :class="compactPanelClasses"
        :style="{
          ...getStyleOverride('menu'),
          '--alignment': 'flex-start',
        }"
        tabindex="-1"
        @keydown="onPanelKeydown"
        @click.capture="onPanelClick"
        @mousedown.stop
      >
        <ABIcon
          icon="iconoir-cancel"
          class="menu-element__compact-menu-close"
          is-button
          :aria-label="$t('menuElement.closeCompactMenu')"
          @click="closeCompactMenu()"
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
    // Leaving the compact variant (device or variant change) must not leave
    // an open menu, focus or preview lock behind.
    useCompactMenu(isCompact) {
      if (!isCompact && this.isCompactMenuOpen) {
        this.closeCompactMenu({ restoreFocus: false })
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
    closeCompactMenuOnClickOutside() {
      // Kept separate from closeCompactMenu() because the click-outside
      // directive passes the originating event as an argument; backdrop
      // dismissal is still a close path that must restore focus.
      this.closeCompactMenu()
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
    onPanelKeydown(event) {
      if (event.key === 'Escape') {
        this.closeCompactMenu()
        return
      }
      if (event.key === 'Tab') {
        this.trapFocusInPanel(event)
      }
    },
    trapFocusInPanel(event) {
      const panel = this.$refs.compactPanel
      if (!panel) {
        return
      }
      const focusables = panel.querySelectorAll(
        'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (!focusables.length) {
        // Nothing else to focus: keep focus on the panel itself so Tab does
        // not escape the dialog.
        event.preventDefault()
        panel.focus()
        return
      }
      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      const active = document.activeElement
      if (event.shiftKey) {
        if (active === first || !panel.contains(active)) {
          event.preventDefault()
          last.focus()
        }
      } else if (active === last || !panel.contains(active)) {
        event.preventDefault()
        first.focus()
      }
    },
    onPanelClick(event) {
      // Activating a menu item (link or button) navigates or fires its
      // event: the overlay must close and hand focus back to the trigger.
      // The capture phase is used because child links stop propagation; the
      // close control and the nested submenu toggle are excluded because
      // they must keep the menu open.
      if (
        event.target.closest(
          '.menu-element__compact-menu-close, .menu-element__menu-item-with-children'
        )
      ) {
        return
      }
      if (event.target.closest('a, button')) {
        this.closeCompactMenu()
      }
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
