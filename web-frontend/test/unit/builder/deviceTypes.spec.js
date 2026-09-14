/**
 * Phase 0 regression tests for the remediation plan
 * (docs/NEW_FEATURES_REMEDIATION_PLAN.md, Phase 3 "One breakpoint contract").
 *
 * The JavaScript device model (modules/builder/deviceTypes.js) and the
 * builder element SCSS (modules/core/assets/scss/components/builder/elements/)
 * currently disagree at the tablet/smartphone boundary: JS treats widths
 * 421-768 as tablet and <=420 as smartphone, while the CSS switches to the
 * stacked/compact smartphone layout at <=500 and tablet at 501-768. Between
 * 421 and 500 the runtime picks "tablet" while the stylesheet renders the
 * smartphone layout.
 *
 * These tests pin the FUTURE single contract and currently fail (RED):
 *  - the contract is exported from one module that both JS and SCSS consume
 *  - at every documented boundary pixel the JS device and the CSS interval
 *    agree, and the intervals never overlap or leave gaps.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import {
  DeviceType,
  DesktopDeviceType,
  TabletDeviceType,
  SmartphoneDeviceType,
} from '@jadawel/modules/builder/deviceTypes'

describe('builder breakpoint contract', () => {
  // The canonical contract: exported once, consumed everywhere.
  const SMARTPHONE_MAX = 500
  const TABLET_MAX = 768

  test('exports the canonical boundaries from the deviceTypes module', () => {
    expect(typeof SmartphoneDeviceType.smartphoneMaxWidth).toBe('number')
    expect(typeof TabletDeviceType.tabletMaxWidth).toBe('number')
    expect(SmartphoneDeviceType.smartphoneMaxWidth).toBe(SMARTPHONE_MAX)
    expect(TabletDeviceType.tabletMaxWidth).toBe(TABLET_MAX)
  })

  test('device intervals are non-overlapping and gapless', () => {
    const desktop = new DesktopDeviceType()
    const tablet = new TabletDeviceType()
    const smartphone = new SmartphoneDeviceType()

    // Desktop starts right above tablet's ceiling.
    expect(desktop.minWidth).toBe(TABLET_MAX + 1)
    // Tablet covers (smartphone ceiling, tablet ceiling].
    expect(tablet.minWidth).toBe(SMARTPHONE_MAX + 1)
    expect(tablet.maxWidth).toBe(TABLET_MAX)
    // Smartphone covers everything up to its ceiling.
    expect(smartphone.minWidth).toBe(0)
    expect(smartphone.maxWidth).toBe(SMARTPHONE_MAX)
  })

  test.each([419, 420, 421, 499, 500, 501, 767, 768, 769])(
    'device resolution agrees with the CSS intervals at %ipx',
    (width) => {
      const expected =
        width <= SMARTPHONE_MAX
          ? 'smartphone'
          : width <= TABLET_MAX
            ? 'tablet'
            : 'desktop'
      const device =
        width <= SmartphoneDeviceType.smartphoneMaxWidth
          ? new SmartphoneDeviceType()
          : width <= TabletDeviceType.tabletMaxWidth
            ? new TabletDeviceType()
            : new DesktopDeviceType()

      expect(device.getType()).toBe(expected)
    }
  )

  test('the compiled element SCSS consumes the same boundaries', () => {
    // The stylesheet must no longer hardcode 500/768; it must derive the
    // media queries from the exported contract (via SCSS variables injected
    // from the same source of truth). Until the unification lands the raw
    // files still contain hardcoded pixels, so assert against the contract
    // the fix will produce: the SCSS sources reference the shared variables
    // instead of raw numbers at the tablet/smartphone edges.
    const columnScss = readFileSync(
      resolve(
        __dirname,
        '../../../modules/core/assets/scss/components/builder/elements/column_element.scss'
      ),
      'utf8'
    )

    // Current code hardcodes the boundaries; the contract requires the SCSS
    // to consume shared variables named after the device types.
    expect(columnScss).toMatch(/\$device-smartphone-max-width/)
    expect(columnScss).toMatch(/\$device-tablet-max-width/)
    expect(columnScss).not.toMatch(/max-width:\s*500px/)
    expect(columnScss).not.toMatch(/min-width:\s*501px/)
  })
})
