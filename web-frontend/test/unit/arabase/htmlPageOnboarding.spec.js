import { mountSuspended } from '@nuxt/test-utils/runtime'
import { vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

import HtmlPageOnboarding from '@jadawel/modules/arabase/views/components/HtmlPageOnboarding'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const fetchAll = vi.fn()

vi.mock('@jadawel/modules/core/services/mcpEndpoint', () => ({
  default: () => ({ fetchAll }),
}))

/**
 * An empty page is a dead end unless it explains the way in, so what matters
 * here is that the three things a person needs are actually present and
 * correct: the endpoint for this workspace, this page's own number, and a
 * prompt carrying that number.
 */
describe('HtmlPageOnboarding', () => {
  const database = { id: 1, workspace: { id: 7 } }
  const view = { id: 4660, name: 'Staff report' }

  // The arabase module's messages are not registered in this environment, so
  // `$t` returns the key it was given. Capturing the key and its parameters is
  // therefore the honest assertion — comparing `$t(x)` to `$t(x)` would pass
  // whatever the translation actually said.
  const translated = []
  const $t = (key, params) => {
    translated.push({ key, params })
    return params ? `${key}::${JSON.stringify(params)}` : key
  }

  const mountPanel = async (
    endpoints = [],
    publicBackendUrl = 'http://localhost:8000'
  ) => {
    fetchAll.mockResolvedValue({ data: endpoints })
    return await mountSuspended(HtmlPageOnboarding, {
      props: { database, view },
      global: {
        mocks: {
          $config: { public: { publicBackendUrl } },
          $client: {},
          $t,
        },
        stubs: { SettingsModal: true, Copied: true },
      },
    })
  }

  beforeEach(() => {
    fetchAll.mockReset()
    translated.length = 0
  })

  test('shows this page number, which is what identifies it to the assistant', async () => {
    const wrapper = await mountPanel()

    expect(wrapper.text()).toContain('4660')
  })

  test('the prompt is built with this page number', async () => {
    const wrapper = await mountPanel()

    expect(wrapper.vm.prompt).toContain('4660')
    const call = translated.find(
      (t) => t.key === 'htmlPageOnboarding.promptTemplate'
    )
    expect(call).toBeDefined()
    expect(call.params.viewId).toBe(4660)
  })

  test('without an endpoint, the MCP setup follows the prompt', async () => {
    const wrapper = await mountPanel([])

    expect(wrapper.vm.endpoint).toBeUndefined()
    const setup = wrapper.get('.html-page-onboarding__setup')
    expect(setup.text()).toContain('htmlPageOnboarding.mcpSetup')
    // Directly under the prompt it enables.
    expect(
      setup.element.previousElementSibling.classList.contains(
        'html-page-onboarding__ask'
      )
    ).toBe(true)
  })

  test('the setup button opens the MCP setup itself', async () => {
    fetchAll.mockResolvedValue({ data: [] })
    const show = vi.fn()
    const wrapper = await mountSuspended(HtmlPageOnboarding, {
      props: { database, view },
      global: {
        mocks: {
          $config: { public: { publicBackendUrl: 'http://localhost:8000' } },
          $client: {},
          $t,
        },
        stubs: {
          SettingsModal: {
            name: 'SettingsModal',
            template: '<div />',
            methods: { show },
          },
          Copied: true,
        },
      },
    })

    await wrapper.get('.html-page-onboarding__setup button').trigger('click')
    await flushPromises()

    expect(show).toHaveBeenCalledWith('mcp-endpoint')
  })

  test('with an endpoint, only the prompt is shown', async () => {
    const wrapper = await mountPanel([
      { id: 2, key: 'supersecretkey', workspace_id: 7 },
    ])

    expect(wrapper.find('.html-page-onboarding__setup').exists()).toBe(false)
    expect(wrapper.find('.html-page-onboarding__ask').exists()).toBe(true)
    // No step shows the endpoint address or its key any more.
    expect(wrapper.text()).not.toContain('supersecretkey')
    expect(wrapper.text()).not.toContain('/mcp/')
  })

  test('only an endpoint from this workspace counts', async () => {
    // Endpoints are per user *and* per workspace, so one belonging to another
    // workspace cannot read this table and must not be offered as if it could.
    const wrapper = await mountPanel([
      { id: 1, key: 'otherkey', workspace_id: 99 },
    ])

    expect(wrapper.vm.endpoint).toBeUndefined()
    expect(wrapper.find('.html-page-onboarding__setup').exists()).toBe(true)
  })

  test('staff can hand the page to Sanad, with its number typed in', async () => {
    fetchAll.mockResolvedValue({ data: [] })
    const $bus = { $emit: vi.fn() }
    const wrapper = await mountSuspended(HtmlPageOnboarding, {
      props: { database, view },
      global: {
        mocks: {
          $config: { public: { publicBackendUrl: 'http://localhost:8000' } },
          $client: {},
          $t,
          $bus,
          $store: { getters: { 'auth/isStaff': true } },
        },
        stubs: { SettingsModal: true, Copied: true },
      },
    })

    // The intro no longer says a page can only be written from outside.
    expect(translated.map((t) => t.key)).toContain(
      'htmlPageOnboarding.leadWithSanad'
    )
    await wrapper.get('.html-page-onboarding__sanad button').trigger('click')

    const draft = 'htmlPageOnboarding.sanadDraft::{"viewId":4660}'
    expect($bus.$emit.mock.calls).toEqual([
      ['toggle-right-sidebar', true],
      ['sanad-draft', draft],
    ])
    // The panel mounts on opening, after the event: it takes the parked text.
    const { takeSanadDraft } =
      await import('@jadawel/modules/arabase/sanad/utils/askSanad')
    expect(takeSanadDraft()).toBe(draft)
    expect(takeSanadDraft()).toBeNull()
  })

  test('a user who is not staff gets the MCP route, without Sanad', async () => {
    fetchAll.mockResolvedValue({ data: [] })
    const wrapper = await mountSuspended(HtmlPageOnboarding, {
      props: { database, view },
      global: {
        mocks: {
          $config: { public: { publicBackendUrl: 'http://localhost:8000' } },
          $client: {},
          $t,
          $store: { getters: { 'auth/isStaff': false } },
        },
        stubs: { SettingsModal: true, Copied: true },
      },
    })

    expect(wrapper.find('.html-page-onboarding__sanad').exists()).toBe(false)
    // Everyone else still gets the page written over MCP.
    expect(wrapper.find('.html-page-onboarding__ask').exists()).toBe(true)
    expect(wrapper.find('.html-page-onboarding__setup').exists()).toBe(true)
    expect(translated.map((t) => t.key)).toContain('htmlPageOnboarding.lead')
    expect(translated.map((t) => t.key)).not.toContain(
      'htmlPageOnboarding.leadWithSanad'
    )
  })

  test('a failed endpoint lookup still leaves a usable panel', async () => {
    fetchAll.mockRejectedValue(new Error('boom'))

    const wrapper = await mountSuspended(HtmlPageOnboarding, {
      props: { database, view },
      global: {
        mocks: {
          $config: { public: { publicBackendUrl: 'http://localhost:8000' } },
          $client: {},
        },
        stubs: { SettingsModal: true, Copied: true },
      },
    })

    expect(wrapper.vm.loading).toBe(false)
    // The prompt is still there, and the way to set up MCP follows it.
    expect(wrapper.find('.html-page-onboarding__ask').exists()).toBe(true)
    expect(wrapper.find('.html-page-onboarding__setup').exists()).toBe(true)
  })
})

/**
 * The prompt's value is in what it says, and that lives in the locale files
 * rather than in the component. Checked here because the messages are not
 * registered in the test environment, so nothing that renders `$t` can see it.
 */
describe('the page onboarding prompt', () => {
  // Read off disk rather than imported: the i18n module pre-compiles JSON
  // locale resources at import time, so an `import` hands back compiled
  // message functions instead of the text a translator actually wrote.
  const read = (language) => {
    const relative = `modules/arabase/locales/${language}.json`
    // Vitest normally runs from web-frontend/, but tolerate the repository root
    // so the suite does not depend on where it was invoked from.
    const path = [relative, `web-frontend/${relative}`]
      .map((candidate) => resolve(process.cwd(), candidate))
      .find((candidate) => existsSync(candidate))
    return JSON.parse(readFileSync(path, 'utf8'))
  }
  const locales = { en: read('en'), ar: read('ar') }

  const checkPrompt = (messages) => {
    const prompt = messages.htmlPageOnboarding.promptTemplate

    test('interpolates the page number', () => {
      expect(prompt).toContain('{viewId}')
    })

    test('names the tools the assistant has to call', () => {
      expect(prompt).toContain('get_page_view')
      expect(prompt).toContain('update_page_view')
    })

    test('contains nothing vue-i18n will read as markup', () => {
      // A stray angle bracket makes vue-i18n refuse the whole file, taking
      // every other string in it down with it — a placeholder written as
      // `<describe it here>` did exactly that.
      for (const [key, value] of Object.entries(messages.htmlPageOnboarding)) {
        expect(`${key}: ${value}`).not.toMatch(/<[a-zA-Z/!]/)
      }
    })
  }

  describe('en', () => {
    checkPrompt(locales.en)
  })
  describe('ar', () => {
    checkPrompt(locales.ar)
  })
})
