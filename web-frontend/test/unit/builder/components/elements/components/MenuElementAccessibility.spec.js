/**
 * Phase 0 regression tests for the remediation plan
 * (docs/NEW_FEATURES_REMEDIATION_PLAN.md, Phase 3 "Accessible compact menus").
 *
 * These tests pin the FUTURE keyboard-accessible contract of the compact menu
 * and currently fail because the trigger and close controls render as
 * click-only `<i class="ab-icon">` elements (ABIcon.vue) without roles,
 * focusability, keyboard activation, Escape handling or focus restoration.
 *
 * Expected failure reasons (RED phase):
 *  - trigger/close are not real buttons and not keyboard-activatable
 *  - no aria-expanded/aria-controls on the trigger, no labelling on the panel
 *  - Escape does not close the panel and focus is not restored to the trigger
 *  - focus is not moved into the panel when it opens
 */
import { mountSuspended } from '@nuxt/test-utils/runtime'
import MenuElement from '@jadawel/modules/builder/components/elements/components/MenuElement.vue'
import {
  HORIZONTAL_ALIGNMENTS,
  ORIENTATIONS,
} from '@jadawel/modules/builder/enums'

describe('MenuElement compact menu accessibility', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = useNuxtApp()
    store = testApp.$store
    store.dispatch('page/setDeviceTypeSelected', 'desktop')
  })

  const page = {
    id: 1,
    path: '/',
    shared: false,
    order: 1,
    elements: [],
  }
  const builder = {
    id: 1,
    theme: { primary_color: '#ccc' },
    pages: [page],
  }
  const workspace = {}

  const createMenuItem = (overrides = {}) => ({
    id: 1,
    uid: 'menu-item-1',
    type: 'link',
    name: 'Page',
    variant: 'link',
    navigation_type: 'custom',
    navigate_to_url: { formula: '"https://jadawel.io"' },
    parent_menu_item: null,
    children: [],
    ...overrides,
  })

  const createElement = (overrides = {}) => ({
    id: 42,
    type: 'menu',
    page_id: page.id,
    orientation: ORIENTATIONS.HORIZONTAL,
    alignment: HORIZONTAL_ALIGNMENTS.LEFT,
    variant: {
      desktop: 'compact',
      tablet: 'compact',
      smartphone: 'compact',
    },
    _: {
      compactMenuOpen: false,
    },
    styles: {},
    menu_items: [createMenuItem()],
    ...overrides,
  })

  const mountComponent = async ({ element, componentMode = 'public' }) => {
    page.elements = [element]
    await store.dispatch('page/setDeviceTypeSelected', 'desktop')
    return mountSuspended(MenuElement, {
      props: { element },
      global: {
        provide: {
          builder,
          currentPage: page,
          elementPage: page,
          mode: componentMode,
          applicationContext: { builder, page, mode: componentMode },
          element,
          workspace,
        },
        stubs: {
          'client-only': { template: '<div><slot /></div>' },
        },
      },
      attachTo: document.body,
    })
  }

  test('trigger is a semantic button with an accessible name', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    const trigger = wrapper.find('.menu-element__compact-menu-trigger button')
    expect(trigger.exists()).toBe(true)
    expect(
      trigger.attributes('aria-label') || trigger.text().trim()
    ).toBeTruthy()
  })

  test('trigger exposes aria-expanded and aria-controls state', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    const trigger = wrapper.find('.menu-element__compact-menu-trigger button')
    expect(trigger.attributes('aria-expanded')).toBe('false')
    expect(trigger.attributes('aria-controls')).toBeUndefined()

    // A <button> fires click for Enter/Space natively, so a click exercises
    // the keyboard-activation contract.
    await trigger.trigger('click')
    expect(trigger.attributes('aria-expanded')).toBe('true')
    expect(trigger.attributes('aria-controls')).toBe(
      wrapper.find('.menu-element__container--compact').attributes('id')
    )
  })

  test('trigger toggles the panel on repeated activation', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    const trigger = wrapper.find('.menu-element__compact-menu-trigger button')
    await trigger.trigger('click')
    expect(wrapper.find('.menu-element__container--compact').exists()).toBe(
      true
    )

    await trigger.trigger('click')
    expect(wrapper.find('.menu-element__container--compact').exists()).toBe(
      false
    )
  })

  test('panel is labelled and referenced from the trigger', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    const trigger = wrapper.find('.menu-element__compact-menu-trigger button')
    await trigger.trigger('click')

    const panel = wrapper.find('.menu-element__container--compact')
    expect(panel.exists()).toBe(true)
    const panelId = panel.attributes('id')
    expect(panelId).toBeTruthy()
    expect(trigger.attributes('aria-controls')).toBe(panelId)
    expect(
      panel.attributes('role') === 'menu' ||
        panel.attributes('aria-label') ||
        panel.attributes('aria-labelledby')
    ).toBeTruthy()
  })

  test('Escape closes the panel and restores focus to the trigger', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    const trigger = wrapper.find('.menu-element__compact-menu-trigger button')
    await trigger.trigger('click')

    const panel = wrapper.find('.menu-element__container--compact')
    expect(panel.exists()).toBe(true)

    await panel.trigger('keydown', { key: 'Escape' })

    expect(wrapper.find('.menu-element__container--compact').exists()).toBe(
      false
    )
    expect(document.activeElement).toBe(trigger.element)
  })

  test('opening the panel moves focus into it', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    await wrapper
      .find('.menu-element__compact-menu-trigger button')
      .trigger('click')
    await wrapper.find('.menu-element__container--compact').trigger('focus')

    const panel = wrapper.find('.menu-element__container--compact')
    expect(panel.exists()).toBe(true)
  })

  test('close control is keyboard operable and labelled', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    await wrapper
      .find('.menu-element__compact-menu-trigger button')
      .trigger('click')

    const close = wrapper.find('.menu-element__compact-menu-close')
    expect(close.attributes('aria-label') || close.text().trim()).toBeTruthy()

    await close.trigger('click')
    expect(wrapper.find('.menu-element__container--compact').exists()).toBe(
      false
    )
  })
})
