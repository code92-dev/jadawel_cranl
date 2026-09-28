import {
  describeRecordValue,
  formatRecordValue,
  resolveDisplayedFields,
} from '@jadawel/modules/arabase/dashboard/recordValues'

describe('formatRecordValue', () => {
  test('empty values render as nothing rather than "null"', () => {
    expect(formatRecordValue(null)).toBe('')
    expect(formatRecordValue(undefined)).toBe('')
  })

  test('primitives pass through as text', () => {
    expect(formatRecordValue('Riyadh')).toBe('Riyadh')
    expect(formatRecordValue(42)).toBe('42')
    // Zero is a value, not an absence — it must not be swallowed.
    expect(formatRecordValue(0)).toBe('0')
  })

  test('booleans render as a tick or nothing', () => {
    expect(formatRecordValue(true)).toBe('✓')
    expect(formatRecordValue(false)).toBe('')
  })

  test('a single select object renders its value', () => {
    expect(formatRecordValue({ id: 1, value: 'Open', color: 'blue' })).toBe(
      'Open'
    )
  })

  test('link rows and collaborators render as a joined list', () => {
    expect(
      formatRecordValue([{ visible_name: 'Sara' }, { visible_name: 'Omar' }])
    ).toBe('Sara, Omar')
  })

  test('empty entries do not leave dangling separators', () => {
    expect(formatRecordValue([{ visible_name: 'Sara' }, null])).toBe('Sara')
  })
})

describe('resolveDisplayedFields', () => {
  const names = (fields) => fields.map(({ id, name }) => ({ id, name }))

  const dataSource = {
    schema: {
      items: {
        properties: {
          id: { title: 'Id' },
          field_1: { title: 'Name' },
          field_2: { title: 'Amount' },
          field_3: { title: 'Region' },
          field_4: { title: 'Notes' },
        },
      },
    },
  }

  test('with nothing stored it falls back to the first fields', () => {
    expect(names(resolveDisplayedFields(dataSource, []))).toEqual([
      { id: 1, name: 'Name' },
      { id: 2, name: 'Amount' },
      { id: 3, name: 'Region' },
    ])
  })

  test('stored ids are honoured in their own order', () => {
    expect(names(resolveDisplayedFields(dataSource, [3, 1]))).toEqual([
      { id: 3, name: 'Region' },
      { id: 1, name: 'Name' },
    ])
  })

  test('an id whose field was deleted is skipped, not rendered blank', () => {
    expect(names(resolveDisplayedFields(dataSource, [1, 99]))).toEqual([
      { id: 1, name: 'Name' },
    ])
  })

  test('a data source with no schema yet yields nothing', () => {
    expect(resolveDisplayedFields(undefined, [])).toEqual([])
    expect(resolveDisplayedFields({}, [1])).toEqual([])
  })
})

describe('describeRecordValue', () => {
  test('empty values of any shape are empty', () => {
    for (const value of [null, undefined, '', []]) {
      expect(describeRecordValue(value, { type: 'text' }).kind).toBe('empty')
    }
  })

  test('select options become pills in their own colours', () => {
    expect(
      describeRecordValue(
        [
          { id: 1, value: 'Red', color: 'light-red' },
          { id: 2, value: 'Odd', color: 'not a colour!' },
        ],
        { type: 'multiple_select' }
      )
    ).toEqual({
      kind: 'pills',
      items: [
        { text: 'Red', color: 'light-red' },
        // A value that is not a colour name never reaches the class list.
        { text: 'Odd', color: 'light-gray' },
      ],
    })
  })

  test('numbers keep the field decimals and group thousands', () => {
    expect(
      describeRecordValue('1234567.5', {
        type: 'number',
        metadata: { number_decimal_places: 2 },
      })
    ).toEqual({ kind: 'number', text: '1,234,567.50' })
  })

  test('Arabic keeps Western digits', () => {
    expect(
      describeRecordValue('1234', { type: 'number', metadata: {} }, 'ar').text
    ).toMatch(/^1.234$/)
  })

  test('people get an initial for their avatar', () => {
    expect(
      describeRecordValue([{ id: 1, name: 'sara' }], {
        type: 'multiple_collaborators',
      })
    ).toEqual({ kind: 'people', items: [{ text: 'sara', initial: 'S' }] })
  })

  test('a date is written out, a boolean is a tick', () => {
    expect(describeRecordValue('2026-03-05', { type: 'date' })).toEqual({
      kind: 'date',
      text: '5 Mar 2026',
    })
    expect(describeRecordValue(true, { type: 'boolean' })).toEqual({
      kind: 'boolean',
      value: true,
    })
  })

  test('without a field type the value is plain text', () => {
    expect(describeRecordValue({ value: 'Won' }, {})).toEqual({
      kind: 'text',
      text: 'Won',
    })
  })
})
