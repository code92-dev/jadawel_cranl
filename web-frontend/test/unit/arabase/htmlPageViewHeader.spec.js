import { mountSuspended } from '@nuxt/test-utils/runtime'
import { vi } from 'vitest'
import flushPromises from 'flush-promises'

import HtmlPageViewHeader from '@jadawel/modules/arabase/views/components/HtmlPageViewHeader'

const fetchState = vi.fn()
const createDraft = vi.fn()
const approveDraft = vi.fn()

vi.mock('@jadawel/modules/arabase/mcp/services/artifactApproval', () => ({
  default: () => ({ fetchState, createDraft, approveDraft }),
}))

vi.mock('@jadawel/modules/core/utils/error', async (importOriginal) => ({
  ...(await importOriginal()),
  notifyIf: vi.fn(),
}))

// Imported after the mock so this is the spy the component calls.
const { notifyIf } = await import('@jadawel/modules/core/utils/error')

/**
 * Characterizes how the header routes a save: a source edit on a managed MCP
 * page becomes a draft for approval, while everything else is a direct view
 * update. Pinned before the header is restructured.
 */
describe('HtmlPageViewHeader', () => {
  const database = { id: 1, workspace: { id: 7 } }
  const table = { id: 2 }

  let view
  let dispatch
  let hasPermission

  const mountHeader = async ({
    loading = false,
    truncated = false,
    canUpdate = true,
  } = {}) => {
    hasPermission = vi.fn(() => canUpdate)
    const wrapper = await mountSuspended(HtmlPageViewHeader, {
      props: {
        database,
        table,
        view,
        fields: [],
        readOnly: false,
        storePrefix: '',
      },
      global: {
        mocks: {
          $client: {},
          $t: (key) => key,
          $hasPermission: hasPermission,
          $store: {
            state: { table: { loading } },
            getters: {
              'view/html_page/getCount': 3,
              'view/html_page/getRowLimit': 200,
              'view/html_page/getTruncated': truncated,
            },
            dispatch,
          },
        },
        stubs: {
          HtmlPageSourceModal: true,
          HtmlPageSettingsContext: true,
          McpArtifactApprovalPanel: true,
        },
      },
    })
    await flushPromises()
    return wrapper
  }

  const sourceModal = (wrapper) =>
    wrapper.findComponent({ name: 'HtmlPageSourceModal' })
  const settingsContext = (wrapper) =>
    wrapper.findComponent({ name: 'HtmlPageSettingsContext' })
  const approvalPanel = (wrapper) =>
    wrapper.findComponent({ name: 'McpArtifactApprovalPanel' })

  const saveSource = async (wrapper, html) => {
    sourceModal(wrapper).vm.$emit('save', html)
    await flushPromises()
  }

  beforeEach(() => {
    view = { id: 11, html: '<p>a</p>', name: 'P' }
    dispatch = vi.fn().mockResolvedValue(undefined)
    fetchState.mockReset()
    createDraft.mockReset()
    approveDraft.mockReset()
    notifyIf.mockReset()
    createDraft.mockResolvedValue({ data: {} })
  })

  test('an unmanaged page saves its source directly', async () => {
    fetchState.mockResolvedValue({
      data: { artifact_state: 'unmanaged', endpoint_id: null },
    })
    const wrapper = await mountHeader()

    await saveSource(wrapper, '<p>b</p>')

    expect(fetchState).toHaveBeenCalledTimes(1)
    expect(fetchState).toHaveBeenCalledWith(11)
    expect(createDraft).not.toHaveBeenCalled()
    expect(dispatch).toHaveBeenCalledTimes(1)
    expect(dispatch).toHaveBeenCalledWith('view/update', {
      view,
      values: { html: '<p>b</p>' },
      readOnly: false,
    })
  })

  test('a managed state without an endpoint saves directly', async () => {
    fetchState.mockResolvedValue({
      data: { artifact_state: 'approved', endpoint_id: null },
    })
    const wrapper = await mountHeader()

    await saveSource(wrapper, '<p>b</p>')

    expect(createDraft).not.toHaveBeenCalled()
    expect(dispatch).toHaveBeenCalledTimes(1)
    expect(dispatch).toHaveBeenCalledWith('view/update', {
      view,
      values: { html: '<p>b</p>' },
      readOnly: false,
    })
  })

  test('a managed page turns a source edit into a draft', async () => {
    fetchState.mockResolvedValue({
      data: {
        artifact_state: 'pending_approval',
        endpoint_id: 9,
        protected_field_ids: [41],
        audience: 'public',
      },
    })
    const wrapper = await mountHeader()

    await saveSource(wrapper, '<p>b</p>')

    expect(createDraft).toHaveBeenCalledTimes(1)
    expect(createDraft).toHaveBeenCalledWith({
      endpoint_id: 9,
      view_id: 11,
      html: '<p>b</p>',
      protected_field_ids: [41],
      audience: 'public',
      pending_view_values: {},
    })
    expect(dispatch).not.toHaveBeenCalled()
  })

  test('a draft defaults missing ids and audience', async () => {
    fetchState.mockResolvedValue({
      data: { artifact_state: 'approved', endpoint_id: 9 },
    })
    const wrapper = await mountHeader()

    await saveSource(wrapper, '<p>b</p>')

    expect(createDraft).toHaveBeenCalledWith({
      endpoint_id: 9,
      view_id: 11,
      html: '<p>b</p>',
      protected_field_ids: [],
      audience: 'authenticated',
      pending_view_values: {},
    })
    expect(dispatch).not.toHaveBeenCalled()
  })

  test('values saved alongside the html travel as pending view values', async () => {
    fetchState.mockResolvedValue({
      data: {
        artifact_state: 'approved',
        endpoint_id: 9,
        protected_field_ids: [41],
        audience: 'authenticated',
      },
    })
    const wrapper = await mountHeader()

    await wrapper.vm.update({ html: 'x', row_limit: 5 })
    await flushPromises()

    expect(createDraft).toHaveBeenCalledTimes(1)
    expect(createDraft).toHaveBeenCalledWith({
      endpoint_id: 9,
      view_id: 11,
      html: 'x',
      protected_field_ids: [41],
      audience: 'authenticated',
      pending_view_values: { row_limit: 5 },
    })
    expect(dispatch).not.toHaveBeenCalled()
  })

  test('a failed state lookup is reported and nothing is saved', async () => {
    const error = new Error('state failed')
    fetchState.mockRejectedValue(error)
    const wrapper = await mountHeader()

    await saveSource(wrapper, '<p>b</p>')

    expect(notifyIf).toHaveBeenCalledWith(error, 'view')
    expect(createDraft).not.toHaveBeenCalled()
    expect(dispatch).not.toHaveBeenCalled()
  })

  test('a failed draft is reported and the view is not updated', async () => {
    const error = new Error('draft failed')
    fetchState.mockResolvedValue({
      data: { artifact_state: 'approved', endpoint_id: 9 },
    })
    createDraft.mockRejectedValue(error)
    const wrapper = await mountHeader()

    await saveSource(wrapper, '<p>b</p>')

    expect(notifyIf).toHaveBeenCalledWith(error, 'view')
    expect(dispatch).not.toHaveBeenCalled()
  })

  test('a settings update skips the artifact flow', async () => {
    const wrapper = await mountHeader()

    settingsContext(wrapper).vm.$emit('update', { row_limit: 50 })
    await flushPromises()

    expect(fetchState).not.toHaveBeenCalled()
    expect(createDraft).not.toHaveBeenCalled()
    expect(dispatch).toHaveBeenCalledTimes(1)
    expect(dispatch).toHaveBeenCalledWith('view/update', {
      view,
      values: { row_limit: 50 },
      readOnly: false,
    })
  })

  test('an approval from the panel refreshes the page', async () => {
    const wrapper = await mountHeader()

    approvalPanel(wrapper).vm.$emit('approved')
    await flushPromises()

    expect(wrapper.emitted('refresh')).toHaveLength(1)
  })

  test('the update permission is passed down', async () => {
    const wrapper = await mountHeader()

    expect(approvalPanel(wrapper).props('readOnly')).toBe(false)
    expect(approvalPanel(wrapper).props('canUpdate')).toBe(true)
    expect(sourceModal(wrapper).props('readOnly')).toBe(false)
    expect(hasPermission).toHaveBeenCalledWith(
      'database.table.view.update',
      view,
      7
    )
  })

  test('without the update permission the source is read-only', async () => {
    const wrapper = await mountHeader({ canUpdate: false })

    expect(sourceModal(wrapper).props('readOnly')).toBe(true)
  })

  test('while the table loads only the approval panel renders', async () => {
    const wrapper = await mountHeader({ loading: true })

    expect(wrapper.find('ul.header__filter').exists()).toBe(false)
    expect(approvalPanel(wrapper).exists()).toBe(true)
  })

  test('a truncated page says so', async () => {
    const wrapper = await mountHeader({ truncated: true })

    expect(wrapper.text()).toContain('htmlPageViewHeader.truncated')
  })
})
