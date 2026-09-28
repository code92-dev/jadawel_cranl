import {
  GRID_GAP,
  ROW_HEIGHT,
  columnWidth,
  sizeFromDrag,
  widgetSize,
} from '@jadawel/modules/arabase/dashboard/layout'

describe('dashboard grid layout', () => {
  // 12 columns of 70px with 11 gaps of 16px.
  const boardWidth = 12 * 70 + 11 * GRID_GAP
  const columnStep = 70 + GRID_GAP
  const rowStep = ROW_HEIGHT + GRID_GAP

  test('a column is the board less its gaps, split twelve ways', () => {
    expect(columnWidth(boardWidth)).toBe(70)
  })

  test('sizes are clamped to the grid and the type minimum', () => {
    expect(widgetSize({ width: 20, height: 0 })).toEqual({
      width: 12,
      height: 4,
    })
    expect(
      widgetSize({ width: 1, height: 1 }, { width: 3, height: 2 })
    ).toEqual({ width: 3, height: 2 })
    expect(widgetSize({})).toEqual({ width: 12, height: 4 })
  })

  test('dragging the corner snaps to the nearest cell', () => {
    const start = { width: 3, height: 2 }

    expect(
      sizeFromDrag({
        start,
        dx: columnStep * 2.6,
        dy: rowStep * 1.4,
        boardWidth,
      })
    ).toEqual({ width: 6, height: 3 })
  })

  test('in right-to-left the widget grows as the pointer moves left', () => {
    const start = { width: 3, height: 2 }

    expect(
      sizeFromDrag({ start, dx: -columnStep * 3, dy: 0, boardWidth, rtl: true })
    ).toEqual({ width: 6, height: 2 })
    expect(
      sizeFromDrag({ start, dx: columnStep * 3, dy: 0, boardWidth, rtl: false })
    ).toEqual({ width: 6, height: 2 })
  })

  test('a drag never goes below the minimum or past the grid', () => {
    const start = { width: 4, height: 4 }
    const minSize = { width: 3, height: 3 }

    expect(
      sizeFromDrag({
        start,
        dx: -columnStep * 10,
        dy: -rowStep * 10,
        boardWidth,
        minSize,
      })
    ).toEqual({ width: 3, height: 3 })
    expect(
      sizeFromDrag({
        start,
        dx: columnStep * 20,
        dy: rowStep * 20,
        boardWidth,
        minSize,
      })
    ).toEqual({ width: 12, height: 12 })
  })
})
