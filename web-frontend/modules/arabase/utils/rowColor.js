/**
 * The only color values row coloring accepts: names from core's
 * `background-color--*` palette, such as `blue` or `light-red`. Value
 * providers resolve anything else to `null`, and the decorator components
 * render it plain, so a stored value can never inject a class or a style.
 */
export const COLOR_PATTERN = /^[a-z-]+$/
