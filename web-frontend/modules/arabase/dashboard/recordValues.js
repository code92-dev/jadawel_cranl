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
