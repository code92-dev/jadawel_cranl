export const INTERFACE_THEME_STORAGE_KEY = 'jadawel.interfaceTheme'
export const DEFAULT_INTERFACE_THEME = 'white'

export const INTERFACE_THEMES = [
  {
    id: 'white',
    swatch: '#ffffff',
    swatchOutline: '#aeb4bc',
    checkColor: '#434a53',
    colors: {
      100: '#ffffff',
      200: '#f5f6f7',
      300: '#e7e9ec',
      400: '#c4c8ce',
      500: '#69717d',
      600: '#565e68',
      700: '#434a53',
      800: '#30363d',
      900: '#1d2228',
    },
    // The derived surfaces mix *towards* white, which for a palette whose 100
    // step already is white collapses every one of them to #ffffff and leaves
    // the border at #f7f7f8 — a contrast ratio of 1.04, so every sidebar,
    // header, card and grid line disappears. A palette this light has to state
    // its surfaces rather than derive them, stepping down its own neutrals.
    surfaces: {
      '--jadawel-app-background': '#f5f6f7',
      '--jadawel-header-background': '#f5f6f7',
      '--jadawel-sidebar-background': '#fafbfc',
      '--jadawel-content-background': '#ffffff',
      '--jadawel-raised-background': '#ffffff',
      '--jadawel-hover-background': '#f0f2f4',
      '--jadawel-border-color': '#e7e9ec',
    },
  },
  {
    id: 'sage',
    colors: {
      100: '#f0f7f3',
      200: '#dbeee3',
      300: '#b5dcc5',
      400: '#55a97d',
      500: '#278053',
      600: '#1b5a3a',
      700: '#15472e',
      800: '#103522',
      900: '#06170e',
    },
  },
  {
    id: 'gray',
    colors: {
      100: '#f3f4f5',
      200: '#e1e3e6',
      300: '#c2c6cb',
      400: '#8f969f',
      500: '#5f6670',
      600: '#4d535c',
      700: '#3c4148',
      800: '#2b2f35',
      900: '#1b1e22',
    },
  },
  {
    id: 'blue',
    colors: {
      100: '#f0f4fc',
      200: '#dae4fd',
      300: '#acc8f8',
      400: '#5190ef',
      500: '#275d9f',
      600: '#1d508b',
      700: '#124377',
      800: '#0d355e',
      900: '#05223f',
    },
  },
  {
    id: 'rose',
    colors: {
      100: '#fdf3f9',
      200: '#f9e1ef',
      300: '#f3c3df',
      400: '#e26ab0',
      500: '#88406a',
      600: '#713558',
      700: '#5a2a46',
      800: '#421d33',
      900: '#2a1020',
    },
  },
  {
    id: 'amber',
    colors: {
      100: '#fffbf0',
      200: '#fff4da',
      300: '#ffe9b4',
      400: '#ffc744',
      500: '#806422',
      600: '#66501b',
      700: '#513e14',
      800: '#3c2d0e',
      900: '#271c08',
    },
  },
]

export const mixWithWhite = (hexColor, amount = 0.5) => {
  const value = hexColor.replace('#', '')
  const channels = [0, 2, 4].map((offset) =>
    Number.parseInt(value.slice(offset, offset + 2), 16)
  )
  const mixed = channels.map((channel) =>
    Math.round(channel + (255 - channel) * amount)
      .toString(16)
      .padStart(2, '0')
  )
  return `#${mixed.join('')}`
}

/**
 * The surface colours a palette resolves to.
 *
 * `overrides` lets a theme state a surface outright instead of deriving it.
 * Deriving works by mixing towards white, which needs the palette to have
 * somewhere to travel — a near-white 100 step has none, and every surface
 * collapses onto the same colour.
 */
