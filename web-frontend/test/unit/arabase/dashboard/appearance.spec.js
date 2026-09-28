import { readFileSync } from 'fs'
import { resolve } from 'path'

import {
  ACCENT_COLORS,
  ICONS,
  accentOf,
  iconOf,
  numberFormatOf,
  seriesPalette,
  withAlpha,
} from '@jadawel/modules/arabase/dashboard/appearance'

describe('widget appearance', () => {
  test('only known colours and icons are used', () => {
    expect(accentOf({ appearance: { color: 'blue' } })).toBe('blue')
    expect(accentOf({ appearance: { color: 'url(x)' } })).toBe('primary')
    expect(accentOf({})).toBe('primary')
    expect(iconOf({ appearance: { icon: 'coins' } })).toBe('coins')
    expect(iconOf({ appearance: { icon: 'x" onclick="' } })).toBeNull()
    expect(iconOf({}, 'calendar')).toBe('calendar')
  })

  test('number options are cleaned before they reach Intl', () => {
    expect(
      numberFormatOf({
        appearance: { decimals: 9, prefix: 5, suffix: 'SAR', compact: 'yes' },
      })
    ).toEqual({ decimals: 4, compact: false, prefix: '', suffix: 'SAR' })
  })

  test('the series palette starts with the accent and does not repeat early', () => {
    const palette = seriesPalette('blue', 8)

    expect(palette[0]).toBe('#4783db')
    expect(new Set(palette).size).toBe(8)
  })

  test('translucent fills', () => {
    expect(withAlpha('#278053', 0.5)).toBe('rgba(39, 128, 83, 0.5)')
    expect(withAlpha('red', 0.5)).toBe('red')
  })

  test('the lists match what Sanad is offered', () => {
    // backend/src/arabase/dashboard/appearance.py mirrors these lists.
    const python = readFileSync(
      resolve(
        __dirname,
        '../../../../../backend/src/arabase/dashboard/appearance.py'
      ),
      'utf8'
    )
    const tuple = (name) =>
      [
        ...python
          .split(`${name} = (`)[1]
          .split(')')[0]
          .matchAll(/"([^"]+)"/g),
      ].map((match) => match[1])

    expect(tuple('ACCENT_COLORS')).toEqual(ACCENT_COLORS)
    expect(tuple('ICONS')).toEqual(ICONS)
  })
})
