/**
 * The dashboard board's grid: 12 columns of 72 px rows with a 16 px gap.
 *
 * A widget's `width` and `height` are spans on it. Twelve columns give the
 * sizes dashboards are built from — quarters, thirds, halves — and rows short
 * enough that a section heading takes one and a key number two. Mirrors
 * `GRID_COLUMNS`/`MAX_HEIGHT` in `jadawel.contrib.dashboard.widgets.models` and
 * the grid in `dashboard_canvas.scss`.
 */

export const GRID_COLUMNS = 12
export const MAX_HEIGHT = 12
export const ROW_HEIGHT = 72
export const GRID_GAP = 16

export const DEFAULT_SIZE = { width: GRID_COLUMNS, height: 4 }
export const DEFAULT_MIN_SIZE = { width: 2, height: 1 }

/** Widths offered by the size menu, as fractions of the row. */
export const WIDTH_PRESETS = [3, 4, 6, 8, 12]
/** Heights offered by the size menu, in rows. */
export const HEIGHT_PRESETS = [1, 2, 3, 4, 5, 6, 8]

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

/**
 * A widget's spans, clamped to the grid. A widget mid-creation has none yet and
 * takes the default.
 */
export function widgetSize(widget, minSize = DEFAULT_MIN_SIZE) {
  const width = parseInt(widget?.width) || DEFAULT_SIZE.width
  const height = parseInt(widget?.height) || DEFAULT_SIZE.height
  return {
    width: clamp(width, Math.min(minSize.width, GRID_COLUMNS), GRID_COLUMNS),
    height: clamp(height, Math.min(minSize.height, MAX_HEIGHT), MAX_HEIGHT),
  }
}

/** The width of one column on a board `boardWidth` pixels wide. */
export function columnWidth(boardWidth) {
  return (boardWidth - GRID_GAP * (GRID_COLUMNS - 1)) / GRID_COLUMNS
}

/**
 * The size a resize drag has reached. `dx`/`dy` are the pointer's movement
 * since the drag began; in right-to-left the widget's end edge is on the left,
 * so moving left makes it wider. Rounds to the nearest cell so the widget snaps
 * where the pointer is closest to, and never goes below the type's minimum.
 */
export function sizeFromDrag({
  start,
  dx,
  dy,
  boardWidth,
  rtl = false,
  minSize = DEFAULT_MIN_SIZE,
}) {
  const columnStep = columnWidth(boardWidth) + GRID_GAP
  const rowStep = ROW_HEIGHT + GRID_GAP
  const inline = rtl ? -dx : dx
  return {
    width: clamp(
      Math.round(start.width + inline / columnStep),
      minSize.width,
      GRID_COLUMNS
    ),
    height: clamp(
      Math.round(start.height + dy / rowStep),
      minSize.height,
      MAX_HEIGHT
    ),
  }
}

/**
 * How a width reads to a person: "Quarter", "Half"… or "5 / 12" for the rest.
 */
export function widthFraction(width) {
  return { 3: '1/4', 4: '1/3', 6: '1/2', 8: '2/3', 9: '3/4', 12: '1' }[width]
}
