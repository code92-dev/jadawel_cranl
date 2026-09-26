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

  describe('characterization pins: error classification', () => {
    const app = {
      $i18n: {
        t: (key) =>
          key === 'clientHandler.notCompletedTitle' ? 'generic' : key,
      },
    }

    const handledError = (status, code = null, detail = null) => {
      const response = {
        status,
        data: code ? { error: code, detail } : {},
      }
      return {
        response,
        handler: new ErrorHandler(
          null,
          app,
          { errorMap: {} },
          response,
          code,
          detail
        ),
      }
    }

    const activePolicy = () => ({
      revision: 4,
      lifecycle_status: 'active',
      fields: [],
    })
    const suspendedPolicy = () => ({
      revision: 4,
      lifecycle_status: 'suspended',
      fields: [],
    })

    const mountEditor = () =>
      mountSuspended(McpProtectionPolicyEditor, {
        props: { endpoint: { id: 9, workspace_id: 1 }, applications: [] },
        global: {
          mocks: { $client: {}, $t: (key) => key },
          stubs: {
            Error: true,
            McpProtectionFieldSelector: true,
          },
        },
      })

    test('fetchPolicy 404 makes the editor read-only without a policy', async () => {
      fetchPolicy.mockRejectedValue(handledError(404))

      const wrapper = await mountEditor()

      expect(wrapper.vm.readOnly).toBe(true)
      expect(wrapper.vm.policy).toBeNull()
      expect(wrapper.vm.error.visible).toBe(false)
    })

    test('fetchPolicy 403 makes the editor read-only', async () => {
      fetchPolicy.mockRejectedValue(
        handledError(403, 'ERROR_USER_NOT_IN_GROUP')
      )

      const wrapper = await mountEditor()

      expect(wrapper.vm.readOnly).toBe(true)
      expect(wrapper.vm.policy).toBeNull()
      expect(wrapper.vm.error.visible).toBe(false)
    })

    test('replacePolicy 403 makes the editor read-only without a conflict', async () => {
      fetchPolicy.mockResolvedValue({ data: activePolicy() })
      replacePolicy.mockRejectedValue(
        handledError(403, 'ERROR_USER_NOT_IN_GROUP')
      )
      const wrapper = await mountEditor()

      await wrapper.vm.save()

      expect(wrapper.vm.readOnly).toBe(true)
      expect(wrapper.vm.conflict).toBe(false)
      expect(wrapper.vm.error.visible).toBe(false)
      expect(wrapper.emitted('saved')).toBeUndefined()
    })

    test('reactivate 409 shows the revision conflict', async () => {
      fetchPolicy.mockResolvedValue({ data: suspendedPolicy() })
      reactivatePolicy.mockRejectedValue(
        handledError(409, 'MCP_PROTECTION_REVISION_CONFLICT', '')
      )
      const wrapper = await mountEditor()

      await wrapper.vm.reactivate()

      expect(reactivatePolicy).toHaveBeenCalledWith(9, 4)
      expect(wrapper.vm.conflict).toBe(true)
      expect(wrapper.vm.readOnly).toBe(false)
      expect(wrapper.vm.error.visible).toBe(false)
      expect(wrapper.emitted('saved')).toBeUndefined()
    })

    test('reactivate 401 makes the editor read-only', async () => {
      fetchPolicy.mockResolvedValue({ data: suspendedPolicy() })
      reactivatePolicy.mockRejectedValue(handledError(401))
      const wrapper = await mountEditor()

      await wrapper.vm.reactivate()

      expect(wrapper.vm.readOnly).toBe(true)
      expect(wrapper.vm.conflict).toBe(false)
      expect(wrapper.vm.error.visible).toBe(false)
    })

    test('reactivate 409 with no body still shows the revision conflict', async () => {
      fetchPolicy.mockResolvedValue({ data: suspendedPolicy() })
      reactivatePolicy.mockRejectedValue(handledError(409))
      const wrapper = await mountEditor()

      await wrapper.vm.reactivate()

      expect(wrapper.vm.conflict).toBe(true)
      expect(wrapper.vm.readOnly).toBe(false)
      expect(wrapper.vm.error.visible).toBe(false)
      expect(wrapper.emitted('saved')).toBeUndefined()
    })

    test('reactivate 409 NOT_READY explains why protection stays paused', async () => {
      fetchPolicy.mockResolvedValue({ data: suspendedPolicy() })
      reactivatePolicy.mockRejectedValue(
        handledError(409, 'MCP_PROTECTION_NOT_READY', '')
      )
      const wrapper = await mountEditor()

      await wrapper.vm.reactivate()

      expect(reactivatePolicy).toHaveBeenCalledWith(9, 4)
      expect(wrapper.vm.conflict).toBe(false)
      expect(wrapper.vm.readOnly).toBe(false)
      expect(wrapper.vm.error.visible).toBe(true)
      expect(wrapper.vm.error.title).toBe(
        'mcpProtection.reactivateNotReadyTitle'
      )
      expect(wrapper.vm.error.message).toBe(
        'mcpProtection.reactivateNotReadyDescription'
      )
      expect(wrapper.emitted('saved')).toBeUndefined()
    })

    test('reactivate errors go through the protection map', async () => {
      fetchPolicy.mockResolvedValue({ data: suspendedPolicy() })
      reactivatePolicy.mockRejectedValue(
        handledError(
          400,
          'ERROR_MCP_PROTECTION_NOT_READY',
          'Field protection is not ready on this server.'
        )
      )
      const wrapper = await mountEditor()

      await wrapper.vm.reactivate()

      expect(wrapper.vm.error.visible).toBe(true)
      expect(wrapper.vm.error.title).toBe('mcpProtection.notReadyTitle')
      expect(wrapper.vm.error.message).toBe('mcpProtection.notReadyDescription')
      expect(wrapper.vm.conflict).toBe(false)
      expect(wrapper.vm.readOnly).toBe(false)
    })

    test('save 404 shows the error and keeps the editor writable', async () => {
      fetchPolicy.mockResolvedValue({ data: activePolicy() })
      replacePolicy.mockRejectedValue(handledError(404))
      const wrapper = await mountEditor()

      await wrapper.vm.save()

      expect(wrapper.vm.error.visible).toBe(true)
      expect(wrapper.vm.error.title).toBe('clientHandler.notFoundTitle')
      expect(wrapper.vm.readOnly).toBe(false)
      expect(wrapper.vm.conflict).toBe(false)
    })

    test('the idempotency key survives a 409 and is regenerated after a successful save', async () => {
      const policy = activePolicy()
      fetchPolicy.mockResolvedValue({ data: policy })
      replacePolicy.mockRejectedValueOnce(
        handledError(409, 'MCP_PROTECTION_REVISION_CONFLICT', '')
      )
      replacePolicy.mockResolvedValueOnce({ data: { ...policy, revision: 5 } })
      const wrapper = await mountEditor()
      const initialKey = wrapper.vm.idempotencyKey

      await wrapper.vm.save()

      expect(wrapper.vm.conflict).toBe(true)
      expect(wrapper.vm.idempotencyKey).toBe(initialKey)
      expect(replacePolicy.mock.calls[0][2]).toBe(initialKey)

      await wrapper.vm.save()

      expect(replacePolicy.mock.calls[1][2]).toBe(initialKey)
      expect(wrapper.vm.idempotencyKey).not.toBe(initialKey)
      expect(wrapper.vm.idempotencyKey).toEqual(expect.any(String))
      expect(wrapper.vm.conflict).toBe(false)
      expect(wrapper.emitted('saved')[0][0]).toStrictEqual({
        ...policy,
        revision: 5,
      })
    })
  })
})
