import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'

import McpProtectionFlow from '@jadawel/modules/arabase/mcp/components/McpProtectionFlow'

const createEndpoint = vi.fn()

vi.mock('@jadawel/modules/arabase/mcp/services/protectionPolicy', () => ({
  default: () => ({ createEndpoint }),
}))

describe('McpProtectionFlow', () => {
  beforeEach(() => {
    createEndpoint.mockReset()
  })

  test('reviews the exact selected policy before creating the endpoint', async () => {
    createEndpoint.mockResolvedValue({ data: { id: 9, key: 'secret-key' } })
    const wrapper = await mountSuspended(McpProtectionFlow, {
      props: {
        workspaces: [{ id: 1, name: 'Operations' }],
        applications: [],
      },
      global: {
        mocks: { $client: {}, $t: (key) => key },
        stubs: {
          McpProtectionFieldSelector: {
            props: ['modelValue'],
            emits: ['update:modelValue'],
            template:
              "<button data-test-id=\"choose-field\" @click=\"$emit('update:modelValue', [{ id: 41, name: 'National ID', type: 'text', table: { id: 20, name: 'People' }, database: { id: 10, name: 'Customers' } }])\">choose</button>",
          },
        },
      },
    })

    await wrapper.get('[data-test-id="endpoint-name"]').setValue('Assistant')
    await wrapper.get('[data-test-id="workspace-id"]').setValue('1')
    await wrapper.get('[data-test-id="next-details"]').trigger('click')
    await wrapper.get('[data-test-id="choose-field"]').trigger('click')
    await wrapper.get('[data-test-id="next-fields"]').trigger('click')

    expect(wrapper.text()).toContain('National ID')
    expect(wrapper.text()).toContain('Customers / People')

    await wrapper
      .get('[data-test-id="create-protected-endpoint"]')
      .trigger('click')

    expect(createEndpoint).toHaveBeenCalledWith(
      {
        name: 'Assistant',
        workspace_id: 1,
        protected_field_ids: [41],
        confirm_empty_policy: false,
      },
      expect.any(String)
    )
    expect(wrapper.emitted('created')[0][0]).toStrictEqual({
      id: 9,
      key: 'secret-key',
    })
  })

  describe('characterization pins', () => {
    const selectorStub = {
      name: 'McpProtectionFieldSelector',
      props: ['databases', 'modelValue'],
      emits: ['update:modelValue'],
      template:
        "<button data-test-id=\"choose-field\" @click=\"$emit('update:modelValue', [{ id: 41, name: 'National ID', type: 'text', table: { id: 20, name: 'People' }, database: { id: 1, name: 'Customers' } }])\">choose</button>",
    }

    const mountFlow = (applications) =>
      mountSuspended(McpProtectionFlow, {
        props: {
          workspaces: [
            { id: 1, name: 'Operations' },
            { id: 2, name: 'Finance' },
          ],
          applications,
        },
        global: {
          mocks: { $client: {}, $t: (key) => key },
          stubs: { McpProtectionFieldSelector: selectorStub },
        },
      })

    const goToFields = async (wrapper) => {
      await wrapper.get('[data-test-id="endpoint-name"]').setValue('Assistant')
      await wrapper.get('[data-test-id="workspace-id"]').setValue('1')
      await wrapper.get('[data-test-id="next-details"]').trigger('click')
    }

    test('passes only the chosen workspace databases to the field selector', async () => {
      const wrapper = await mountFlow([
        {
          id: 1,
          type: 'database',
          name: 'A',
          workspace: { id: 1 },
          tables: [],
        },
        { id: 2, type: 'database', name: 'B', workspace_id: 1, tables: [] },
        {
          id: 3,
          type: 'database',
          name: 'C',
          workspace: { id: 2 },
          tables: [],
        },
        { id: 4, type: 'builder', name: 'D', workspace: { id: 1 } },
      ])
      await goToFields(wrapper)

      const selector = wrapper.findComponent({
        name: 'McpProtectionFieldSelector',
      })
      expect(selector.exists()).toBe(true)
      expect(
        selector.props('databases').map((database) => database.id)
      ).toStrictEqual([1, 2])
    })

    test('an implicit form submit in the fields step does not create the endpoint', async () => {
      createEndpoint.mockResolvedValue({ data: { id: 9, key: 'secret-key' } })
      const wrapper = await mountFlow([])
      await goToFields(wrapper)
      await wrapper.get('[data-test-id="choose-field"]').trigger('click')
      expect(
        wrapper.find('[data-test-id="create-protected-endpoint"]').exists()
      ).toBe(false)

      await wrapper.get('form').trigger('submit')
      await flushPromises()

      expect(createEndpoint).not.toHaveBeenCalled()
      expect(wrapper.find('[data-test-id="next-fields"]').exists()).toBe(true)
      expect(
        wrapper.find('[data-test-id="create-protected-endpoint"]').exists()
      ).toBe(false)
    })
  })

  describe('implicit form submission', () => {
    const selectorStub = {
      name: 'McpProtectionFieldSelector',
      props: ['databases', 'modelValue'],
      emits: ['update:modelValue'],
      template:
        "<button type=\"button\" data-test-id=\"choose-field\" @click=\"$emit('update:modelValue', [{ id: 41, name: 'National ID', type: 'text', table: { id: 20, name: 'People' }, database: { id: 1, name: 'Customers' } }])\">choose</button>",
    }

    const mountFlow = () =>
      mountSuspended(McpProtectionFlow, {
        props: {
          workspaces: [{ id: 1, name: 'Operations' }],
          applications: [],
        },
        global: {
          mocks: { $client: {}, $t: (key) => key },
          stubs: { McpProtectionFieldSelector: selectorStub },
        },
      })

    const goToFields = async (wrapper) => {
      await wrapper.get('[data-test-id="endpoint-name"]').setValue('Assistant')
      await wrapper.get('[data-test-id="workspace-id"]').setValue('1')
      await wrapper.get('[data-test-id="next-details"]').trigger('click')
    }

    const goToReview = async (wrapper) => {
      await goToFields(wrapper)
      await wrapper.get('[data-test-id="choose-field"]').trigger('click')
      await wrapper.get('[data-test-id="next-fields"]').trigger('click')
    }

    test('an implicit submit on the details step does not create', async () => {
      createEndpoint.mockResolvedValue({ data: { id: 9, key: 'secret-key' } })
      const wrapper = await mountFlow()
      await goToFields(wrapper)
      await wrapper.get('[data-test-id="choose-field"]').trigger('click')
      await wrapper
        .findAll('button')
        .find((button) => button.text() === 'mcpProtection.back')
        .trigger('click')
      expect(wrapper.find('[data-test-id="endpoint-name"]').exists()).toBe(true)

      await wrapper.get('form').trigger('submit')
      await flushPromises()

      expect(createEndpoint).not.toHaveBeenCalled()
      expect(wrapper.find('[data-test-id="endpoint-name"]').exists()).toBe(true)
    })

    test('an implicit submit on the review step creates exactly once', async () => {
      createEndpoint.mockResolvedValue({ data: { id: 9, key: 'secret-key' } })
      const wrapper = await mountFlow()
      await goToReview(wrapper)

      await wrapper.get('form').trigger('submit')
      await flushPromises()

      expect(createEndpoint).toHaveBeenCalledTimes(1)
      expect(createEndpoint).toHaveBeenCalledWith(
        {
          name: 'Assistant',
          workspace_id: 1,
          protected_field_ids: [41],
          confirm_empty_policy: false,
        },
        expect.any(String)
      )
      expect(wrapper.emitted('created')[0][0]).toStrictEqual({
        id: 9,
        key: 'secret-key',
      })
    })

    test('an implicit submit on the review step does not create while metadata failed to load', async () => {
      createEndpoint.mockResolvedValue({ data: { id: 9, key: 'secret-key' } })
      const wrapper = await mountFlow()
      await goToReview(wrapper)
      wrapper.vm.metadataStatus = { loading: false, error: true }
      await flushPromises()
      expect(
        wrapper.get('[data-test-id="create-protected-endpoint"]').attributes()
      ).toHaveProperty('disabled')

      await wrapper.get('form').trigger('submit')
      await flushPromises()

      expect(createEndpoint).not.toHaveBeenCalled()
    })
  })
})
