import { flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'
import { TestApp } from '@jadawel/test/helpers/testApp'
import SanadPanel from '@jadawel/modules/arabase/sanad/components/SanadPanel'
import SanadSidebarItem from '@jadawel/modules/arabase/sanad/components/SanadSidebarItem'
import { ArabasePlugin } from '@jadawel/modules/arabase/plugins'
import { AutomationApplicationType } from '@jadawel/modules/automation/applicationTypes'
import { BuilderApplicationType } from '@jadawel/modules/builder/applicationTypes'

/**
 * Sanad (سند) and the admin-only app types (docs/SANAD_AI_ASSISTANT.md): who
 * sees them, and how the chat panel sends, polls and asks for approval.
 */
const appFor = (isStaff) => ({
  $store: { getters: { 'auth/isStaff': isStaff } },
})

describe('admin-only features', () => {
  test('Sanad is offered to staff only', () => {
    const staff = new ArabasePlugin({ app: appFor(true) })
    const member = new ArabasePlugin({ app: appFor(false) })

    expect(staff.getSidebarWorkspaceComponents({})).toEqual([SanadSidebarItem])
    expect(staff.getRightSidebarWorkspaceComponents({})).toEqual([SanadPanel])
    expect(member.getSidebarWorkspaceComponents({})).toEqual([])
    expect(member.getRightSidebarWorkspaceComponents({})).toEqual([])
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

    expect(wrapper.find('.sanad__notice').text()).toBe('sanad.noModel')
    expect(wrapper.find('.sanad__input').attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('.sanad__suggestion')).toHaveLength(0)
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
    ])
    expect(actions[0].find('.sanad__action-link').attributes('href')).toBe(
      '/automation/5/workflow/9'
    )
    expect(actions[1].find('.sanad__action-link').attributes('href')).toBe(
      '/builder/3/page/4'
    )
    // An app without a page yet has nothing to open.
    expect(actions[2].find('.sanad__action-link').exists()).toBe(false)
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
})
