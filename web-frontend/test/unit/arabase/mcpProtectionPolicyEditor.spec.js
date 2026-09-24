import { mountSuspended } from '@nuxt/test-utils/runtime'
import { vi } from 'vitest'

import McpProtectionPolicyEditor from '@jadawel/modules/arabase/mcp/components/McpProtectionPolicyEditor'
import { ErrorHandler } from '@jadawel/modules/core/plugins/clientHandler'

const fetchPolicy = vi.fn()
const replacePolicy = vi.fn()
const reactivatePolicy = vi.fn()

vi.mock('@jadawel/modules/arabase/mcp/services/protectionPolicy', () => ({
  default: () => ({ fetchPolicy, replacePolicy, reactivatePolicy }),
}))

describe('McpProtectionPolicyEditor', () => {
  beforeEach(() => {
    fetchPolicy.mockReset()
    replacePolicy.mockReset()
    reactivatePolicy.mockReset()
  })

  test('offers explicit reactivation for a suspended policy', async () => {
    const policy = {
      revision: 4,
      lifecycle_status: 'suspended',
      fields: [
        {
          id: 41,
          name: 'National ID',
          type: 'text',
          table: { id: 20, name: 'People' },
          database: { id: 10, name: 'Customers' },
        },
      ],
    }
    fetchPolicy.mockResolvedValue({ data: policy })
    reactivatePolicy.mockResolvedValue({
      data: { ...policy, revision: 5, lifecycle_status: 'active' },
    })

    const wrapper = await mountSuspended(McpProtectionPolicyEditor, {
      props: {
        endpoint: { id: 9, workspace_id: 1 },
        applications: [],
      },
      global: {
        mocks: { $client: {}, $t: (key) => key },
        stubs: {
          Error: true,
          McpProtectionFieldSelector: true,
        },
      },
    })

    await wrapper.get('button.button--small').trigger('click')

    expect(reactivatePolicy).toHaveBeenCalledWith(9, 4)
    expect(wrapper.emitted('saved')[0][0]).toStrictEqual({
      ...policy,
      revision: 5,
      lifecycle_status: 'active',
    })
  })

  test('surfaces a stale revision without overwriting the current policy', async () => {
    const policy = { revision: 4, lifecycle_status: 'active', fields: [] }
    fetchPolicy.mockResolvedValue({ data: policy })
    replacePolicy.mockRejectedValue({ response: { status: 409 } })

    const wrapper = await mountSuspended(McpProtectionPolicyEditor, {
      props: { endpoint: { id: 9, workspace_id: 1 }, applications: [] },
      global: {
        mocks: { $client: {}, $t: (key) => key },
        stubs: {
          Error: true,
          McpProtectionFieldSelector: true,
        },
      },
    })

    await wrapper.vm.save()

    expect(wrapper.vm.conflict).toBe(true)
    expect(wrapper.emitted('saved')).toBeUndefined()
    expect(replacePolicy).toHaveBeenCalledWith(
      9,
      {
        protected_field_ids: [],
        expected_revision: 4,
        confirm_remove_field_ids: [],
      },
      expect.any(String)
    )
  })

  test('explains that the server cannot protect fields yet', async () => {
    const policy = { revision: 4, lifecycle_status: 'active', fields: [] }
    fetchPolicy.mockResolvedValue({ data: policy })
    const response = {
      status: 400,
      data: {
        error: 'ERROR_MCP_PROTECTION_NOT_READY',
        detail: 'Field protection is not ready on this server.',
      },
    }
    replacePolicy.mockRejectedValue({
      response,
      handler: new ErrorHandler(
        null,
        null,
        { errorMap: {} },
        response,
        response.data.error,
        response.data.detail
      ),
    })

    const wrapper = await mountSuspended(McpProtectionPolicyEditor, {
      props: { endpoint: { id: 9, workspace_id: 1 }, applications: [] },
      global: {
        mocks: { $client: {}, $t: (key) => key },
        stubs: {
          Error: true,
          McpProtectionFieldSelector: true,
        },
      },
    })

    await wrapper.vm.save()

    expect(wrapper.vm.error.title).toBe('mcpProtection.notReadyTitle')
    expect(wrapper.vm.error.message).toBe('mcpProtection.notReadyDescription')
    expect(wrapper.emitted('saved')).toBeUndefined()
  })

  test('keeps unavailable protected identities visible during review', async () => {
    const policy = {
      revision: 4,
      lifecycle_status: 'active',
      fields: [{ id: 41, name: null, type: null, table: null, database: null }],
    }
    fetchPolicy.mockResolvedValue({ data: policy })

    const wrapper = await mountSuspended(McpProtectionPolicyEditor, {
      props: { endpoint: { id: 9, workspace_id: 1 }, applications: [] },
      global: {
        mocks: {
          $client: {},
          $t: (key, params) => `${key}:${params?.id || ''}`,
        },
        stubs: {
          Error: true,
          McpProtectionFieldSelector: true,
        },
      },
    })

    expect(
      wrapper.get('[data-test-id="unavailable-protected-field-41"]').text()
    ).toContain('unavailableField:41')
    expect(wrapper.vm.unavailableFieldIds).toStrictEqual([41])
  })
})
