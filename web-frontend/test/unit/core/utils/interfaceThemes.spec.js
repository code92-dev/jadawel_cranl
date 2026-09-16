import head from '@jadawel/modules/core/head'
import {
  applyInterfaceTheme,
  DEFAULT_INTERFACE_THEME,
  getInterfaceThemeBootScript,
  getInterfaceThemeSurfaces,
  getInterfaceThemeVariables,
  initializeInterfaceTheme,
  INTERFACE_THEMES,
  INTERFACE_THEME_STORAGE_KEY,
  mixWithWhite,
} from '@jadawel/modules/core/utils/interfaceThemes'

/** WCAG relative luminance, for asserting a border is actually visible. */
const luminance = (hex) => {
  const channels = [0, 2, 4].map((offset) => {
    const value =
      Number.parseInt(hex.replace('#', '').slice(offset, offset + 2), 16) / 255
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}

const contrast = (a, b) => {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}

describe('interface themes', () => {
  test('contains six complete color palettes in the requested order', () => {
    expect(INTERFACE_THEMES).toHaveLength(6)
    expect(INTERFACE_THEMES.map(({ id }) => id)).toEqual([
      'white',
      'sage',
      'gray',
      'blue',
      'rose',
      'amber',
    ])
    INTERFACE_THEMES.forEach((theme) => {
      expect(Object.keys(theme.colors)).toEqual([
        '100',
        '200',
        '300',
        '400',
        '500',
        '600',
        '700',
        '800',
        '900',
      ])
    })
  })

  test('lightens the grid colors by fifty percent', () => {
    expect(mixWithWhite('#dbeee3')).toBe('#edf7f1')
  })

  test('derives themed chrome and a fixed white table workspace', () => {
    const sage = INTERFACE_THEMES.find(({ id }) => id === 'sage')

    expect(getInterfaceThemeSurfaces(sage.colors)).toEqual({
      '--jadawel-app-background': '#f5faf7',
      '--jadawel-header-background': '#f0f7f3',
      '--jadawel-sidebar-background': '#f3f8f5',
      '--jadawel-content-background': '#fcfdfc',
      '--jadawel-raised-background': '#fbfdfb',
      '--jadawel-hover-background': '#f7fbf8',
      '--jadawel-border-color': '#cfe8d9',
      '--jadawel-grid-surface': '#ffffff',
      '--jadawel-grid-line': '#e5e7eb',
    })
  })

  test('keeps the table workspace neutral for every interface color', () => {
    INTERFACE_THEMES.forEach(({ colors }) => {
      const surfaces = getInterfaceThemeSurfaces(colors)

      expect(surfaces['--jadawel-grid-surface']).toBe('#ffffff')
      expect(surfaces['--jadawel-grid-line']).toBe('#e5e7eb')
    })
  })

  test('every theme keeps its chrome distinguishable', () => {
    // The surfaces are derived by mixing towards white, so a palette that is
    // already near-white has nowhere to travel and collapses all of them onto
    // one colour — which is what made every border, sidebar edge and grid line
    // vanish on the white theme. A theme in that position states its surfaces
    // instead, and this is the property that has to hold either way.
    INTERFACE_THEMES.forEach((theme) => {
      const surfaces = getInterfaceThemeSurfaces(theme.colors, theme.surfaces)

      expect(surfaces['--jadawel-header-background']).not.toBe(
        surfaces['--jadawel-content-background']
      )
      expect(
        contrast(surfaces['--jadawel-border-color'], '#ffffff')
      ).toBeGreaterThan(1.1)
    })
  })

  test('a theme can state its surfaces instead of deriving them', () => {
    const white = INTERFACE_THEMES.find(({ id }) => id === 'white')
    const surfaces = getInterfaceThemeSurfaces(white.colors, white.surfaces)

    expect(surfaces['--jadawel-header-background']).toBe('#f5f6f7')
    expect(surfaces['--jadawel-border-color']).toBe('#e7e9ec')
    // The overrides must not drop the neutral table canvas the derivation sets.
    expect(surfaces['--jadawel-grid-surface']).toBe('#ffffff')
    expect(surfaces['--jadawel-grid-line']).toBe('#e5e7eb')
  })

  test('defaults and falls back to the first white theme', () => {
    const root = document.createElement('div')

    expect(DEFAULT_INTERFACE_THEME).toBe('white')
    expect(INTERFACE_THEMES[0].id).toBe(DEFAULT_INTERFACE_THEME)
    expect(applyInterfaceTheme('unknown', root)).toBe('white')
    expect(root.dataset.interfaceTheme).toBe('white')
    expect(root.style.getPropertyValue('--jadawel-primary-500')).toBe('#69717d')
    expect(root.style.getPropertyValue('--jadawel-header-background')).toBe(
      '#f5f6f7'
    )
    expect(root.style.getPropertyValue('--jadawel-grid-surface')).toBe(
      '#ffffff'
    )
    expect(root.style.getPropertyValue('--jadawel-grid-line')).toBe('#e5e7eb')
  })

  test('restores a stored theme before mount and repairs an unknown id', () => {
    const root = document.createElement('div')
    const storage = {
      getItem: vi.fn(() => 'blue'),
      setItem: vi.fn(),
    }

    expect(initializeInterfaceTheme(storage, root)).toBe('blue')
    expect(root.dataset.interfaceTheme).toBe('blue')
    expect(root.style.getPropertyValue('--jadawel-primary-500')).toBe('#275d9f')
    expect(storage.setItem).not.toHaveBeenCalled()

    storage.getItem.mockReturnValue('removed-theme')
    expect(initializeInterfaceTheme(storage, root)).toBe('white')
    expect(root.dataset.interfaceTheme).toBe('white')
    expect(storage.setItem).toHaveBeenCalledWith(
      INTERFACE_THEME_STORAGE_KEY,
      'white'
    )
  })
})

describe('interface theme boot script', () => {
  /** Runs the head script against a throwaway document-like environment. */
  const boot = (stored) => {
    const root = document.createElement('div')
    const setProperty = vi.fn((name, value) =>
      root.style.setProperty(name, value)
    )
    const context = {
      document: {
        documentElement: {
          style: { setProperty },
          setAttribute: (name, value) => root.setAttribute(name, value),
        },
      },
      window: {
        localStorage: {
          getItem: () => stored,
        },
      },
    }

    new Function('document', 'window', getInterfaceThemeBootScript())(
      context.document,
      context.window
    )
    return root
  }

  test('paints the stored theme and its attribute together', () => {
    const root = boot('blue')
    const blue = INTERFACE_THEMES.find(({ id }) => id === 'blue')

    expect(root.getAttribute('data-interface-theme')).toBe('blue')
    Object.entries(getInterfaceThemeVariables(blue)).forEach(
      ([property, color]) => {
        expect(root.style.getPropertyValue(property)).toBe(color)
      }
    )
  })

  test('falls back to the default for missing and unknown selections', () => {
    expect(boot(null).getAttribute('data-interface-theme')).toBe(
      DEFAULT_INTERFACE_THEME
    )
    expect(boot('removed-theme').getAttribute('data-interface-theme')).toBe(
      DEFAULT_INTERFACE_THEME
    )
  })

  test('the head ships it inline so nothing paints before it runs', () => {
    const tag = head.script.find(({ key }) => key === 'interface-theme')

    expect(tag.tagPosition).toBe('head')
    expect(tag.innerHTML).toBe(getInterfaceThemeBootScript())
    expect(tag.src).toBeUndefined()
    expect(tag.innerHTML).not.toContain('</script')
  })

  test('the static head never declares the theme attribute', () => {
    // unhead re-applies the attributes it manages on hydration, so declaring
    // this one would reset the document to the default theme while the custom
    // properties kept the stored one.
    expect(head.htmlAttrs?.['data-interface-theme']).toBeUndefined()
  })
})
