import { describe, expect, test } from 'vitest'
import {
  DEFAULT_MAX_IMPORT_FILE_SIZE_MB,
  fileExceedsImportSizeLimit,
  getMaxImportFileSizeMb,
} from '@jadawel/modules/database/utils/importFile'

/**
 * Direct tests for the shared upload-limit helper. The component tests in
 * `TableExcelImporter.spec.js` prove the wiring; these pin the parsing
 * contract itself: any value that is not exactly a positive integer must
 * fall back to the documented default, and prefix-parsing traps
 * ("999999abc" parseInt-parses to 999999) must not weaken the limit.
 */
describe('getMaxImportFileSizeMb', () => {
  test.each([
    { label: 'missing config', config: undefined },
    { label: 'missing key', config: {} },
    { label: 'zero', config: { jadawelMaxImportFileSizeMb: 0 } },
    { label: 'negative', config: { jadawelMaxImportFileSizeMb: -5 } },
    { label: 'NaN string', config: { jadawelMaxImportFileSizeMb: 'NaN' } },
    { label: 'non-numeric', config: { jadawelMaxImportFileSizeMb: '1abc' } },
    {
      label: 'numeric prefix (parseInt trap)',
      config: { jadawelMaxImportFileSizeMb: '999999abc' },
    },
    { label: 'float', config: { jadawelMaxImportFileSizeMb: 1.5 } },
    { label: 'empty string', config: { jadawelMaxImportFileSizeMb: '' } },
  ])('$label falls back to the documented default', ({ config }) => {
    expect(getMaxImportFileSizeMb(config)).toBe(DEFAULT_MAX_IMPORT_FILE_SIZE_MB)
  })

  test.each([
    { label: 'integer', value: 256 },
    { label: 'integer string', value: '256' },
  ])('$label is honored', ({ value }) => {
    expect(getMaxImportFileSizeMb({ jadawelMaxImportFileSizeMb: value })).toBe(
      256
    )
  })
})

describe('fileExceedsImportSizeLimit', () => {
  const fileOfSize = (bytes) => ({ size: bytes })

  test('a file exactly at the limit does not exceed it', () => {
    expect(
      fileExceedsImportSizeLimit(fileOfSize(2 * 1024 * 1024), {
        jadawelMaxImportFileSizeMb: 2,
      })
    ).toBe(false)
  })

  test('a file one byte over the limit exceeds it', () => {
    expect(
      fileExceedsImportSizeLimit(fileOfSize(2 * 1024 * 1024 + 1), {
        jadawelMaxImportFileSizeMb: 2,
      })
    ).toBe(true)
  })

  test('a malformed numeric-prefix config cannot disable validation', () => {
    // "999999abc" must not become a 999999 MB limit: the fallback applies,
    // so a file over the documented default is rejected.
    expect(
      fileExceedsImportSizeLimit(
        fileOfSize((DEFAULT_MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024),
        { jadawelMaxImportFileSizeMb: '999999abc' }
      )
    ).toBe(true)
  })
})
