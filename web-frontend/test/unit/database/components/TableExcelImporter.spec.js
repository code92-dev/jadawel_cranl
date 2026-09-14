/**
 * Phase 0 regression test for the remediation plan
 * (docs/NEW_FEATURES_REMEDIATION_PLAN.md, Phase 1 "Spreadsheet import size
 * limit").
 *
 * TableExcelImporter.vue used to read `config.public.baserowMaxImportFileSizeMb`,
 * while the canonical runtime-config key is `jadawelMaxImportFileSizeMb`
 * (modules/core/module.js:64, env-remap.mjs:45). `parseInt(undefined, 10)`
 * is NaN, so `file.size > NaN` is always false and the configured upload
 * limit was silently disabled for Excel/ODS imports.
 *
 * These tests pin the fixed behavior: the component enforces the configured
 * limit through the shared `utils/importFile.js` helper, and a missing or
 * unusable runtime value falls back to the documented 512 MB default instead
 * of disabling validation.
 *
 * Component state contract (mixins/importer.js + mixins/form.js):
 * `error` is a message string (empty when no error) and `values.filename`
 * holds the chosen file name. The runtime config is the live Nuxt object, so
 * each test mutates `testApp.getApp().$config.public` before mounting.
 */
import { TestApp } from '@jadawel/test/helpers/testApp'
import TableExcelImporter from '@jadawel/modules/database/components/table/TableExcelImporter.vue'
import { DEFAULT_MAX_IMPORT_FILE_SIZE_MB } from '@jadawel/modules/database/utils/importFile'

describe('TableExcelImporter upload limit', () => {
  let testApp = null
  let publicConfig = null

  beforeEach(() => {
    testApp = new TestApp()
    publicConfig = testApp.getApp().$config.public
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mountImporter = (limitMb) => {
    publicConfig.jadawelMaxImportFileSizeMb = limitMb
    return testApp.mount(TableExcelImporter, {
      props: { importData: null, application: null },
    })
  }

  const fileOfSize = (bytes) => new File([new ArrayBuffer(bytes)], 'test.xlsx')

  test('rejects a file above the configured limit', async () => {
    const wrapper = await mountImporter(1) // 1 MB limit

    // Bypass the native input's file filtering by calling select() directly.
    const oversized = fileOfSize(2 * 1024 * 1024)
    await wrapper.vm.select({ target: { files: [oversized] } })

    // resetImporterState() replaces the whole `values` object, so the
    // filename key is gone entirely after a rejected file.
    expect(wrapper.vm.values.filename).toBeFalsy()
    expect(wrapper.vm.error).not.toBe('')
  })

  test('accepts a file below the configured limit', async () => {
    const wrapper = await mountImporter(1)

    const small = fileOfSize(1024)
    await wrapper.vm.select({ target: { files: [small] } })

    expect(wrapper.vm.error).toBe('')
  })

  test('a missing runtime value falls back to the documented default, not NaN', async () => {
    const wrapper = await mountImporter(undefined)

    // The documented default is 512 MB, so a 600 MB file must be rejected
    // instead of silently passing the NaN comparison.
    const oversized = fileOfSize(
      (DEFAULT_MAX_IMPORT_FILE_SIZE_MB + 88) * 1024 * 1024
    )
    await wrapper.vm.select({ target: { files: [oversized] } })

    expect(wrapper.vm.values.filename).toBeFalsy()
    expect(wrapper.vm.error).not.toBe('')
  })

  test('a zero runtime value falls back to the documented default', async () => {
    const wrapper = await mountImporter(0)

    const oversized = fileOfSize(
      (DEFAULT_MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
    )
    await wrapper.vm.select({ target: { files: [oversized] } })

    expect(wrapper.vm.values.filename).toBeFalsy()
    expect(wrapper.vm.error).not.toBe('')
  })
})
