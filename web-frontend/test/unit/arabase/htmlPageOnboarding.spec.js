import { mountSuspended } from '@nuxt/test-utils/runtime'
import { vi } from 'vitest'

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

  test('offers the protected setup when the workspace has no endpoint', async () => {
    const wrapper = await mountPanel([])

    expect(wrapper.vm.endpoint).toBeUndefined()
    expect(translated.map((t) => t.key)).toContain(
      'htmlPageOnboarding.createKey'
    )
  })

  test('only an endpoint from this workspace counts', async () => {
    // Endpoints are per user *and* per workspace, so one belonging to another
    // workspace cannot read this table and must not be offered as if it could.
    const wrapper = await mountPanel([
      { id: 1, key: 'otherkey', workspace_id: 99 },
    ])

    expect(wrapper.vm.endpoint).toBeUndefined()
  })

  test('the key is masked until it is asked for', async () => {
    const wrapper = await mountPanel([
      { id: 2, key: 'supersecretkey', workspace_id: 7 },
    ])

    // The panel sits open on a table view, often on a shared screen.
    expect(wrapper.vm.displayedUrl).not.toContain('supersecretkey')
    expect(wrapper.vm.displayedUrl).toContain('•••••••')
    // ...while what the copy button puts on the clipboard is the real thing.
    expect(wrapper.vm.endpointUrl).toBe(
      'http://localhost:8000/mcp/supersecretkey/sse'
    )

    wrapper.vm.reveal = true
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.displayedUrl).toContain('supersecretkey')
  })

  test('the config snippet offered for copying holds the real key', async () => {
    const wrapper = await mountPanel([
      { id: 2, key: 'supersecretkey', workspace_id: 7 },
    ])

    expect(wrapper.vm.clientConfig).not.toContain('supersecretkey')
    expect(wrapper.vm.realClientConfig).toContain('supersecretkey')
    expect(() => JSON.parse(wrapper.vm.realClientConfig)).not.toThrow()
  })

  test('normalizes a trailing slash in the public backend URL', async () => {
    const wrapper = await mountPanel(
      [{ id: 2, key: 'supersecretkey', workspace_id: 7 }],
      'http://localhost:8000/'
    )

    expect(wrapper.get('.html-page-onboarding__code').text()).toBe(
      'http://localhost:8000/mcp/•••••••/sse'
    )
    expect(wrapper.text()).not.toContain('http://localhost:8000//mcp/')
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
    expect(wrapper.text()).toContain('4660')
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