export const getInterfaceThemeSurfaces = (colors, overrides = {}) => ({
  '--jadawel-app-background': mixWithWhite(colors[100], 0.35),
  '--jadawel-header-background': colors[100],
  '--jadawel-sidebar-background': mixWithWhite(colors[100], 0.18),
  '--jadawel-content-background': mixWithWhite(colors[100], 0.78),
  '--jadawel-raised-background': mixWithWhite(colors[100], 0.7),
  '--jadawel-hover-background': mixWithWhite(colors[100], 0.45),
  // From the 300 step, not the 200. The 200 step is near-white on the lighter
  // palettes, so mixing it further left amber at 1.076 contrast and white at
  // 1.071 — borders nobody can see. The 300 step is the first genuinely tinted
  // one, and mixing it back keeps the line subtle without erasing it.
  '--jadawel-border-color': mixWithWhite(colors[300], 0.35),
  // Keep the data canvas neutral so theme colors frame the table instead of
  // tinting the workspace where users read and edit values.
  '--jadawel-grid-surface': '#ffffff',
  '--jadawel-grid-line': '#e5e7eb',
  ...overrides,
})

/**
 * Every custom property a theme sets, as one flat map. Both the runtime
 * `applyInterfaceTheme` and the pre-paint boot script read this, so the two
 * cannot drift apart and repaint the document differently.
 */
export const getInterfaceThemeVariables = (theme) => ({
  ...Object.fromEntries(
    Object.entries(theme.colors).map(([step, color]) => [
      `--jadawel-primary-${step}`,
      color,
    ])
  ),
  ...getInterfaceThemeSurfaces(theme.colors, theme.surfaces),
})

export const INTERFACE_THEME_VARIABLES = Object.fromEntries(
  INTERFACE_THEMES.map((theme) => [theme.id, getInterfaceThemeVariables(theme)])
)

export const applyInterfaceTheme = (
  themeId,
  root = globalThis.document?.documentElement
) => {
  const theme =
    INTERFACE_THEMES.find(({ id }) => id === themeId) || INTERFACE_THEMES[0]

  if (!root) {
    return theme.id
  }

  Object.entries(getInterfaceThemeVariables(theme)).forEach(
    ([property, color]) => root.style.setProperty(property, color)
  )
  root.dataset.interfaceTheme = theme.id

  return theme.id
}

/**
 * The theme has to be on the document before the first paint, and it has to be
 * the *stored* one. SSR cannot read localStorage, so a server-rendered default
 * plus a client plugin means one painted frame in the wrong colours — the green
 * flash on every refresh. This returns a tiny synchronous script for the head:
 * it runs before the body is parsed, so the first frame is already themed.
 *
 * It is also the only thing that sets `data-interface-theme`. Declaring that
 * attribute in the static head instead would hand it to unhead, which re-applies
 * its own value on hydration and would reset the attribute to the default while
 * the custom properties stayed on the stored theme — chrome styled for one theme
 * painted in the colours of another, until the user re-picked from the menu.
 */
export const getInterfaceThemeBootScript = () =>
  `(function(){var v=${JSON.stringify(INTERFACE_THEME_VARIABLES)};` +
  `var d=${JSON.stringify(DEFAULT_INTERFACE_THEME)},t=d;` +
  `try{var s=window.localStorage.getItem(${JSON.stringify(
    INTERFACE_THEME_STORAGE_KEY
  )});if(s&&v[s]){t=s}}catch(e){}` +
  `var r=document.documentElement,p=v[t]||v[d];` +
  `for(var n in p){r.style.setProperty(n,p[n])}` +
  `r.setAttribute('data-interface-theme',t)})()`

/**
 * Re-applies the stored theme once the application boots, and repairs storage
 * that names a theme which no longer exists. The head script has normally
 * painted the same theme already; this keeps the picker, storage and document
 * agreeing even when that script could not run.
 */
export const initializeInterfaceTheme = (
  storage = globalThis.localStorage,
  root = globalThis.document?.documentElement
) => {
  const stored = storage?.getItem(INTERFACE_THEME_STORAGE_KEY)
  const activeTheme = applyInterfaceTheme(stored, root)

  // Replace removed or unknown theme ids with the resolved default so the
  // picker, storage and document cannot disagree on subsequent page loads.
  if (storage && stored !== activeTheme) {
    storage.setItem(INTERFACE_THEME_STORAGE_KEY, activeTheme)
  }

  return activeTheme
}
