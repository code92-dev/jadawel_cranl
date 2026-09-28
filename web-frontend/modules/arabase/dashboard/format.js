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

/** U+20C1 SAUDI RIYAL SIGN; `saudi_riyal.scss` supplies its glyph. */
export const SAUDI_RIYAL = '⃁'

// The ways the riyal is written as a unit: ر.س (with or without dots and
// spaces), ريال / ريال سعودي, SAR, SR and the older ligature ﷼.
const RIYAL_UNIT = /^(ر\s?\.?\s?س\.?|ريالا?(\sسعودي)?|SAR|SR|﷼|⃁)$/i

// The same abbreviations inside a sentence or a title. The words ريال and
// ريالات are left alone there: in prose they are words, not units.
const RIYAL_IN_TEXT =
  /(^|[\s(（[،,:/-])(ر\s?\.\s?س\.?|SAR|﷼)(?=$|[\s)）\].،,:/-])/gi

const isRtl = () =>
  typeof document !== 'undefined' && document.documentElement.dir === 'rtl'

export function isRiyal(unit) {
  return typeof unit === 'string' && RIYAL_UNIT.test(unit.trim())
}

/**
 * Puts the riyal sign beside a formatted amount. The Saudi Central Bank's
 * guidance puts the sign to the left of the number in Arabic and English
 * alike, with a space: so it follows an Arabic amount (right to left, the end
 * is the left) and precedes an English one. A no-break space keeps the two
 * on one line.
 */
export function withRiyal(text, rtl = isRtl()) {
  return rtl ? `${text}\u00A0${SAUDI_RIYAL}` : `${SAUDI_RIYAL}\u00A0${text}`
}

/**
 * Replaces the riyal's abbreviations in a title or a sentence with its sign:
 * "Budget (SAR)" becomes "Budget (⃁)", "المبلغ ر.س" becomes "المبلغ ⃁".
 * Text with no abbreviation comes back unchanged.
 */
export function riyalText(text) {
  if (typeof text !== 'string' || text === '') {
    return text
  }
  const replaced = text.replace(
    RIYAL_IN_TEXT,
    (match, before) => `${before}${SAUDI_RIYAL}`
  )
  // "SAR" was a Latin word and held its place in an English title on an
  // Arabic page; the sign has no direction of its own and drifted to the
  // front ("(⃁) Budget"). A first-strong isolate (U+2068…U+2069) lays the text
  // out in its own direction again.
  return replaced === text ? text : `\u2068${replaced}\u2069`
}

/**
 * Adds a unit before or after an already formatted value. A space separates
 * them unless the unit is a symbol that sits tight against a number (%, $).
 * The Saudi riyal, however it is written, becomes its sign, placed as the
 * central bank asks.
 */
export function withAffixes(text, { prefix = '', suffix = '' } = {}) {
  let result = String(text)
  let riyal = false
  if (isRiyal(prefix)) {
    riyal = true
    prefix = ''
  }
  if (isRiyal(suffix)) {
    riyal = true
    suffix = ''
  }
  const tight = (unit) => /^[%‰$€£¥]$/.test(unit)
  if (prefix) {
    result = tight(prefix) ? `${prefix}${result}` : `${prefix} ${result}`
  }
  if (suffix) {
    result = tight(suffix) ? `${result}${suffix}` : `${result} ${suffix}`
  }
  // A value its field already marked as riyals keeps its one sign.
  return riyal && !result.includes(SAUDI_RIYAL) ? withRiyal(result) : result
}

/**
 * A value some other formatter already decorated ("1,000 SAR", "ر.س 50"):
 * a riyal unit at either end moves to where the sign belongs, one in the
 * middle is swapped in place.
 */
export function riyalFormatted(text) {
  if (typeof text !== 'string') {
    return text
  }
  const parts = text.trim().split(/\s+/)
  if (parts.length > 1 && isRiyal(parts[parts.length - 1])) {
    return withRiyal(parts.slice(0, -1).join(' '))
  }
  if (parts.length > 1 && isRiyal(parts[0])) {
    return withRiyal(parts.slice(1).join(' '))
  }
  return riyalText(text)
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
  return withAffixes(riyalFormatted(String(formatted ?? raw)), options)
}
