import { Registerable } from '@jadawel/modules/core/registry'

/**
 * The canonical responsive boundary model for the Application Builder.
 *
 * These numbers are the single source of truth for device classification.
 * The SCSS media queries consume the same values through the
 * `$device-*-width` variables in `modules/core/assets/scss/variables.scss`,
 * so JavaScript state and CSS rendering always resolve to the same device
 * at every viewport width:
 *
 * - smartphone: width <= 500px
 * - tablet:     501px <= width <= 768px
 * - desktop:    width >= 769px
 */
export const SMARTPHONE_MAX_WIDTH = 500
export const TABLET_MAX_WIDTH = 768

export class DeviceType extends Registerable {
  get iconClass() {
    return null
  }

  getOrder() {
    return null
  }

  get minWidth() {
    return 0
  }

  get maxWidth() {
    return 0
  }
}

export class DesktopDeviceType extends DeviceType {
  static getType() {
    return 'desktop'
  }

  static get tabletMaxWidth() {
    return TABLET_MAX_WIDTH
  }

  get iconClass() {
    return 'iconoir-apple-imac-2021'
  }

  getOrder() {
    return 1
  }

  get minWidth() {
    return TABLET_MAX_WIDTH + 1
  }

  get maxWidth() {
    return null // Can be as wide as you want
  }
}

export class TabletDeviceType extends DeviceType {
  static getType() {
    return 'tablet'
  }

  static get tabletMaxWidth() {
    return TABLET_MAX_WIDTH
  }

  get iconClass() {
    return 'jadawel-icon-tablet'
  }

  getOrder() {
    return 2
  }

  get minWidth() {
    return SMARTPHONE_MAX_WIDTH + 1
  }

  get maxWidth() {
    return TABLET_MAX_WIDTH
  }
}

export class SmartphoneDeviceType extends DeviceType {
  static getType() {
    return 'smartphone'
  }

  static get smartphoneMaxWidth() {
    return SMARTPHONE_MAX_WIDTH
  }

  get iconClass() {
    return 'jadawel-icon-smartphone'
  }

  getOrder() {
    return 3
  }

  get minWidth() {
    return 0
  }

  get maxWidth() {
    return SMARTPHONE_MAX_WIDTH
  }
}
