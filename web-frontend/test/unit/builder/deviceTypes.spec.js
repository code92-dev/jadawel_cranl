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
  DesktopDeviceType,
  TabletDeviceType,
  SmartphoneDeviceType,
} from '@jadawel/modules/builder/deviceTypes'
import deviceBreakpoints from '@jadawel/modules/builder/deviceBreakpoints.json'

describe('builder breakpoint contract', () => {
  // The canonical contract: one JSON, consumed by JS and (via the generated
  // partial) by SCSS.
  const SMARTPHONE_MAX = deviceBreakpoints.smartphoneMaxWidth
  const TABLET_MAX = deviceBreakpoints.tabletMaxWidth

  test('device intervals are non-overlapping and gapless', () => {
    const desktop = new DesktopDeviceType()
    const tablet = new TabletDeviceType()
    const smartphone = new SmartphoneDeviceType()

    // The classification path (PageContent.closestDeviceType) walks the
    // devices from widest to narrowest against maxWidth, so the contract is:
    // desktop unlimited, tablet capped at the tablet boundary, smartphone
    // capped at the smartphone boundary, in that order.
    expect(desktop.maxWidth).toBeNull()
    expect(tablet.maxWidth).toBe(TABLET_MAX)
    expect(smartphone.maxWidth).toBe(SMARTPHONE_MAX)
    expect(SMARTPHONE_MAX).toBeLessThan(TABLET_MAX)
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
      // Mirror PageContent.closestDeviceType: devices sorted by order and
      // reversed, so the narrowest device whose maxWidth covers the width
      // wins.
      const device = [
        new SmartphoneDeviceType(),
        new TabletDeviceType(),
        new DesktopDeviceType(),
      ].find((d) => d.maxWidth === null || width <= d.maxWidth)

      expect(device.getType()).toBe(expected)
    }
  )

  test('the compiled element SCSS consumes the same boundaries', () => {
    // The stylesheet must not hardcode 500/768; it derives the media queries
    // from the generated partial, which is built from the same JSON.
    const columnScss = readFileSync(
      resolve(
        __dirname,
        '../../../modules/core/assets/scss/components/builder/elements/column_element.scss'
      ),
      'utf8'
    )

    expect(columnScss).toMatch(/\$device-smartphone-max-width/)
    expect(columnScss).toMatch(/\$device-tablet-max-width/)
    expect(columnScss).not.toMatch(/max-width:\s*500px/)
    expect(columnScss).not.toMatch(/min-width:\s*501px/)
  })

  test('the generated Sass partial matches the canonical JSON', () => {
    const generated = readFileSync(
      resolve(
        __dirname,
        '../../../modules/core/assets/scss/_generated-device-breakpoints.scss'
      ),
      'utf8'
    )

    expect(generated).toContain(
      `$device-smartphone-max-width: ${SMARTPHONE_MAX};`
    )
    expect(generated).toContain(`$device-tablet-max-width: ${TABLET_MAX};`)
  })
})
