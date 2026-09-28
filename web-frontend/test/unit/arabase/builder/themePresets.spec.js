import { readFileSync } from 'fs'
import { resolve } from 'path'

import {
  DEFAULT_THEME_PRESET,
  THEME_PRESETS,
  contentLanguageOf,
  matchingPreset,
  presetTheme,
} from '@jadawel/modules/arabase/builder/themePresets'

describe('theme presets', () => {
  test('there are five, the default first', () => {
    expect(THEME_PRESETS.map((preset) => preset.key)).toEqual([
      'jadawel',
      'ocean',
      'heritage',
      'sand',
      'stone',
    ])
    expect(DEFAULT_THEME_PRESET).toBe('jadawel')
  })

  test('a preset is applied for the language of the content', () => {
    const arabic = presetTheme('ocean', 'ar')
    const english = presetTheme('ocean', 'en')

    expect(arabic.primary_color).toBe('#0059fcff')
    expect(arabic.heading_1_text_alignment).toBe('right')
    expect(arabic.page_direction).toBe('rtl')
    expect(english.heading_1_text_alignment).toBe('left')
    expect(english.page_direction).toBe('ltr')
    expect(english.button_text_alignment).toBe('center')
    expect(presetTheme('nope')).toBeNull()
  })

  test('a theme matches a preset until one of its values changes', () => {
    const theme = presetTheme('sand', 'en')

    expect(matchingPreset(theme)).toBe('sand')
    // Stored colours may come back in capitals.
    expect(
      matchingPreset({
        ...theme,
        primary_color: theme.primary_color.toUpperCase(),
      })
    ).toBe('sand')
    expect(matchingPreset({ ...theme, button_border_radius: 2 })).toBeNull()
    expect(matchingPreset(null)).toBeNull()
  })

  test('the content language is read from the theme', () => {
    expect(contentLanguageOf({ page_direction: 'rtl' }, 'en')).toBe('ar')
    expect(contentLanguageOf({ page_direction: 'ltr' }, 'ar')).toBe('en')
    expect(contentLanguageOf({ body_text_alignment: 'right' }, 'en')).toBe('ar')
    expect(contentLanguageOf({ page_direction: 'auto' }, 'en-GB')).toBe('en')
    expect(contentLanguageOf({}, 'ar')).toBe('ar')
  })

  test('the presets are the backend module generated as JSON', () => {
    const python = readFileSync(
      resolve(
        __dirname,
        '../../../../../backend/src/arabase/builder/theme_presets.py'
      ),
      'utf8'
    )
    for (const preset of THEME_PRESETS) {
      expect(python).toContain(`"primary": "${preset.swatches.primary}"`)
    }
  })
})
