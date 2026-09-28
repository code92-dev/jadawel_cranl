/**
 * One-click box styles for container elements, the builder's counterpart of a
 * dashboard widget's accent: the card, tinted panel and outline the dashboards
 * are built from, in the app's own theme colours. Each is a set of the
 * element's ordinary `style_*` values, so everything stays editable below.
 *
 * Sanad draws the same boxes through `backend/src/arabase/builder/box_styles.py`;
 * keep the two in step — `elementQuickStyles.spec.js` and
 * `test_builder_box_styles.py` pin the same values.
 */

/** Elements that hold other elements and are worth framing. */
export const QUICK_STYLE_ELEMENTS = [
  'simple_container',
  'column',
  'repeat',
  'form_container',
]

export const QUICK_STYLES = ['plain', 'card', 'tinted', 'outlined']

const SIDES = ['top', 'bottom', 'left', 'right']

function sides(prefix, value) {
  return Object.fromEntries(
    SIDES.map((side) => [`${prefix}_${side}_${value[0]}`, value[1]])
  )
}

function padding(block, inline) {
  return {
    style_padding_top: block,
    style_padding_bottom: block,
    style_padding_left: inline,
    style_padding_right: inline,
  }
}

function channels(hex) {
  const value = String(hex || '').replace('#', '')
  if (!/^[0-9a-f]{6}([0-9a-f]{2})?$/i.test(value)) {
    return null
  }
  return [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16))
}

/** `color` mixed into `base` by `amount` (0–1), as #rrggbbff. */
export function mix(color, base, amount) {
  const a = channels(color)
  const b = channels(base)
  if (!a || !b) {
    return base
  }
  const mixed = a.map((channel, i) =>
    Math.round(channel * amount + b[i] * (1 - amount))
      .toString(16)
      .padStart(2, '0')
  )
  return `#${mixed.join('')}ff`
}

/** The colour cards are drawn in: the theme's table cells, else white. */
export function surfaceOf(theme) {
  return channels(theme?.table_cell_background_color)
    ? theme.table_cell_background_color.toLowerCase()
    : '#ffffffff'
}

/** The `style_*` values of the quick style `key` for a theme. */
export function quickStyle(key, theme = {}) {
  const surface = surfaceOf(theme)
  const noBorder = sides('style_border', ['size', 0])
  const line = {
    ...sides('style_border', ['size', 1]),
    ...sides('style_border', ['color', 'border']),
  }
  switch (key) {
    case 'plain':
      return {
        style_background: 'none',
        style_background_radius: 0,
        style_border_radius: 0,
        ...noBorder,
        ...padding(10, 20),
      }
    case 'card':
      return {
        style_background: 'color',
        style_background_color: surface,
        style_background_radius: 12,
        style_border_radius: 12,
        ...line,
        ...padding(24, 24),
      }
    case 'tinted':
      return {
        style_background: 'color',
        style_background_color: mix(theme?.primary_color, surface, 0.08),
        style_background_radius: 12,
        style_border_radius: 12,
        ...noBorder,
        ...padding(24, 24),
      }
    case 'outlined':
      return {
        style_background: 'none',
        style_background_radius: 12,
        style_border_radius: 12,
        ...line,
        ...padding(20, 20),
      }
    default:
      return null
  }
}

/** The quick style an element still has exactly, or null. */
export function matchingQuickStyle(element, theme) {
  return (
    QUICK_STYLES.find((key) =>
      Object.entries(quickStyle(key, theme)).every(
        ([name, value]) =>
          String(element?.[name]).toLowerCase() === String(value).toLowerCase()
      )
    ) || null
  )
}
