/**
 * Flatten a DRF error response into one readable line.
 *
 * The table-access endpoints answer with field errors such as
 * `{"error": "ERROR_TABLE_NOT_IN_WORKSPACE"}`. Showing the code next to the
 * translated banner turns an opaque 400 into something an admin can act on.
 */
export function describeApiError(error) {
  const data = error?.response?.data
  if (!data) return ''
  if (typeof data === 'string') return data
  const parts = []
  const walk = (value, field) => {
    if (Array.isArray(value)) {
      value.forEach((item) => walk(item, field))
    } else if (value && typeof value === 'object') {
      Object.entries(value).forEach(([key, item]) =>
        walk(item, field ? `${field}.${key}` : key)
      )
    } else if (value !== null && value !== undefined && value !== '') {
      parts.push(field ? `${field}: ${value}` : String(value))
    }
  }
  walk(data, '')
  return parts.join(' · ')
}
