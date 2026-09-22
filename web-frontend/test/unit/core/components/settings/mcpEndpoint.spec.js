import McpEndpoint from '@jadawel/modules/core/components/settings/McpEndpoint'
import { TestApp } from '@jadawel/test/helpers/testApp'

const ENDPOINT_URL = 'https://api.example.test/mcp/secret-key/sse'

const translations = {
  'mcpEndpoint.copyPrompt': 'Copy prompt',
  'mcpEndpoint.setupPromptTitle': 'Paste this prompt to your AI agent',
  'mcpEndpoint.setupPromptInstructions':
    'Reveal the full URL first, then copy the prompt below.',
  'mcpEndpoint.setupPrompt':
    'Set up the following Jadawel MCP server.\nServer URL: {endpointUrl}\nTreat this URL as a password.',
}

const getTranslation = (key, values = {}) => {
  const value = translations[key] ?? key
  return Object.entries(values).reduce(
    (translated, [name, replacement]) =>
      translated.replaceAll(`{${name}}`, replacement),
    value
  )
}

describe('McpEndpoint setup instructions', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
    testApp.store.dispatch('workspace/forceCreate', {
      id: 7,
      name: 'Operations',
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mountComponent = async (
    publicBackendUrl = 'https://api.example.test'
  ) =>
    await testApp.mount(McpEndpoint, {
      props: {
        endpoint: {
          id: 4,
          key: 'secret-key',
          name: 'Jadawel MCP',
          workspace_id: 7,
        },
      },
      global: {
        mocks: {
          $config: {
            public: { publicBackendUrl },
          },
          $t: getTranslation,
        },
      },
    })

  test('offers one reusable AI agent prompt with no client-specific tabs', async () => {
    const wrapper = await mountComponent()
    await wrapper.get('.mcp-endpoint__toggle a').trigger('click')
    await wrapper.get('.flex > a').trigger('click')

    expect(wrapper.find('.tabs').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Claude')
    expect(wrapper.text()).not.toContain('Cursor')
    expect(wrapper.text()).not.toContain('Codex')
    expect(wrapper.text()).not.toContain('Windsurf')
    expect(wrapper.get('.mcp-endpoint__setup-title').text()).toBe(
      'Paste this prompt to your AI agent'
    )

    const prompt = wrapper.get('.mcp-endpoint__prompt')
    expect(prompt.text()).toContain('Set up the following Jadawel MCP server')
    expect(prompt.text()).toContain(`Server URL: ${ENDPOINT_URL}`)
    expect(prompt.text()).toContain('Treat this URL as a password')
  })

  test('normalizes a trailing slash in the public backend URL', async () => {
    const wrapper = await mountComponent('https://api.example.test/')
    await wrapper.get('.mcp-endpoint__toggle a').trigger('click')
    await wrapper.get('.flex > a').trigger('click')

    expect(wrapper.get('.mcp-endpoint__box').text()).toBe(ENDPOINT_URL)
    expect(wrapper.text()).not.toContain('https://api.example.test//mcp/')
  })

  test('copies the endpoint URL when the Clipboard API is unavailable', async () => {
    const clipboardDescriptor = Object.getOwnPropertyDescriptor(
      navigator,
      'clipboard'
    )
    const execCommandDescriptor = Object.getOwnPropertyDescriptor(
      document,
      'execCommand'
    )
    const execCommand = vi.fn(() => true)

    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: undefined,
    })
    Object.defineProperty(document, 'execCommand', {
      configurable: true,
      value: execCommand,
    })

    try {
      const wrapper = await mountComponent()
      await wrapper.get('.mcp-endpoint__toggle a').trigger('click')
      await wrapper.get('.mcp-endpoint__link-action').trigger('click')

      expect(execCommand).toHaveBeenCalledWith('copy')
    } finally {
      if (clipboardDescriptor === undefined) {
        delete navigator.clipboard
      } else {
        Object.defineProperty(navigator, 'clipboard', clipboardDescriptor)
      }
      if (execCommandDescriptor === undefined) {
        delete document.execCommand
      } else {
        Object.defineProperty(document, 'execCommand', execCommandDescriptor)
      }
    }
  })

  test('copies the prompt with the full endpoint URL', async () => {
    const clipboardDescriptor = Object.getOwnPropertyDescriptor(
      navigator,
      'clipboard'
    )
    const writeText = vi.fn(() => Promise.resolve())

    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    })

    try {
      const wrapper = await mountComponent()
      await wrapper.get('.mcp-endpoint__toggle a').trigger('click')
      await wrapper.get('.mcp-endpoint__prompt-action').trigger('click')

      expect(writeText).toHaveBeenCalledWith(
        `Set up the following Jadawel MCP server.\nServer URL: ${ENDPOINT_URL}\nTreat this URL as a password.`
      )
    } finally {
      if (clipboardDescriptor === undefined) {
        delete navigator.clipboard
      } else {
        Object.defineProperty(navigator, 'clipboard', clipboardDescriptor)
      }
    }
  })
})
