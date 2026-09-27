import { flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'
import { TestApp } from '@jadawel/test/helpers/testApp'
import SanadPanel from '@jadawel/modules/arabase/sanad/components/SanadPanel'
import SanadUtilityItem from '@jadawel/modules/arabase/sanad/components/SanadUtilityItem'
import AdminGenerativeAISettings from '@jadawel/modules/arabase/generativeAI/AdminGenerativeAISettings'
import AppUtilities from '@jadawel/modules/core/components/AppUtilities'
import { ArabasePlugin } from '@jadawel/modules/arabase/plugins'
import { AutomationApplicationType } from '@jadawel/modules/automation/applicationTypes'
import { BuilderApplicationType } from '@jadawel/modules/builder/applicationTypes'
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { INTERFACE_THEMES } from '@jadawel/modules/core/utils/interfaceThemes'
import {
  askSanad,
  takeSanadDraft,
} from '@jadawel/modules/arabase/sanad/utils/askSanad'

/**
 * Sanad (سند) and the admin-only app types (docs/SANAD_AI_ASSISTANT.md): who
 * sees them, and how the chat panel sends, polls and asks for approval.
 */
const appFor = (isStaff) => ({
  $store: { getters: { 'auth/isStaff': isStaff } },
})

describe('admin-only features', () => {
  test('Sanad opens from the tools window, for staff only', () => {
    const staff = new ArabasePlugin({ app: appFor(true) })
    const member = new ArabasePlugin({ app: appFor(false) })

    expect(staff.getWorkspaceUtilityComponents({})).toEqual([SanadUtilityItem])
    expect(staff.getRightSidebarWorkspaceComponents({})).toEqual([SanadPanel])
    expect(member.getWorkspaceUtilityComponents({})).toEqual([])
    expect(member.getRightSidebarWorkspaceComponents({})).toEqual([])
    // No left-panel entry any more, for anyone.
    expect(staff.getSidebarWorkspaceComponents({})).toBeNull()
  })

  test('the AI settings join the admin settings page', () => {
    const plugin = new ArabasePlugin({ app: appFor(true) })
    expect(plugin.getSettingsPageComponents()).toEqual([
      AdminGenerativeAISettings,
    ])
  })

  test.each([AutomationApplicationType, BuilderApplicationType])(
    '%o can be created by staff only',
    (ApplicationType) => {
      expect(new ApplicationType({ app: appFor(true) }).canBeCreated()).toBe(
        true
      )
      expect(new ApplicationType({ app: appFor(false) }).canBeCreated()).toBe(
        false
      )
    }
  )
})

describe('SanadPanel', () => {
  let testApp = null
  const workspace = { id: 7, name: 'Workspace' }

  beforeEach(() => {
    testApp = new TestApp()
    localStorage.clear()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(async () => {
    vi.useRealTimers()
    await testApp.afterEach()
    vi.restoreAllMocks()
  })

  const message = (overrides) => ({
    id: 1,
    role: 'assistant',
    status: 'done',
    content: '',
    context: {},
    actions: [],
    approvals: [],
    error: '',
    created_on: '2026-09-26T10:00:00Z',
    ...overrides,
  })

  const chat = (messages) => ({
    id: 3,
    title: 'Build',
    model: 'openai/gpt-test',
    created_on: '2026-09-26T10:00:00Z',
    updated_on: '2026-09-26T10:00:00Z',
    messages,
  })

  const mountPanel = async (models = ['openai/gpt-test']) => {
    testApp.mock
      .onGet(`/arabase/sanad/workspace/${workspace.id}/models/`)
      .reply(200, { models })
    const wrapper = await testApp.mount(SanadPanel, { props: { workspace } })
    await flushPromises()
    return wrapper
  }

  test('explains how to configure a provider when none is enabled', async () => {
    const wrapper = await mountPanel([])

    const notice = wrapper.find('.sanad__notice')
    expect(notice.text()).toContain('sanad.noModel')
    expect(notice.find('.sanad__notice-link').attributes('href')).toBe(
      '/admin/settings#generative-ai'
    )
    expect(wrapper.find('.sanad__input').attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('.sanad__suggestion')).toHaveLength(0)
  })

  test('an empty chat is greeted by the whole portrait', async () => {
    const wrapper = await mountPanel()

    expect(
      wrapper.find('.sanad__welcome-portrait img').attributes('src')
    ).toMatch(/sanad-portrait/)
    // The header keeps the face only.
    expect(wrapper.find('.sanad__logo img').attributes('src')).toMatch(
      /sanad-avatar/
    )
  })

  test('sends a message, then polls until the answer arrives', async () => {
    const wrapper = await mountPanel()
    testApp.mock
      .onPost(`/arabase/sanad/workspace/${workspace.id}/chats/`)
      .reply(200, chat([]))
    testApp.mock
      .onPost('/arabase/sanad/chats/3/messages/')
      .reply(202, message({ id: 2, status: 'pending' }))
    const question = message({ id: 1, role: 'user', content: 'Make a table' })
    testApp.mock
      .onGet('/arabase/sanad/chats/3/')
      .replyOnce(
        200,
        chat([
          question,
          message({
            id: 2,
            status: 'pending',
            actions: [{ tool: 'list_databases', ok: true, refs: {} }],
          }),
        ])
      )
      .onGet('/arabase/sanad/chats/3/')
      .reply(
        200,
        chat([
          question,
          message({
            id: 2,
            content: '**Done**',
            actions: [
              { tool: 'list_databases', ok: true, refs: {} },
              {
                tool: 'create_table',
                ok: true,
                refs: { id: 12, database_id: 4 },
              },
            ],
          }),
        ])
      )

    await wrapper.find('.sanad__input').setValue('Make a table')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const sent = JSON.parse(testApp.mock.history.post[1].data)
    expect(sent.content).toBe('Make a table')
    expect(sent.model).toBe('openai/gpt-test')
    expect(sent.context).toEqual({ table_id: null, view_id: null })
    expect(wrapper.find('.sanad__thinking').exists()).toBe(true)
    expect(wrapper.find('.sanad__bubble').text()).toBe('Make a table')

    await vi.advanceTimersByTimeAsync(1600)
    await flushPromises()

    expect(wrapper.find('.sanad__thinking').exists()).toBe(false)
    expect(wrapper.find('.sanad__answer').html()).toContain(
      '<strong>Done</strong>'
    )
    const actions = wrapper.findAll('.sanad__action')
    expect(actions.map((a) => a.find('span').text())).toEqual([
      'sanad.tools.list_databases',
      'sanad.tools.create_table',
    ])
    expect(actions[0].find('.sanad__action-link').exists()).toBe(false)
    expect(actions[1].find('.sanad__action-link').attributes('href')).toBe(
      '/database/4/table/12'
    )
    expect(localStorage.getItem('jadawel.sanad.chat.7')).toBe('3')
  })

  test('asks before a destructive action and sends the decision', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    const waiting = message({
      id: 2,
      status: 'awaiting_approval',
      approvals: [
        {
          tool_call_id: 'call-1',
          tool: 'delete_rows',
          arguments: { table_id: 5, row_ids: [9] },
        },
      ],
    })
    testApp.mock
      .onGet('/arabase/sanad/chats/3/')
      .replyOnce(200, chat([waiting]))
    const wrapper = await mountPanel()

    expect(wrapper.find('.sanad__approval-text').text()).toBe(
      'sanad.tools.delete_rows'
    )
    expect(wrapper.find('.sanad__input').attributes('disabled')).toBeDefined()

    testApp.mock
      .onPost('/arabase/sanad/chats/3/decisions/')
      .reply(202, { ...waiting, status: 'pending' })
    testApp.mock.onGet('/arabase/sanad/chats/3/').reply(
      200,
      chat([
        message({
          id: 2,
          content: 'Deleted.',
          approvals: [{ ...waiting.approvals[0], approved: false }],
        }),
      ])
    )

    const [, keep] = wrapper.findAll('.sanad__approval-buttons button')
    await keep.trigger('click')
    await flushPromises()

    expect(JSON.parse(testApp.mock.history.post[0].data)).toEqual({
      decisions: [{ tool_call_id: 'call-1', approved: false }],
    })
    expect(wrapper.find('.sanad__approval').exists()).toBe(false)
    expect(wrapper.find('.sanad__decided').text()).toBe('sanad.declined')
  })

  test('shows a translated error for a failed turn', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock
      .onGet('/arabase/sanad/chats/3/')
      .reply(
        200,
        chat([message({ status: 'error', error: 'SANAD_ERROR_MODEL_FAILED' })])
      )

    const wrapper = await mountPanel()

    expect(wrapper.find('.sanad__error').text()).toMatch(/^sanad\.errors\./)
  })

  test('a used-up monthly allowance is explained, not shown as a failure', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock
      .onGet('/arabase/sanad/chats/3/')
      .reply(
        200,
        chat([
          message({ status: 'error', error: 'SANAD_ERROR_BUDGET_EXCEEDED' }),
        ])
      )

    const wrapper = await mountPanel()

    expect(wrapper.find('.sanad__error').text()).toBe(
      'sanad.errors.SANAD_ERROR_BUDGET_EXCEEDED'
    )
  })

  test('links built automations and pages to their editors', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock.onGet('/arabase/sanad/chats/3/').reply(
      200,
      chat([
        message({
          actions: [
            {
              tool: 'create_automation',
              ok: true,
              refs: { automation_id: 5, workflow_id: 9 },
            },
            {
              tool: 'add_form_to_page',
              ok: true,
              refs: { application_id: 3, page_id: 4 },
            },
            {
              tool: 'create_builder_application',
              ok: true,
              refs: { application_id: 3 },
            },
            {
              tool: 'add_dashboard_widget',
              ok: true,
              refs: { dashboard_id: 8, application_id: 8 },
            },
            { tool: 'load_skill', ok: true, refs: {} },
          ],
        }),
      ])
    )

    const wrapper = await mountPanel()

    const actions = wrapper.findAll('.sanad__action')
    expect(actions.map((a) => a.find('span').text())).toEqual([
      'sanad.tools.create_automation',
      'sanad.tools.add_form_to_page',
      'sanad.tools.create_builder_application',
      'sanad.tools.add_dashboard_widget',
      'sanad.tools.load_skill',
    ])
    expect(actions[3].find('.sanad__action-link').attributes('href')).toBe(
      '/dashboard/8'
    )
    expect(actions[0].find('.sanad__action-link').attributes('href')).toBe(
      '/automation/5/workflow/9'
    )
    expect(actions[1].find('.sanad__action-link').attributes('href')).toBe(
      '/builder/3/page/4'
    )
    // An app without a page yet has nothing to open.
    expect(actions[2].find('.sanad__action-link').exists()).toBe(false)
  })

  test('links a written page to its table view', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock.onGet('/arabase/sanad/chats/3/').reply(
      200,
      chat([
        message({
          actions: [
            {
              tool: 'write_page_view',
              ok: true,
              refs: { view_id: 91, table_id: 47, database_id: 19 },
            },
          ],
        }),
      ])
    )

    const wrapper = await mountPanel()

    const action = wrapper.find('.sanad__action')
    expect(action.find('span').text()).toBe('sanad.tools.write_page_view')
    expect(action.find('.sanad__action-link').attributes('href')).toBe(
      '/database/19/table/47/91'
    )
  })

  test('a request typed elsewhere waits in a new chat', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock
      .onGet('/arabase/sanad/chats/3/')
      .reply(200, chat([message({ content: 'Earlier answer' })]))
    askSanad(testApp.getApp().$bus, 'Design page 91: ')

    const wrapper = await mountPanel()

    expect(wrapper.find('.sanad__input').element.value).toBe('Design page 91: ')
    // A new request, so the remembered chat is set aside, not appended to.
    expect(wrapper.vm.chat).toBeNull()
    expect(takeSanadDraft()).toBeNull()

    // Once open, the panel takes the next one straight from the event.
    askSanad(testApp.getApp().$bus, 'Design page 92: ')
    await flushPromises()
    expect(wrapper.find('.sanad__input').element.value).toBe('Design page 92: ')
  })

  test('each message is its own block, and a long list of steps folds once answered', async () => {
    const steps = (count) =>
      Array.from({ length: count }, () => ({
        tool: 'create_fields',
        ok: true,
        refs: {},
      }))
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock
      .onGet('/arabase/sanad/chats/3/')
      .reply(
        200,
        chat([
          message({ id: 1, role: 'user', content: 'Build it' }),
          message({ id: 2, actions: steps(3), content: 'Done' }),
          message({ id: 3, actions: steps(6), content: 'Done' }),
          message({ id: 4, actions: steps(6), status: 'pending' }),
        ])
      )

    const wrapper = await mountPanel()

    expect(wrapper.findAll('.sanad__bubble')).toHaveLength(1)
    expect(wrapper.findAll('.sanad__card')).toHaveLength(3)
    // Sanad's face heads the panel and every one of its answers; the full
    // portrait is only for the empty chat's welcome.
    const faces = wrapper.findAll('.sanad__avatar img, .sanad__logo img')
    expect(faces).toHaveLength(4)
    expect(
      faces.every((face) => /sanad-avatar/.test(face.attributes('src')))
    ).toBe(true)
    expect(wrapper.find('.sanad__welcome-portrait').exists()).toBe(false)
    const open = wrapper
      .findAll('.sanad__steps')
      .map((steps) => steps.element.open)
    // A short list stays open, a long one folds under the answer, and while
    // Sanad works the steps are its progress, so they stay open.
    expect(open).toEqual([true, false, true])
    expect(wrapper.find('.sanad__card--pending .sanad__typing').exists()).toBe(
      true
    )
  })

  test('asks to publish with publish wording, not delete wording', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock.onGet('/arabase/sanad/chats/3/').reply(
      200,
      chat([
        message({
          status: 'awaiting_approval',
          approvals: [
            {
              tool_call_id: 'c-publish',
              tool: 'publish_workflow',
              arguments: { workflow_id: 9 },
            },
          ],
        }),
      ])
    )

    const wrapper = await mountPanel()

    const buttons = wrapper.findAll('.sanad__approval-buttons button')
    expect(buttons.map((button) => button.text())).toEqual([
      'sanad.approvePublish',
      'sanad.declinePublish',
    ])
    expect(wrapper.find('.sanad__approval-text').text()).toBe(
      'sanad.tools.publish_workflow'
    )
  })

  test('sharing a form on a public link also reads as publishing', async () => {
    localStorage.setItem('jadawel.sanad.chat.7', '3')
    testApp.mock.onGet('/arabase/sanad/chats/3/').reply(
      200,
      chat([
        message({
          status: 'awaiting_approval',
          approvals: [
            {
              tool_call_id: 'c-share',
              tool: 'share_form',
              arguments: { view_id: 9 },
            },
          ],
        }),
      ])
    )

    const wrapper = await mountPanel()

    const buttons = wrapper.findAll('.sanad__approval-buttons button')
    expect(buttons.map((button) => button.text())).toEqual([
      'sanad.approvePublish',
      'sanad.declinePublish',
    ])
    expect(wrapper.find('.sanad__approval-text').text()).toBe(
      'sanad.tools.share_form'
    )
  })
})

