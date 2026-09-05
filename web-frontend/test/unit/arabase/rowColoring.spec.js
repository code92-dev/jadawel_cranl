import { mount } from '@vue/test-utils'

import BackgroundColorDecorator from '@jadawel/modules/arabase/components/BackgroundColorDecorator'
import LeftBorderColorDecorator from '@jadawel/modules/arabase/components/LeftBorderColorDecorator'
import ConditionalColorForm from '@jadawel/modules/arabase/components/ConditionalColorForm'
import { BackgroundColorDecoratorType } from '@jadawel/modules/arabase/decorators/backgroundColor'
import { LeftBorderColorDecoratorType } from '@jadawel/modules/arabase/decorators/leftBorderColor'
import { SingleSelectColorValueProviderType } from '@jadawel/modules/arabase/valueProviders/singleSelectColor'
import { ConditionalColorValueProviderType } from '@jadawel/modules/arabase/valueProviders/conditionsColor'

/**
 * Row coloring resolves entirely client-side from loaded row values, so that
 * is what is asserted: option color in, color string out, and nothing rendered
 * when the configuration points nowhere.
 */
const app = { $i18n: { t: (key) => key } }

const fields = [
  { id: 10, name: 'Status', type: 'single_select' },
  { id: 11, name: 'Notes', type: 'text' },
]

describe('SingleSelectColorValueProviderType', () => {
  const provider = new SingleSelectColorValueProviderType({ app })

  test('resolves the option color of the configured field', () => {
    const row = { id: 1, field_10: { id: 5, value: 'Open', color: 'blue' } }
    expect(provider.getValue({ options: { field_id: 10 }, fields, row })).toBe(
      'blue'
    )
  })

  test('returns null when the field is unknown', () => {
    const row = { id: 1, field_10: { id: 5, value: 'Open', color: 'blue' } }
    expect(provider.getValue({ options: { field_id: 999 }, fields, row })).toBe(
      null
    )
  })

  test('returns null when the row has no value or no color', () => {
    expect(
      provider.getValue({ options: { field_id: 10 }, fields, row: { id: 1 } })
    ).toBe(null)
    expect(
      provider.getValue({
        options: { field_id: 10 },
        fields,
        row: { id: 1, field_10: { id: 5, value: 'Open' } },
      })
    ).toBe(null)
  })

  test('rejects values outside the option palette', () => {
    const row = { id: 1, field_10: { id: 5, value: 'X', color: 'red;evil' } }
    expect(provider.getValue({ options: { field_id: 10 }, fields, row })).toBe(
      null
    )
  })

  test('defaults to the first single select field', () => {
    expect(provider.getDefaultConfiguration({ fields, view: {} })).toEqual({
      field_id: 10,
    })
    expect(
      provider.getDefaultConfiguration({
        fields: [{ id: 11, type: 'text' }],
        view: {},
      })
    ).toEqual({ field_id: null })
  })
})

describe('BackgroundColorDecoratorType', () => {
  const decorator = new BackgroundColorDecoratorType({ app })

  test('is compatible with grid and gallery views', () => {
    expect(decorator.isCompatible({ type: 'grid' })).toBe(true)
    expect(decorator.isCompatible({ type: 'gallery' })).toBe(true)
    expect(decorator.isCompatible({ type: 'form' })).toBe(false)
  })

  test('allows a single background decoration per view', () => {
    expect(decorator.canAdd({ view: { decorations: [] } })[0]).toBe(true)
    const [canAdd] = decorator.canAdd({
      view: { decorations: [{ type: 'background_color' }] },
    })
    expect(canAdd).toBe(false)
  })

  test('renders at the row wrapper place', () => {
    expect(decorator.getPlace()).toBe('wrapper')
  })
})

describe('BackgroundColorDecorator', () => {
  test('applies the palette class for a known color', () => {
    const wrapper = mount(BackgroundColorDecorator, {
      props: { value: 'blue' },
    })
    expect(wrapper.classes()).toContain('background-color--blue')
  })

  test('renders plain rows for missing or unsafe values', () => {
    for (const value of [null, undefined, 'red;evil']) {
      const wrapper = mount(BackgroundColorDecorator, {
        props: { value },
      })
      expect(
        wrapper.classes().some((c) => c.startsWith('background-color--'))
      ).toBe(false)
    }
  })
})

