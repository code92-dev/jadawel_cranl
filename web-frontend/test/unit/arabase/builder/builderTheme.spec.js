import {
  fontFamilyStack,
  InterFontFamilyType,
  GeorgiaFontFamilyType,
  CourierNewFontFamilyType,
} from '@jadawel/modules/builder/fontFamilyTypes'
import { ThemeConfigBlockType } from '@jadawel/modules/builder/themeConfigBlockTypes'

describe('builder theme CSS', () => {
  test('sans-serif fonts fall back to the Arabic face, generics are unquoted', () => {
    const app = useNuxtApp()

    expect(fontFamilyStack(new InterFontFamilyType(app))).toBe(
      '"Inter","IBM Plex Sans Arabic",sans-serif'
    )
    expect(fontFamilyStack(new GeorgiaFontFamilyType(app))).toBe(
      '"Georgia",serif'
    )
    expect(fontFamilyStack(new CourierNewFontFamilyType(app))).toBe(
      '"Courier new",monospace'
    )
  })

  test('the page direction becomes a CSS variable, unless automatic', () => {
    const { $registry } = useNuxtApp()
    const blocks = $registry.getOrderedList('themeConfigBlock')
    const style = (theme) => ThemeConfigBlockType.getAllStyles(blocks, theme)

    expect(style({ page_direction: 'rtl' })['--page-direction']).toBe('rtl')
    expect(style({ page_direction: 'ltr' })['--page-direction']).toBe('ltr')
    expect(
      style({ page_direction: 'auto' })['--page-direction']
    ).toBeUndefined()
    expect(style({ body_font_family: 'inter' })['--body-font-family']).toBe(
      '"Inter","IBM Plex Sans Arabic",sans-serif'
    )
  })
})