describe('the panel follows the selected interface theme', () => {
  // Read off disk: the stylesheet is what decides the colours, and the test
  // environment does not compile it.
  const stylesheet = () => {
    const relative = 'modules/arabase/assets/scss/sanad.scss'
    const path = [relative, `web-frontend/${relative}`]
      .map((candidate) => resolve(process.cwd(), candidate))
      .find((candidate) => existsSync(candidate))
    return readFileSync(path, 'utf8')
  }

  test('its accent and tints come from the theme palette', () => {
    const css = stylesheet()

    for (const step of [300, 400, 500, 700]) {
      expect(css).toContain(`var(--jadawel-primary-${step}`)
    }
    expect(css).toContain('var(--jadawel-content-background')
    // A fixed hue would ignore the user's choice of theme.
    expect(css).not.toMatch(/\$palette-(cyan|blue|green)-/)
  })

  test('every theme gives the steps the panel mixes from', () => {
    for (const theme of INTERFACE_THEMES) {
      for (const step of [300, 400, 500, 700]) {
        expect(theme.colors[step]).toMatch(/^#[0-9a-f]{6}$/)
      }
    }
  })
})

describe('workspace tools window', () => {
  let testApp = null
  const workspace = { id: 7, name: 'Workspace', users: [] }

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
    vi.restoreAllMocks()
  })

  test('lists the tools other modules add', async () => {
    testApp.store.state.auth.user = { is_staff: true }
    const wrapper = await testApp.mount(AppUtilities, { props: { workspace } })
    await wrapper
      .find('[data-highlight="workspace-utilities"]')
      .trigger('click')
    await flushPromises()

    const items = [
      ...document.querySelectorAll(
        '.app-utilities__menu .context__menu-item-link'
      ),
    ].map((item) => item.textContent.trim())
    expect(items).toContain('sanad.name')
    expect(items.indexOf('sanad.name')).toBe(items.length - 1)
  })

  test('opening Sanad closes the window and opens the side panel', async () => {
    const wrapper = await testApp.mount(SanadUtilityItem, {
      props: { workspace },
    })
    const emit = vi.spyOn(testApp._app.$bus, '$emit')

    await wrapper.find('a').trigger('click')

    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(emit).toHaveBeenCalledWith('toggle-right-sidebar', true)
  })
})

