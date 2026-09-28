/**
 * Theme presets for application-builder apps: complete themes drawn from the
 * same system as the redesigned dashboards. `themePresets.json` is generated
 * from `backend/src/arabase/builder/theme_presets.py`, the source of truth;
 * docs/APPLICATION_REDESIGN.md explains the presets.
 *
 * A preset leaves alignment and direction to the language the app's content
 * is written in: Arabic aligns everything to the right and lays the page out
 * right to left, English the other way.
 */
import data from '@jadawel/modules/arabase/builder/themePresets.json'

export const THEME_PRESETS = data.presets
export const DEFAULT_THEME_PRESET = data.default
export const CONTENT_LANGUAGES = Object.keys(data.languages)

export function themePreset(key) {
  return THEME_PRESETS.find((preset) => preset.key === key) || null
}

/** Every theme value the preset `key` sets for content in `language`. */
export function presetTheme(key, language = 'ar') {
  const preset = themePreset(key)
  if (!preset) {
    return null
  }
  const languageValues = data.languages[language] || data.languages.ar
  return { ...preset.values, ...languageValues }
}

function sameValue(first, second) {
  if (Array.isArray(first) || Array.isArray(second)) {
    return JSON.stringify(first) === JSON.stringify(second)
  }
  return String(first).toLowerCase() === String(second).toLowerCase()
}

/** The preset the theme still matches exactly, or null once it was changed. */
export function matchingPreset(theme) {
  if (!theme) {
    return null
  }
  const preset = THEME_PRESETS.find((candidate) =>
    Object.entries(candidate.values).every(([key, value]) =>
      sameValue(theme[key], value)
    )
  )
  return preset ? preset.key : null
}

/**
 * The language an app's content is written in, as far as its theme tells:
 * its direction when one is set, else its body alignment, else the language
 * of the interface it is edited in.
 */
export function contentLanguageOf(theme, locale = 'ar') {
  if (theme?.page_direction === 'rtl') {
    return 'ar'
  }
  if (theme?.page_direction === 'ltr') {
    return 'en'
  }
  if (theme?.body_text_alignment === 'right') {
    return 'ar'
  }
  return String(locale).split('-')[0] === 'ar' ? 'ar' : 'en'
}
