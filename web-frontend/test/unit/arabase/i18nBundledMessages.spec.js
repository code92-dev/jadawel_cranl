import plugin from '@jadawel/modules/arabase/i18nBundledMessages.client'

describe('arabase i18n bundled messages plugin', () => {
  const setUp = () => {
    const hooks = {}
    const nuxtApp = {
      hook: (name, fn) => {
        hooks[name] = fn
      },
    }
    plugin.setup(nuxtApp)
    return { nuxtApp, hooks }
  }

  test('runs before i18n creates its context', () => {
    expect(plugin.enforce).toBe('pre')
  })

  test('switches message loading to the bundled chunks before a load', () => {
    const { nuxtApp, hooks } = setUp()
    // i18n's own plugin creates the context after this one has run.
    nuxtApp._nuxtI18n = { dynamicResourcesSSG: false }

    hooks['i18n:beforeLocaleSwitch']({ newLocale: 'ar', initialSetup: true })

    expect(nuxtApp._nuxtI18n.dynamicResourcesSSG).toBe(true)
  })

  test('tolerates the hook firing without an i18n context', () => {
    const { hooks } = setUp()

    expect(() =>
      hooks['i18n:beforeLocaleSwitch']({ newLocale: 'ar' })
    ).not.toThrow()
  })
})