describe('AdminGenerativeAISettings', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
    vi.restoreAllMocks()
  })

  const provider = (type, fields, overrides = {}) => ({
    type,
    fields,
    api_key_set: false,
    api_key_hint: '',
    models: [],
    host: '',
    base_url: '',
    organization: '',
    configured_by_environment: false,
    enabled: false,
    updated_on: null,
    ...overrides,
  })

  const PROVIDERS = [
    provider('openai', ['api_key', 'models', 'organization', 'base_url'], {
      api_key_set: true,
      api_key_hint: '1234',
      models: ['gpt-5'],
      enabled: true,
    }),
    provider('anthropic', ['api_key', 'models']),
    provider('ollama', ['host', 'models']),
    provider('openrouter', ['api_key', 'models', 'organization']),
  ]

  const mountSettings = async () => {
    testApp.mock
      .onGet('/arabase/admin/generative-ai/')
      .reply(200, { providers: PROVIDERS })
    const wrapper = await testApp.mount(AdminGenerativeAISettings, {})
    await flushPromises()
    return wrapper
  }

  test('offers exactly OpenAI, Claude, Ollama and OpenRouter', async () => {
    const wrapper = await mountSettings()

    const names = wrapper
      .findAll('.admin-ai__name')
      .map((name) => name.text().replace(/\s+/g, ' '))
    expect(names).toEqual([
      'OpenAI adminAI.active',
      'Claude (Anthropic) adminAI.inactive',
      'Ollama adminAI.inactive',
      'OpenRouter adminAI.inactive',
    ])
    expect(wrapper.text()).not.toMatch(/Mistral/)
    expect(wrapper.find('.admin-ai__disabled').text()).toBe(
      'adminAI.mistralDisabled'
    )
    // Ollama asks for a host, not a key.
    const ollama = wrapper.findAll('.admin-ai__provider')[2]
    expect(ollama.findAll('input[type="password"]')).toHaveLength(0)
  })

  test('never shows a saved key, and saves only what was typed', async () => {
    const wrapper = await mountSettings()
    const openai = wrapper.findAll('.admin-ai__provider')[0]
    const keyInput = openai.find('input[type="password"]')
    expect(keyInput.element.value).toBe('')

    testApp.mock
      .onPatch('/arabase/admin/generative-ai/anthropic/')
      .reply(200, { providers: PROVIDERS })
    const anthropic = wrapper.findAll('.admin-ai__provider')[1]
    const [key, models] = anthropic.findAll('input')
    await key.setValue('sk-ant-secret')
    await models.setValue('claude-sonnet-5, , claude-haiku-4-5')
    await anthropic.find('form').trigger('submit')
    await flushPromises()

    expect(JSON.parse(testApp.mock.history.patch[0].data)).toEqual({
      api_key: 'sk-ant-secret',
      models: ['claude-sonnet-5', 'claude-haiku-4-5'],
    })
    // The typed key is not kept in the form after saving.
    expect(anthropic.findAll('input')[0].element.value).toBe('')
  })

  test('removing a key sends only that request', async () => {
    const wrapper = await mountSettings()
    testApp.mock
      .onPatch('/arabase/admin/generative-ai/openai/')
      .reply(200, { providers: PROVIDERS })

    await wrapper.find('.admin-ai__clear').trigger('click')
    await flushPromises()

    expect(JSON.parse(testApp.mock.history.patch[0].data)).toEqual({
      clear_api_key: true,
    })
  })
})
