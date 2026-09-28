/**
 * How dashboard charts look, in the values chart.js needs.
 *
 * A canvas inherits nothing from CSS, so the palette steps the rest of the
 * interface uses (colors.scss: neutral-200 grid lines, neutral-800 ticks,
 * neutral-1200 tooltips) are repeated here, and the font is read from the page
 * so Arabic labels use the same Arabic face as the text around them.
 */

const FALLBACK_FONT = "'Inter', 'IBM Plex Sans Arabic', sans-serif"

export function chartTheme() {
  let fontFamily = FALLBACK_FONT
  if (typeof document !== 'undefined' && document.body) {
    fontFamily = getComputedStyle(document.body).fontFamily || FALLBACK_FONT
  }
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
