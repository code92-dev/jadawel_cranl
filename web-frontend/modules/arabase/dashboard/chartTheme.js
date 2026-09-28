/**
 * How dashboard charts look, in the values chart.js needs.
 *
 * A canvas inherits nothing from CSS, so the palette steps the rest of the
 * interface uses (colors.scss: neutral-200 grid lines, neutral-800 ticks,
 * neutral-1200 tooltips) are repeated here, and the font is read from the page
 * so Arabic labels use the same Arabic face as the text around them.
 */

const FALLBACK_FONT =
  "'Inter', 'IBM Plex Sans Arabic', 'Saudi Riyal Sign', sans-serif"

/**
 * The dashboard's font stack, which ends in the Saudi riyal sign's own font
 * (`saudi_riyal.scss`) so tooltips and legends drawn on the canvas show it.
 */
function dashboardFont() {
  if (typeof document === 'undefined') {
    return FALLBACK_FONT
  }
  const root =
    document.querySelector('.dashboard-app, .public-dashboard') || document.body
  const family = root ? getComputedStyle(root).fontFamily : ''
  if (!family) {
    return FALLBACK_FONT
  }
  return family.includes('Saudi Riyal Sign')
    ? family
    : family.replace(/,?\s*sans-serif\s*$/, '') +
        ", 'Saudi Riyal Sign', sans-serif"
}

export function chartTheme() {
  const fontFamily = dashboardFont()
  return {
    fontFamily,
    gridColor: '#eaefe7',
    tickColor: '#7e8a7c',
    labelColor: '#4d564b',
    tooltipBackground: '#1e241d',
    tooltipText: '#eaefe7',
    lineColor: '#ffffff',
  }
}
