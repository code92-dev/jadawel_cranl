import moment from '@jadawel/modules/core/moment'
import { formatNumber } from '@jadawel/modules/arabase/dashboard/format'

/**
 * Turns a dispatched row value into something printable in a widget list.
 *
 * The list services serialize rows with user field names and run each value
 * through its field type's runtime conversion, so most values arrive as strings
 * or numbers already. The remaining shapes are the collection-ish field types:
 * a single select is an object, link rows and collaborators are arrays.
 *
 * This is deliberately a formatter and not the grid's field components. Reusing
 * those inside a dashboard widget would drag in editing, selection and row
 * context for read-only text. The cost is that rich types render as plain text.
 */
export function formatRecordValue(value) {
  if (value === null || value === undefined) {
    return ''
  }

  if (Array.isArray(value)) {
    return value.map(formatRecordValue).filter(Boolean).join(', ')
  }

  if (typeof value === 'object') {
    // Single select and file objects use `value`; link rows and collaborators
    // use `visible_name`; files fall back to `name`.
    return String(value.value ?? value.visible_name ?? value.name ?? '')
  }

  if (typeof value === 'boolean') {
    return value ? '✓' : ''
  }

  return String(value)
}

/**
 * The field names a list widget should show, given the widget's stored field ids
 * and the data source schema.
 *
 * Rows are keyed by field *name*, but the widget stores ids — a name would break
 * the moment someone renamed a field. The schema is what maps one to the other.
 * With nothing stored, the first few fields of the table are used, so a freshly
 * created widget shows something instead of an empty frame.
 */
export function resolveDisplayedFields(
  dataSource,
  fieldIds,
  fallbackCount = 3
) {
  const properties = dataSource?.schema?.items?.properties || {}

  const named = Object.entries(properties)
    .filter(([key]) => key.startsWith('field_'))
    .map(([key, property]) => ({
      id: parseInt(key.replace('field_', ''), 10),
      name: property.title,
      type: property.original_type || null,
      metadata: property.metadata || {},
    }))
    .filter(({ name }) => !!name)

  if (!fieldIds || fieldIds.length === 0) {
    return named.slice(0, fallbackCount)
  }

  // Ordered by the widget's stored order, not the table's, and silently skipping
  // ids whose field has since been deleted.
  return fieldIds
    .map((id) => named.find((field) => field.id === id))
    .filter((field) => field !== undefined)
}

const SELECT_TYPES = ['single_select', 'multiple_select']
const LINK_TYPES = ['link_row']
const PEOPLE_TYPES = [
  'multiple_collaborators',
  'created_by',
  'last_modified_by',
]
const NUMBER_TYPES = ['number', 'count', 'rollup', 'autonumber']
const DATE_TYPES = ['date', 'created_on', 'last_modified']

/** A select option colour as a class suffix, or neutral if it is not one. */
const optionColor = (color) =>
  typeof color === 'string' && /^[a-z-]+$/.test(color) ? color : 'light-gray'

const asList = (value) => (Array.isArray(value) ? value : [value])

/**
 * What a list widget cell shows, by field type: select options as coloured
 * pills (the colours the grid shows), linked records and people as chips,
 * numbers aligned and grouped, dates in the reader's language, booleans as a
 * tick. Anything else falls back to `formatRecordValue` text.
 *
 * `field` carries the `type` and `metadata` `resolveDisplayedFields` read off
 * the schema; the public dashboard may not have them, and gets text.
 */
export function describeRecordValue(value, field = {}, locale = 'en') {
  const empty =
    value === null ||
    value === undefined ||
    value === '' ||
    (Array.isArray(value) && value.length === 0)
  if (empty) {
    return { kind: 'empty', text: '' }
  }
  const type = field.type
  const metadata = field.metadata || {}

  if (typeof value === 'boolean' || type === 'boolean') {
    return { kind: 'boolean', value: value === true || value === 'true' }
  }
  if (SELECT_TYPES.includes(type)) {
    return {
      kind: 'pills',
      items: asList(value)
        .filter(Boolean)
        .map((option) => ({
          text: String(option.value ?? option.name ?? option),
          color: optionColor(option.color),
        })),
    }
  }
  if (LINK_TYPES.includes(type)) {
    return {
      kind: 'chips',
      items: asList(value).map((item) => ({ text: formatRecordValue(item) })),
    }
  }
  if (PEOPLE_TYPES.includes(type)) {
    return {
      kind: 'people',
      items: asList(value).map((person) => {
        const text = formatRecordValue(person)
        return { text, initial: text.trim().charAt(0).toUpperCase() }
      }),
    }
  }
  if (NUMBER_TYPES.includes(type) || type === 'rating') {
    const decimals = Number.isInteger(metadata.number_decimal_places)
      ? metadata.number_decimal_places
      : null
    const text = formatNumber(value, { locale, decimals })
    if (text !== null) {
      return type === 'rating'
        ? { kind: 'rating', value: Number(value), max: metadata.max_value || 5 }
        : { kind: 'number', text }
    }
  }
  if (DATE_TYPES.includes(type)) {
    const date = moment(value)
    if (date.isValid()) {
      const withTime =
        metadata.date_include_time === true && String(value).includes('T')
      return {
        kind: 'date',
        text: date
          .locale(locale)
          .format(withTime ? 'D MMM YYYY, HH:mm' : 'D MMM YYYY'),
      }
    }
  }
  return { kind: 'text', text: formatRecordValue(value) }
}
