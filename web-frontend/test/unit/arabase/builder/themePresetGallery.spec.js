import MockAdapter from 'axios-mock-adapter'
import { flushPromises } from '@vue/test-utils'
import { mountSuspended } from '@nuxt/test-utils/runtime'

import ThemePresetGallery from '@jadawel/modules/arabase/builder/components/ThemePresetGallery.vue'
import { presetTheme } from '@jadawel/modules/arabase/builder/themePresets'

describe('ThemePresetGallery', () => {
  let mock = null

  beforeEach(() => {
    mock = new MockAdapter(useNuxtApp().$client, {
      onNoMatch: 'throwException',
    })
  })

  afterEach(() => {
    mock.restore()
  })

  const mount = (theme) =>
    mountSuspended(ThemePresetGallery, {
      props: { builder: { id: 7, theme: { ...theme } } },
    })

  test('shows every preset and marks the one the theme matches', async () => {
    const wrapper = await mount(presetTheme('heritage', 'ar'))

    const cards = wrapper.findAll('.theme-preset')
    expect(cards).toHaveLength(5)
    expect(wrapper.find('.theme-preset--active').text()).toContain(
      wrapper.vm.$t('themePresets.presets.heritage.name')
    )
  })

  test('applies a preset in one request, and undoes it', async () => {
    const theme = { primary_color: '#5190efff', body_text_alignment: 'left' }
    const requests = []
    mock.onPatch('/builder/7/theme/').reply((config) => {
      requests.push(JSON.parse(config.data))
      return [200, {}]
    })
    const wrapper = await mount(theme)
    await wrapper.setData({ language: 'en' })

    await wrapper.findAll('.theme-preset')[1].trigger('click')
    await flushPromises()

    expect(requests).toHaveLength(1)
    expect(requests[0]).toEqual(presetTheme('ocean', 'en'))
    expect(wrapper.props('builder').theme.primary_color).toBe('#0059fcff')
    expect(wrapper.emitted('applied')).toHaveLength(1)
    expect(wrapper.find('.theme-presets__applied').exists()).toBe(true)

    await wrapper.find('.theme-presets__undo').trigger('click')
    await flushPromises()

    expect(requests[1].primary_color).toBe('#5190efff')
    expect(wrapper.props('builder').theme.primary_color).toBe('#5190efff')
    expect(wrapper.find('.theme-presets__applied').exists()).toBe(false)
  })

  test('a failed request puts the old theme back', async () => {
    mock.onPatch('/builder/7/theme/').reply(500, {})
    const wrapper = await mount({ primary_color: '#123456ff' })

    await wrapper.findAll('.theme-preset')[0].trigger('click')
    await flushPromises()

    expect(wrapper.props('builder').theme.primary_color).toBe('#123456ff')
    expect(wrapper.emitted('applied')).toBeUndefined()
  })
})
