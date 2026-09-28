/**
 * The presentation options a widget's `appearance` can hold.
 *
 * The API stores `appearance` as a small flat dict and leaves its meaning to this
 * file, so anything not listed here is ignored rather than rendered — a colour or
 * icon name ends up in a class, never in markup. Sanad chooses from the same
 * lists (`backend/src/arabase/dashboard/appearance.py`); `appearance.spec.js`
 * keeps the two in step.
 */

export const ACCENT_COLORS = [
  'primary',
  'blue',
  'cyan',
  'green',
  'yellow',
  'red',
  'magenta',
  'purple',
  'neutral',
]

export const ICONS = [
  'coins',
  'cash',
  'wallet',
  'bank',
  'credit-card',
  'cart',
  'shop',
  'box-iso',
  'truck',
  'graph-up',
  'graph-down',
  'percentage',
  'user',
  'group',
  'user-crown',
  'building',
  'calendar',
  'clock',
  'hourglass',
  'check-circle',
  'warning-triangle',
  'triangle-flag',
  'trophy',
  'star',
  'rocket',
  'light-bulb',
  'help-circle',
  'task-list',
  'headset-help',
  'mail',
  'phone',
  'globe',
]

/**
 * The hex each accent paints with where CSS cannot reach: inside a chart's
 * canvas. `primary` is read from the workspace theme at draw time.
 */
export const ACCENT_HEX = {
  primary: '#278053',
  blue: '#4783db',
  cyan: '#0ea3b7',
  green: '#0eaa42',
  yellow: '#e5b33d',
  red: '#e35d6a',
  magenta: '#cb5f9e',
  purple: '#9d48d3',
  neutral: '#667063',
}

/**
 * Series colours in the order a chart hands them out. The accent comes first,
 * so a one-series chart is simply "the widget's colour"; the rest are spaced
 * around the wheel so neighbours never look alike.
 */
export const SERIES_ORDER = [
  'primary',
  'blue',
  'yellow',
  'purple',
  'cyan',
  'red',
  'magenta',
  'neutral',
]

const pick = (list, value, fallback = null) =>
  list.includes(value) ? value : fallback

export function appearanceOf(widget) {
  const appearance = widget?.appearance
  return appearance && typeof appearance === 'object' ? appearance : {}
}

export function accentOf(widget, fallback = 'primary') {
  return pick(ACCENT_COLORS, appearanceOf(widget).color, fallback)
}

export function iconOf(widget, fallback = null) {
  return pick(ICONS, appearanceOf(widget).icon, fallback)
}

/**
 * The number options of a widget, cleaned: a decimals value outside 0–4 or a
 * prefix that is not a string would otherwise leak into `Intl.NumberFormat`.
 */
export function numberFormatOf(widget) {
  const appearance = appearanceOf(widget)
  const decimals = Number.isInteger(appearance.decimals)
    ? Math.min(4, Math.max(0, appearance.decimals))
    : null
  const text = (value) => (typeof value === 'string' ? value.slice(0, 12) : '')
  return {
    decimals,
    compact: appearance.compact === true,
    prefix: text(appearance.prefix),
    suffix: text(appearance.suffix),
  }
}

/**
 * The workspace's accent, which a theme can override through
 * `--jadawel-primary-500`. Canvas drawing cannot use a CSS variable, so it is
 * resolved here once per draw.
 */
export function resolvePrimaryHex() {
  if (typeof document === 'undefined') {
    return ACCENT_HEX.primary
  }
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue('--jadawel-primary-500')
    .trim()
  return value || ACCENT_HEX.primary
}

export function accentHex(name) {
  return name === 'primary' ? resolvePrimaryHex() : ACCENT_HEX[name]
}

/**
 * `count` series colours starting from the widget's accent.
 */
export function seriesPalette(accent, count) {
  const order = [accent, ...SERIES_ORDER.filter((name) => name !== accent)]
  return Array.from({ length: count }, (_, index) =>
    accentHex(order[index % order.length])
  )
}

/**
 * A translucent version of a hex colour, for area fills and hover states.
 */
export function withAlpha(hex, alpha) {
  const match = /^#?([0-9a-f]{6})$/i.exec(String(hex).trim())
  if (!match) {
    return hex
  }
  const value = parseInt(match[1], 16)
  const r = (value >> 16) & 255
  const g = (value >> 8) & 255
  const b = value & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
