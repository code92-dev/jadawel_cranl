/**
 * Number formatting for dashboard widgets.
 *
 * Arabic reads with Western digits across Jadawel (docs/GLOSSARY_AR.md), so the
 * Arabic locale is asked for the Latin numbering system explicitly; left to
 * itself `Intl` would print Eastern Arabic digits.
 */

const formatters = new Map()

export function intlLocale(locale) {
  const base = String(locale || 'en').split('-')[0]
  return base === 'ar' ? 'ar-u-nu-latn' : locale || 'en'
}

function formatter(locale, options) {
  const key = `${locale}|${JSON.stringify(options)}`
  if (!formatters.has(key)) {
    formatters.set(key, new Intl.NumberFormat(intlLocale(locale), options))
  }
  return formatters.get(key)
}

/**
 * A number from what an aggregation or a row value arrives as. Numbers are
 * serialized as strings by their field type ("1610000.00"), and an empty table
 * gives back null; anything that is not a finite number is `null`.
 */
export function toNumber(value) {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }
  if (typeof value !== 'string' || value.trim() === '') {
    return null
  }
  const parsed = Number(value.trim())
  return Number.isFinite(parsed) ? parsed : null
}

/**
 * Formats `value` with thousands separators, optional compact notation
 * ("1.6M", "1.6 مليون"), fixed decimals and a prefix or suffix.
 *
 * Without fixed decimals, whole numbers print whole and others keep up to two
 * decimals (one in compact notation, where more is noise).
 */
export function formatNumber(value, options = {}) {
  const number = toNumber(value)
  if (number === null) {
    return null
  }
  const { locale, decimals = null, compact = false } = options
  const intlOptions = compact
    ? {
        notation: 'compact',
        maximumFractionDigits: decimals ?? 1,
        minimumFractionDigits: decimals ?? 0,
      }
    : {
        maximumFractionDigits: decimals ?? 2,
        minimumFractionDigits: decimals ?? 0,
      }
  return withAffixes(formatter(locale, intlOptions).format(number), options)
}

/**
 * Adds a unit before or after an already formatted value. A space separates
 * them unless the unit is a symbol that sits tight against a number (%, $).
 */
export function withAffixes(text, { prefix = '', suffix = '' } = {}) {
  const tight = (unit) => /^[%‰$€£¥]$/.test(unit)
  let result = String(text)
  if (prefix) {
    result = tight(prefix) ? `${prefix}${result}` : `${prefix} ${result}`
  }
  if (suffix) {
    result = tight(suffix) ? `${result}${suffix}` : `${result} ${suffix}`
  }
  return result
}

/**
 * Whether a string an aggregation's own formatter produced is a bare number
 * ("1610000", "1,610,000.50") that can safely be formatted again. Currency,
 * durations, dates and percentages come back decorated and are left alone.
 */
export function isPlainNumber(text) {
  return typeof text === 'number' || /^-?[\d,]+(\.\d+)?$/.test(String(text))
}

/**
 * The value a key-number widget shows. The aggregation's own formatter owns
 * units such as currency or durations; plain numbers are formatted here, with
 * the widget's decimals, compact notation and affixes.
 */
export function formatAggregate(raw, formatted, options = {}) {
  if (raw === null || raw === undefined || raw === '') {
    return null
  }
  if (isPlainNumber(formatted ?? raw)) {
    return formatNumber(toNumber(raw) ?? toNumber(formatted), options)
  }
  return withAffixes(formatted ?? raw, options)
}
