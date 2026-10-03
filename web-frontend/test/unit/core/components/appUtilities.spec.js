import { TestApp } from '@jadawel/test/helpers/testApp'
import AppUtilities from '@jadawel/modules/core/components/AppUtilities'
import {
  getInterfaceThemeSurfaces,
  INTERFACE_THEMES,
  INTERFACE_THEME_STORAGE_KEY,
} from '@jadawel/modules/core/utils/interfaceThemes'

const ContextStub = {
  name: 'Context',
  emits: ['hidden', 'shown'],
  methods: {
    toggle() {
      this.$emit('shown')
    },
    hide() {
      this.$emit('hidden')
    },
  },
  template: '<div class="context"><slot /></div>',
}

const EmptyOverlayStub = {
  methods: {
    show() {},
    toggle() {},
  },
  template: '<div />',
}

describe('AppUtilities component', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
    localStorage.removeItem(INTERFACE_THEME_STORAGE_KEY)
  })

  afterEach(async () => {
    INTERFACE_THEMES.forEach(({ colors }) => {
      Object.keys(colors).forEach((step) => {
        document.documentElement.style.removeProperty(
          `--jadawel-primary-${step}`
        )
      })
    })
    document.documentElement.style.removeProperty('--jadawel-grid-surface')
    document.documentElement.style.removeProperty('--jadawel-grid-line')
    Object.keys(getInterfaceThemeSurfaces(INTERFACE_THEMES[0].colors)).forEach(
      (property) => document.documentElement.style.removeProperty(property)
    )
    delete document.documentElement.dataset.interfaceTheme
    localStorage.removeItem(INTERFACE_THEME_STORAGE_KEY)
    await testApp.afterEach()
  })

  const stubs = {
    Context: ContextStub,
    NotificationPanel: EmptyOverlayStub,
    WorkspaceMemberInviteModal: EmptyOverlayStub,
    TrashModal: EmptyOverlayStub,
    BadgeCounter: true,
  }

  test('defaults to white first and keeps green as the second interface color', async () => {
    // Inviting is offered when the user is an admin of some workspace.
    await testApp.store.dispatch('workspace/forceCreate', {
      id: 1,
      name: 'Acme',
      permissions: 'ADMIN',
      users: [],
    })
    const wrapper = await testApp.mount(AppUtilities, {
      props: {
        workspace: { id: 1, users: [{ id: 1 }, { id: 2 }] },
      },
      global: {
        mocks: {
          $hasPermission: () => true,
        },
        stubs: {
          Context: ContextStub,
          NotificationPanel: EmptyOverlayStub,
          WorkspaceMemberInviteModal: EmptyOverlayStub,
          TrashModal: EmptyOverlayStub,
          BadgeCounter: true,
        },
      },
    })

    expect(wrapper.findAll('.app-utilities__item')).toHaveLength(2)
    expect(wrapper.find('.app-utilities__item .iconoir-bell').exists()).toBe(
      true
    )
    expect(
      wrapper.find('.app-utilities__item .iconoir-view-grid').exists()
    ).toBe(true)
    expect(wrapper.find('.context__menu .iconoir-group').exists()).toBe(true)
    expect(wrapper.find('.context__menu .iconoir-add-user').exists()).toBe(true)
    expect(wrapper.find('.context__menu .iconoir-bin').exists()).toBe(true)

    const colorOptions = wrapper.findAll('.app-utilities__theme-option')
    expect(colorOptions).toHaveLength(6)
    expect(colorOptions[0].attributes('aria-checked')).toBe('true')
    expect(document.documentElement.dataset.interfaceTheme).toBe('white')

    await colorOptions[1].trigger('click')

    expect(colorOptions[1].attributes('aria-checked')).toBe('true')
    expect(document.documentElement.dataset.interfaceTheme).toBe('sage')
    expect(
      document.documentElement.style.getPropertyValue('--jadawel-primary-500')
    ).toBe('#278053')
    expect(
      document.documentElement.style.getPropertyValue(
        '--jadawel-header-background'
      )
    ).toBe('#f0f7f3')
    expect(
      document.documentElement.style.getPropertyValue(
        '--jadawel-app-background'
      )
    ).toBe('#f5faf7')
    expect(
      document.documentElement.style.getPropertyValue('--jadawel-border-color')
    ).toBe('#cfe8d9')
    expect(localStorage.getItem(INTERFACE_THEME_STORAGE_KEY)).toBe('sage')
  })

  test('on the pages spanning every workspace it has no workspace', async () => {
    await testApp.store.dispatch('workspace/forceCreate', {
      id: 1,
      name: 'Acme',
      permissions: 'MEMBER',
      users: [],
    })
    const wrapper = await testApp.mount(AppUtilities, {
      global: { stubs },
    })

    expect(wrapper.classes()).toContain('app-utilities--inline')
    // Notifications belong to one workspace, so only the tools are shown.
    expect(wrapper.find('.iconoir-bell').exists()).toBe(false)
    expect(wrapper.findAll('.app-utilities__item')).toHaveLength(1)
    // Members covers every workspace.
    const members = wrapper.get('.context__menu-item-link:has(.iconoir-group)')
    expect(members.attributes('href')).toBe('/members')
    // Not an admin anywhere, so there is nobody to invite to.
    expect(wrapper.find('.context__menu .iconoir-add-user').exists()).toBe(
      false
    )
    expect(wrapper.find('.context__menu .iconoir-bin').exists()).toBe(true)
  })

  test('inside a workspace members still covers every workspace', async () => {
    const workspace = { id: 1, name: 'Acme', permissions: 'ADMIN', users: [] }
    await testApp.store.dispatch('workspace/forceCreate', workspace)
    const wrapper = await testApp.mount(AppUtilities, {
      props: { workspace },
      global: { stubs },
    })

    expect(wrapper.classes()).not.toContain('app-utilities--inline')
    expect(wrapper.find('.iconoir-bell').exists()).toBe(true)
    expect(
      wrapper
        .get('.context__menu-item-link:has(.iconoir-group)')
        .attributes('href')
    ).toBe('/members')
    expect(wrapper.find('.context__menu .iconoir-add-user').exists()).toBe(true)
  })
})