describe('LeftBorderColorDecoratorType', () => {
  const decorator = new LeftBorderColorDecoratorType({ app })

  test('is compatible with grid and gallery views', () => {
    expect(decorator.isCompatible({ type: 'grid' })).toBe(true)
    expect(decorator.isCompatible({ type: 'gallery' })).toBe(true)
    expect(decorator.isCompatible({ type: 'form' })).toBe(false)
  })

  test('allows a single left border decoration per view', () => {
    expect(decorator.canAdd({ view: { decorations: [] } })[0]).toBe(true)
    const [canAdd] = decorator.canAdd({
      view: { decorations: [{ type: 'left_border_color' }] },
    })
    expect(canAdd).toBe(false)
  })

  test('renders at the first cell place so it can coexist with background', () => {
    expect(decorator.getPlace()).toBe('first_cell')
  })
})

describe('LeftBorderColorDecorator', () => {
  test('applies the palette bar class for a known color', () => {
    const wrapper = mount(LeftBorderColorDecorator, {
      props: { value: 'blue' },
    })
    expect(wrapper.classes()).toContain('row-coloring__border-bar')
    expect(wrapper.classes()).toContain('background-color--blue')
  })

  test('renders nothing for missing or unsafe values', () => {
    for (const value of [null, undefined, 'red;evil']) {
      const wrapper = mount(LeftBorderColorDecorator, {
        props: { value },
      })
      expect(wrapper.find('.row-coloring__border-bar').exists()).toBe(false)
    }
  })
})

/**
 * The conditions resolver evaluates view-filter operators client-side, so
 * the fake registry only needs the two registry lookups the filter tree
 * makes: the field type and the view filter type.
 */
const filterTypes = {
  contains: {
    matches: (rowValue, filterValue) =>
      String(rowValue ?? '')
        .toLowerCase()
        .includes(String(filterValue).toLowerCase()),
  },
  // Core hands filter types the stringified filter value, mirroring that
  // here keeps the fake honest.
  equal: {
    matches: (rowValue, filterValue) => String(rowValue) === filterValue,
  },
}
const registry = {
  get: (type, name) => {
    if (type === 'field') {
      return { type: name }
    }
    return filterTypes[name]
  },
}
const conditionalApp = { $i18n: { t: (key) => key }, $registry: registry }

const conditionalFields = [
  { id: 10, name: 'Name', type: 'text' },
  { id: 11, name: 'Score', type: 'number' },
]

const rule = (filters, operator, color) => ({
  id: 'rule-' + color,
  filters,
  filter_groups: [],
  operator,
  color,
})

