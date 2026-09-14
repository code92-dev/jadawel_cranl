#!/usr/bin/env node
/**
 * Generates the Sass partial that exposes the Builder device breakpoints to
 * the stylesheets, from the one canonical source:
 *
 *   modules/builder/deviceBreakpoints.json  (canonical data)
 *   modules/core/assets/scss/_generated-device-breakpoints.scss  (generated)
 *
 * JavaScript imports the canonical JSON directly (deviceTypes.js); Sass
 * imports only this generated partial (variables.scss). Never edit the
 * generated file by hand — change the JSON and run:
 *
 *   yarn generate:device-breakpoints
 *
 * CI runs `yarn generate:device-breakpoints --check`, which fails when the
 * committed partial has drifted from the JSON.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const jsonPath = fileURLToPath(
  new URL('../modules/builder/deviceBreakpoints.json', import.meta.url)
)
const scssPath = fileURLToPath(
  new URL(
    '../modules/core/assets/scss/_generated-device-breakpoints.scss',
    import.meta.url
  )
)

const breakpoints = JSON.parse(readFileSync(jsonPath, 'utf8'))
for (const key of ['smartphoneMaxWidth', 'tabletMaxWidth']) {
  const value = breakpoints[key]
  if (!Number.isInteger(value) || value <= 0) {
    console.error(
      `deviceBreakpoints.json: "${key}" must be a positive integer.`
    )
    process.exit(1)
  }
}
if (breakpoints.smartphoneMaxWidth >= breakpoints.tabletMaxWidth) {
  console.error(
    'deviceBreakpoints.json: "smartphoneMaxWidth" must be smaller than "tabletMaxWidth".'
  )
  process.exit(1)
}

const dollar = '$'
const content = `// GENERATED FILE — do not edit by hand.
// Source of truth: web-frontend/modules/builder/deviceBreakpoints.json
// Regenerate with: yarn generate:device-breakpoints (CI runs --check).
// Consume through the $device-* variables re-exported by variables.scss.
${dollar}device-smartphone-max-width: ${breakpoints.smartphoneMaxWidth};
${dollar}device-tablet-max-width: ${breakpoints.tabletMaxWidth};
`
if (process.argv.includes('--check')) {
  const existing = readFileSync(scssPath, 'utf8')
  if (existing !== content) {
    console.error(
      '_generated-device-breakpoints.scss has drifted from deviceBreakpoints.json.\n' +
        'Run `yarn generate:device-breakpoints` and commit the result.'
    )
    process.exit(1)
  }
  console.log('Generated device breakpoints are up to date.')
} else {
  writeFileSync(scssPath, content)
  console.log(`Wrote ${scssPath}`)
}
