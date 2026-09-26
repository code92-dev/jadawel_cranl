import { mountSuspended } from '@nuxt/test-utils/runtime'
import { vi } from 'vitest'
import flushPromises from 'flush-promises'

import McpProtectionFieldSelector from '@jadawel/modules/arabase/mcp/components/McpProtectionFieldSelector'
import McpProtectionReview from '@jadawel/modules/arabase/mcp/components/McpProtectionReview'

const fetchAll = vi.fn()

vi.mock('@jadawel/modules/database/services/field', () => ({
  default: () => ({ fetchAll }),
}))

describe('McpProtectionFieldSelector', () => {
  beforeEach(() => {
    fetchAll.mockReset()
  })

  test('loads a table lazily and selects fields by stable identity', async () => {
    fetchAll.mockResolvedValue({
      data: [
        { id: 41, name: 'National ID', type: 'text' },
        { id: 42, name: 'Active', type: 'boolean' },
      ],
    })
    const wrapper = await mountSuspended(McpProtectionFieldSelector, {
      props: {
        databases: [
          {
            id: 10,
            name: 'Customers',
            tables: [{ id: 20, name: 'People' }],
          },
        ],
        modelValue: [],
      },
      global: { mocks: { $client: {}, $t: (key) => key } },
    })

    await wrapper.get('[data-test-id="expand-table-20"]').trigger('click')
    await wrapper.get('[data-test-id="protected-field-41"]').setValue(true)

    expect(fetchAll).toHaveBeenCalledWith(20)
    expect(wrapper.emitted('update:modelValue')[0][0]).toStrictEqual([
      {
        id: 41,
        name: 'National ID',
        type: 'text',
        table: { id: 20, name: 'People' },
        database: { id: 10, name: 'Customers' },
      },
    ])
  })

  test('requires scope confirmation before selecting a whole database', async () => {
    fetchAll.mockImplementation(async (tableId) => ({
      data: [{ id: tableId + 100, name: `Field ${tableId}`, type: 'text' }],
    }))
    const wrapper = await mountSuspended(McpProtectionFieldSelector, {
      props: {
        databases: [
          {
            id: 10,
            name: 'Customers',
            tables: [
              { id: 20, name: 'People' },
              { id: 21, name: 'Companies' },
            ],
          },
        ],
        modelValue: [],
      },
      global: { mocks: { $client: {}, $t: (key) => key } },
    })

    await wrapper.get('[data-test-id="select-database-10"]').trigger('click')
    expect(wrapper.find('[data-test-id="confirm-database-10"]').exists()).toBe(
      true
    )
    await wrapper
      .find('.mcp-protection-selector__scope-confirmation input')
      .setValue(true)
    await wrapper.get('[data-test-id="confirm-database-10"]').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('update:modelValue')[0][0]).toHaveLength(2)
    expect(fetchAll).toHaveBeenCalledWith(20)
    expect(fetchAll).toHaveBeenCalledWith(21)
  })

  test('offers an explicit retry after a metadata load failure', async () => {
    fetchAll.mockRejectedValueOnce(new Error('temporary failure'))
    const wrapper = await mountSuspended(McpProtectionFieldSelector, {
      props: {
        databases: [
          { id: 10, name: 'Customers', tables: [{ id: 20, name: 'People' }] },
        ],
        modelValue: [],
      },
      global: { mocks: { $client: {}, $t: (key) => key } },
    })

    await wrapper.get('[data-test-id="expand-table-20"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[data-test-id="retry-fields-20"]').exists()).toBe(true)

    fetchAll.mockResolvedValueOnce({
      data: [{ id: 41, name: 'National ID', type: 'text' }],
    })
    await wrapper.get('[data-test-id="retry-fields-20"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[data-test-id="protected-field-41"]').exists()).toBe(
      true
    )
  })

  test('exposes live status and keyboard-focusable semantic field controls', async () => {
    fetchAll.mockResolvedValue({
      data: [{ id: 41, name: 'National ID', type: 'text' }],
    })
    const wrapper = await mountSuspended(McpProtectionFieldSelector, {
      props: {
        databases: [
          { id: 10, name: 'Customers', tables: [{ id: 20, name: 'People' }] },
        ],
        modelValue: [],
      },
      global: { mocks: { $client: {}, $t: (key) => key } },
    })

    const selector = wrapper.get('section[aria-live="polite"]')
    expect(selector.attributes('aria-busy')).toBe('false')
    const expand = wrapper.get('[data-test-id="expand-table-20"]')
    expect(expand.attributes('aria-expanded')).toBe('false')

    await expand.trigger('click')
    const checkbox = wrapper.get('[data-test-id="protected-field-41"]')
    expect(checkbox.attributes('aria-label')).toContain(
      'Customers / People / National ID'
    )
    expect(checkbox.element.tabIndex).toBe(0)
    expect(checkbox.element.disabled).toBe(false)
    await checkbox.setValue(true)
    expect(wrapper.emitted('update:modelValue')[0][0][0].id).toBe(41)
  })

  describe('characterization pins', () => {
    const databases = [
      { id: 10, name: 'Customers', tables: [{ id: 20, name: 'People' }] },
    ]
    const otherTableEntry = {
      id: 99,
      name: 'Tax number',
      type: 'text',
      table: { id: 30, name: 'Companies' },
      database: { id: 11, name: 'Suppliers' },
    }

    const mountSelector = (modelValue) =>
      mountSuspended(McpProtectionFieldSelector, {
        props: { databases, modelValue },
        global: { mocks: { $client: {}, $t: (key) => key } },
      })

    const expandPeople = async (wrapper) => {
      await wrapper.get('[data-test-id="expand-table-20"]').trigger('click')
      await flushPromises()
    }

    const selectAllInput = (wrapper) =>
      wrapper.get('.mcp-protection-selector__select-all input')

    beforeEach(() => {
      fetchAll.mockResolvedValue({
        data: [
          { id: 41, name: 'National ID', type: 'text' },
          { id: 42, name: 'Active', type: 'boolean' },
        ],
      })
    })

    test('per-table select-all emits the same entry shape as single selection', async () => {
      const wrapper = await mountSelector([])
      await expandPeople(wrapper)

      await selectAllInput(wrapper).trigger('change')

      const emitted = wrapper.emitted('update:modelValue')[0][0]
      expect(emitted).toStrictEqual([
        {
          id: 41,
          name: 'National ID',
          type: 'text',
          table: { id: 20, name: 'People' },
          database: { id: 10, name: 'Customers' },
        },
        {
          id: 42,
          name: 'Active',
          type: 'boolean',
          table: { id: 20, name: 'People' },
          database: { id: 10, name: 'Customers' },
        },
      ])
      emitted.forEach((entry) =>
        expect(entry.database).toStrictEqual({ id: 10, name: 'Customers' })
      )

      const review = await mountSuspended(McpProtectionReview, {
        props: {
          name: 'A',
          workspaceName: 'W',
          fields: emitted,
          confirmEmptyPolicy: false,
        },
        global: { mocks: { $t: (k) => k } },
      })
      expect(review.text()).toContain('Customers / People')
    })

    test('per-table select-all keeps existing entries by reference and adds new ones with their database', async () => {
      const existing41 = {
        id: 41,
        name: 'National ID',
        type: 'text',
        table: { id: 20, name: 'People' },
        database: { id: 10, name: 'Customers' },
      }
      const wrapper = await mountSelector([otherTableEntry, existing41])
      await expandPeople(wrapper)

      await selectAllInput(wrapper).trigger('change')

      const emitted = wrapper.emitted('update:modelValue')[0][0]
      expect(emitted).toHaveLength(3)
      expect(emitted[0]).toBe(otherTableEntry)
      expect(emitted[1]).toBe(existing41)
      expect(emitted[2]).toStrictEqual({
        id: 42,
        name: 'Active',
        type: 'boolean',
        table: { id: 20, name: 'People' },
        database: { id: 10, name: 'Customers' },
      })
    })

    test('per-table select-all in the all state removes every field of the table', async () => {
      const wrapper = await mountSelector([
        { id: 41, name: 'National ID', type: 'text' },
        otherTableEntry,
        { id: 42, name: 'Active', type: 'boolean' },
      ])
      await expandPeople(wrapper)
      expect(selectAllInput(wrapper).element.checked).toBe(true)
      expect(selectAllInput(wrapper).element.indeterminate).toBe(false)

      await selectAllInput(wrapper).trigger('change')

      const emitted = wrapper.emitted('update:modelValue')[0][0]
      expect(emitted).toHaveLength(1)
      expect(emitted[0]).toBe(otherTableEntry)
    })

    test('per-table select-all is indeterminate when some fields are selected', async () => {
      const wrapper = await mountSelector([
        { id: 41, name: 'National ID', type: 'text' },
      ])
      await expandPeople(wrapper)

      expect(selectAllInput(wrapper).element.indeterminate).toBe(true)
      expect(selectAllInput(wrapper).element.checked).toBe(false)
    })

    test('search loads metadata from two characters and hides unmatched databases', async () => {
      const wrapper = await mountSelector([])
      const search = wrapper.get('[data-test-id="protected-field-search"]')

      await search.setValue('a')
      await flushPromises()
      expect(fetchAll).not.toHaveBeenCalled()
      expect(wrapper.find('[data-test-id="select-database-10"]').exists()).toBe(
        true
      )

      await search.setValue('Peo')
      await flushPromises()
      expect(fetchAll).toHaveBeenCalledTimes(1)
      expect(fetchAll).toHaveBeenCalledWith(20)
      expect(wrapper.find('[data-test-id="expand-table-20"]').exists()).toBe(
        true
      )

      await search.setValue('zz')
      await flushPromises()
      expect(wrapper.find('[data-test-id="select-database-10"]').exists()).toBe(
        false
      )
      expect(wrapper.find('[data-test-id="expand-table-20"]').exists()).toBe(
        false
      )
    })

    test('whole-database select replaces an existing entry in place with a database-bearing object', async () => {
      const existing41 = {
        id: 41,
        name: 'National ID',
        type: 'text',
        table: { id: 20, name: 'People' },
      }
      const wrapper = await mountSelector([existing41, otherTableEntry])

      await wrapper.get('[data-test-id="select-database-10"]').trigger('click')
      await wrapper
        .get('.mcp-protection-selector__scope-confirmation input')
        .setValue(true)
      await wrapper.get('[data-test-id="confirm-database-10"]').trigger('click')
      await flushPromises()

      const emitted = wrapper.emitted('update:modelValue')[0][0]
      expect(emitted).toHaveLength(3)
      expect(emitted[0]).not.toBe(existing41)
      expect(emitted[0]).toStrictEqual({
        id: 41,
        name: 'National ID',
        type: 'text',
        table: { id: 20, name: 'People' },
        database: { id: 10, name: 'Customers' },
      })
      expect(emitted[1]).toBe(otherTableEntry)
      expect(emitted[2]).toStrictEqual({
        id: 42,
        name: 'Active',
        type: 'boolean',
        table: { id: 20, name: 'People' },
        database: { id: 10, name: 'Customers' },
      })
    })
  })
})