describe('ConditionalColorValueProviderType', () => {
  const provider = new ConditionalColorValueProviderType({
    app: conditionalApp,
  })

  test('is compatible with both row coloring decorators', () => {
    expect(
      provider.getCompatibleDecoratorTypes().map((t) => t.getType())
    ).toEqual(['background_color', 'left_border_color'])
  })

  test('first matching rule wins', () => {
    const options = {
      colors: [
        rule(
          [{ id: '1', type: 'contains', field: 10, value: 'gold' }],
          'AND',
          'red'
        ),
        rule([], 'AND', 'gray'),
      ],
    }
    const row = { id: 1, field_10: 'GOLD customer' }
    expect(provider.getValue({ options, fields: conditionalFields, row })).toBe(
      'red'
    )
  })

  test('falls through to the next rule when nothing matches', () => {
    const options = {
      colors: [
        rule(
          [{ id: '1', type: 'contains', field: 10, value: 'gold' }],
          'AND',
          'red'
        ),
        rule([{ id: '2', type: 'equal', field: 11, value: 5 }], 'AND', 'blue'),
      ],
    }
    const row = { id: 1, field_10: 'silver', field_11: 5 }
    expect(provider.getValue({ options, fields: conditionalFields, row })).toBe(
      'blue'
    )
  })

  test('a rule without conditions is the default color for unmatched rows', () => {
    const options = {
      colors: [
        rule(
          [{ id: '1', type: 'contains', field: 10, value: 'gold' }],
          'AND',
          'red'
        ),
        rule([], 'AND', 'gray'),
      ],
    }
    const row = { id: 1, field_10: 'silver' }
    expect(provider.getValue({ options, fields: conditionalFields, row })).toBe(
      'gray'
    )
    expect(
      provider.getValue({
        options: { colors: [] },
        fields: conditionalFields,
        row,
      })
    ).toBe(null)
  })

  test('AND requires every condition, OR any of them', () => {
    const andRule = rule(
      [
        { id: '1', type: 'contains', field: 10, value: 'gold' },
        { id: '2', type: 'equal', field: 11, value: 5 },
      ],
      'AND',
      'red'
    )
    const orRule = rule(
      [
        { id: '1', type: 'contains', field: 10, value: 'gold' },
        { id: '2', type: 'equal', field: 11, value: 5 },
      ],
      'OR',
      'blue'
    )
    const partialRow = { id: 1, field_10: 'gold', field_11: 1 }
    expect(
      provider.getValue({
        options: { colors: [andRule] },
        fields: conditionalFields,
        row: partialRow,
      })
    ).toBe(null)
    expect(
      provider.getValue({
        options: { colors: [orRule] },
        fields: conditionalFields,
        row: partialRow,
      })
    ).toBe('blue')
  })

  test('conditions inside groups are respected', () => {
    const options = {
      colors: [
        {
          id: 'g',
          filters: [
            { id: '1', type: 'equal', field: 11, value: 9, group: 'a1' },
          ],
          filter_groups: [{ id: 'a1', filter_type: 'AND', parent_group: null }],
          operator: 'OR',
          color: 'purple',
        },
      ],
    }
    expect(
      provider.getValue({
        options,
        fields: conditionalFields,
        row: { id: 1, field_11: 9 },
      })
    ).toBe('purple')
    expect(
      provider.getValue({
        options,
        fields: conditionalFields,
        row: { id: 1, field_11: 1 },
      })
    ).toBe(null)
  })

  test('rules referencing unknown fields are skipped instead of crashing', () => {
    const options = {
      colors: [
        rule(
          [{ id: '1', type: 'contains', field: 999, value: 'x' }],
          'AND',
          'red'
        ),
        rule([], 'AND', 'gray'),
      ],
    }
    const row = { id: 1 }
    expect(provider.getValue({ options, fields: conditionalFields, row })).toBe(
      'gray'
    )
  })

  test('rejects colors outside the palette', () => {
    const options = {
      colors: [{ ...rule([], 'AND', '#ff0000') }],
    }
    expect(
      provider.getValue({
        options,
        fields: conditionalFields,
        row: { id: 1 },
      })
    ).toBe(null)
  })

  test('colors update when the configuration object changes', () => {
    const options = {
      colors: [rule([], 'AND', 'gray')],
    }
    const row = { id: 1 }
    expect(provider.getValue({ options, fields: conditionalFields, row })).toBe(
      'gray'
    )
    const updated = { colors: [rule([], 'AND', 'blue')] }
    expect(
      provider.getValue({ options: updated, fields: conditionalFields, row })
    ).toBe('blue')
  })
})

describe('ConditionalColorForm', () => {
  const mountForm = (colors) =>
    mount(ConditionalColorForm, {
      props: {
        view: { id: 1, type: 'grid' },
        table: { id: 1 },
        database: { id: 1 },
        fields: conditionalFields,
        readOnly: false,
        options: { colors },
      },
      global: {
        stubs: {
          Dropdown: { template: '<div class="stub-dropdown"><slot /></div>' },
          DropdownItem: { template: '<div class="stub-dropdown-item" />' },
          ButtonIcon: { template: '<button class="stub-icon" />' },
          ButtonText: {
            template:
              '<button class="stub-button" v-bind="$attrs"><slot /></button>',
          },
          ColorSelectContext: { template: '<div />' },
          ViewFieldConditionsForm: {
            template: '<div class="stub-conditions"><slot /></div>',
          },
        },
        mocks: { $t: (key) => key },
      },
    })

  test('renders one block per configured rule', () => {
    const wrapper = mountForm([rule([], 'AND', 'gray')])
    expect(wrapper.findAll('.conditional-color-form__rule')).toHaveLength(1)
    expect(
      wrapper.find('.conditional-color-form__default-badge').exists()
    ).toBe(true)
  })

  test('adding a rule emits the updated configuration', async () => {
    const wrapper = mountForm([rule([], 'AND', 'gray')])
    const buttons = wrapper.findAll('button.stub-button')
    await buttons[buttons.length - 1].trigger('click')
    const emitted = wrapper.emitted('update')
    expect(emitted).toHaveLength(1)
    expect(emitted[0][0].colors).toHaveLength(2)
    expect(emitted[0][0].colors[0].color).toBe('gray')
  })

  test('removing a rule emits the configuration without it', async () => {
    const wrapper = mountForm([
      rule([], 'AND', 'gray'),
      rule([], 'AND', 'blue'),
    ])
    await wrapper.findAll('button.stub-icon').at(0).trigger('click')
    const emitted = wrapper.emitted('update')
    expect(emitted[0][0].colors).toHaveLength(1)
    expect(emitted[0][0].colors[0].color).toBe('blue')
  })
})
