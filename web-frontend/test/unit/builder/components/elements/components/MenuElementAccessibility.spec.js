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

  let activeWrapper = null

  afterEach(async () => {
    // mountSuspended attaches to document.body; without an unmount, panels
    // from earlier tests stay open in the document and their click-outside
    // handlers interfere with later focus assertions.
    if (activeWrapper) {
      await activeWrapper.unmount()
      activeWrapper = null
    }
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
    const wrapper = await mountSuspended(MenuElement, {
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
    activeWrapper = wrapper
    return wrapper
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

    const panel = wrapper.find('.menu-element__container--compact')
    expect(panel.exists()).toBe(true)
    // The watcher focuses the panel itself (tabindex="-1"), so keyboard
    // users land inside the dialog instead of staying on the trigger.
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(document.activeElement).toBe(panel.element)
  })

  test('Tab is trapped inside the open panel', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    await wrapper
      .find('.menu-element__compact-menu-trigger button')
      .trigger('click')
    const panel = wrapper.find('.menu-element__container--compact')
    await new Promise((resolve) => setTimeout(resolve, 0))

    const close = wrapper.find('.menu-element__compact-menu-close')
    const links = panel.findAll('a')
    const lastLink = links.at(links.length - 1)

    // The test runner does not emulate the browser's default Tab focus
    // move, so the trap is asserted at the wrap edges, where the handler
    // itself moves focus: Shift+Tab on the first focusable element wraps
    // to the last one.
    close.element.focus()
    await close.trigger('keydown', { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(lastLink.element)

    // ... and Tab on the last focusable element wraps back to the first.
    await lastLink.trigger('keydown', { key: 'Tab' })
    expect(document.activeElement).toBe(close.element)
  })
  test('close control is keyboard operable, labelled and restores focus', async () => {
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
    // Every close path — including the close button — must hand focus back
    // to the trigger.
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(document.activeElement).toBe(
      wrapper.find('.menu-element__compact-menu-trigger button').element
    )
  })

  test('activating a menu link closes the panel and restores focus', async () => {
    const wrapper = await mountComponent({ element: createElement() })

    await wrapper
      .find('.menu-element__compact-menu-trigger button')
      .trigger('click')

    const link = wrapper.find('.menu-element__container--compact a')
    await link.trigger('click')

    expect(wrapper.find('.menu-element__container--compact').exists()).toBe(
      false
    )
    await new Promise((resolve) => setTimeout(resolve, 0))
    const trigger = wrapper.find('.menu-element__compact-menu-trigger button')
    expect(document.activeElement).toBe(trigger.element)
  })

  test('empty compact menu keeps focus trapped on the panel', async () => {
    const wrapper = await mountComponent({
      element: createElement({ menu_items: [] }),
    })

    await wrapper
      .find('.menu-element__compact-menu-trigger button')
      .trigger('click')
    const panel = wrapper.find('.menu-element__container--compact')
    await new Promise((resolve) => setTimeout(resolve, 0))

    // With no items, Tab keeps focus on the panel itself.
    await panel.trigger('keydown', { key: 'Tab' })
    expect(document.activeElement).toBe(panel.element)
  })

  test('nested submenu toggle is keyboard operable with ARIA state', async () => {
    const parentItem = createMenuItem({
      id: 2,
      uid: 'menu-item-parent',
      children: [createMenuItem({ id: 3, uid: 'menu-item-child' })],
    })
    const wrapper = await mountComponent({
      element: createElement({ menu_items: [parentItem] }),
    })

    await wrapper
      .find('.menu-element__compact-menu-trigger button')
      .trigger('click')

    // The compact variant renders submenus inline; the toggle is a div
    // with the full button contract instead of a nested interactive
    // control inside the parent link.
    const toggle = wrapper.find('.menu-element__menu-item-with-children')
    expect(toggle.attributes('role')).toBe('button')
    expect(toggle.attributes('tabindex')).toBe('0')
    expect(toggle.attributes('aria-expanded')).toBe('false')

    // Enter and Space activate it like a button.
    await toggle.trigger('keydown', { key: 'Enter' })
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('.menu-element__sub-link--container').exists()).toBe(
      true
    )

    await toggle.trigger('keydown', { key: ' ', code: 'Space' })
    expect(toggle.attributes('aria-expanded')).toBe('false')

    // When expanded, the controlled region is referenced by id.
    await toggle.trigger('keydown', { key: 'Enter' })
    const container = wrapper.find('.menu-element__sub-link--container')
    expect(toggle.attributes('aria-controls')).toBe(container.attributes('id'))
  })
})
