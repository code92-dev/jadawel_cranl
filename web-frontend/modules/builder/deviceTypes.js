import { Registerable } from '@jadawel/modules/core/registry'
import deviceBreakpoints from '@jadawel/modules/builder/deviceBreakpoints.json'

/**
 * The canonical responsive boundary model for the Application Builder.
 *
 * The numbers come from `modules/builder/deviceBreakpoints.json` — the one
 * source of truth for device classification. The generated Sass partial
 * (`_generated-device-breakpoints.scss`, built from the same JSON by
 * `yarn generate:device-breakpoints`) feeds the `$device-*` variables in
 * `modules/core/assets/scss/variables.scss`, so JavaScript state and CSS
 * rendering always resolve to the same device at every viewport width:
 *
 * - smartphone: width <= smartphoneMaxWidth (500)
 * - tablet:     smartphoneMaxWidth < width <= tabletMaxWidth (768)
 * - desktop:    width > tabletMaxWidth
 */
export const SMARTPHONE_MAX_WIDTH = deviceBreakpoints.smartphoneMaxWidth
export const TABLET_MAX_WIDTH = deviceBreakpoints.tabletMaxWidth
export class DeviceType extends Registerable {
  get iconClass() {
    return null
  }

  getOrder() {
    return null
  }

  /**
   * The inclusive upper viewport bound this device applies to, or null for
   * "unlimited" (desktop). `PageContent.closestDeviceType` classifies the
   * viewport against these bounds; the numbers derive from the canonical
   * JSON above.
   */
  get maxWidth() {
    return 0
  }
}

export class DesktopDeviceType extends DeviceType {
  static getType() {
    return 'desktop'
  }

  get iconClass() {
    return 'iconoir-apple-imac-2021'
  }

  getOrder() {
    return 1
  }

  get maxWidth() {
    return null // Can be as wide as you want
  }
}

export class TabletDeviceType extends DeviceType {
  static getType() {
    return 'tablet'
  }

  get iconClass() {
    return 'jadawel-icon-tablet'
  }

  getOrder() {
    return 2
  }

  get maxWidth() {
    return TABLET_MAX_WIDTH
  }
}

export class SmartphoneDeviceType extends DeviceType {
  static getType() {
    return 'smartphone'
  }

  get iconClass() {
    return 'jadawel-icon-smartphone'
  }

  getOrder() {
    return 3
  }

  get maxWidth() {
    return SMARTPHONE_MAX_WIDTH
  }
}
