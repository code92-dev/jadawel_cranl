import { mountSuspended } from '@nuxt/test-utils/runtime'
import ElementQuickStyles from '@jadawel/modules/arabase/builder/components/ElementQuickStyles.vue'
import {
  matchingQuickStyle,
  mix,
  quickStyle,
  surfaceOf,
} from '@jadawel/modules/arabase/builder/elementQuickStyles'
import { presetTheme } from '@jadawel/modules/arabase/builder/themePresets'

describe('element quick styles', () => {
  const theme = presetTheme('jadawel', 'ar')

  test('a card is drawn in the theme surface with a border in the theme colour', () => {
    const card = quickStyle('card', theme)

    expect(card.style_background_color).toBe('#ffffffff')
    expect(card.style_border_top_color).toBe('border')
    expect(card.style_border_left_size).toBe(1)
    expect(card.style_border_radius).toBe(12)
    expect(card.style_padding_right).toBe(24)
    // A theme whose cells are tinted draws its cards in that tint.
    expect(
      quickStyle('card', { table_cell_background_color: '#FAF8F2FF' })
        .style_background_color
    ).toBe('#faf8f2ff')
  })

  test('a card has the values Sanad draws (test_builder_box_styles.py)', () => {
    const sides = (name, value) =>
      Object.fromEntries(
        ['top', 'bottom', 'left', 'right'].map((side) => [
          `style_border_${side}_${name}`,
          value,
        ])
      )

    expect(quickStyle('card', theme)).toEqual({
      style_background: 'color',
      style_background_color: '#ffffffff',
      style_background_radius: 12,
      style_border_radius: 12,
      ...sides('size', 1),
      ...sides('color', 'border'),
      style_padding_top: 24,
      style_padding_bottom: 24,
      style_padding_left: 24,
      style_padding_right: 24,
    })
  })

  test('a tinted panel mixes the primary colour into the surface', () => {
    expect(mix('#278053ff', '#ffffffff', 0.08)).toBe('#eef5f1ff')
    expect(quickStyle('tinted', theme).style_background_color).toBe('#eef5f1ff')
    expect(mix('primary', '#ffffffff', 0.5)).toBe('#ffffffff')
    expect(surfaceOf({})).toBe('#ffffffff')
    expect(quickStyle('nope', theme)).toBeNull()
  })

  test('the element style it still has is recognised', () => {
    expect(matchingQuickStyle(quickStyle('outlined', theme), theme)).toBe(
      'outlined'
    )
    expect(
      matchingQuickStyle(
        { ...quickStyle('card', theme), style_padding_top: 8 },
        theme
      )
    ).toBeNull()
  })

  test('the picker emits the values of the style chosen', async () => {
    const wrapper = await mountSuspended(ElementQuickStyles, {
      props: { element: quickStyle('plain', theme), theme },
    })

    expect(wrapper.find('.quick-style--active').text()).toBe(
      wrapper.vm.$t('quickStyles.styles.plain.name')
    )
    await wrapper.findAll('.quick-style')[1].trigger('click')

    expect(wrapper.emitted('apply')[0][0]).toEqual(quickStyle('card', theme))
  })
})
