/**
 * Phase 0 regression test for the remediation plan
 * (docs/NEW_FEATURES_REMEDIATION_PLAN.md, Phase 1 "Spreadsheet import size
 * limit").
 *
 * TableExcelImporter.vue reads `config.public.baserowMaxImportFileSizeMb`,
 * but the canonical runtime-config key is `jadawelMaxImportFileSizeMb`
 * (modules/core/module.js:64, env-remap.mjs:45). `parseInt(undefined, 10)`
 * is NaN, so `file.size > NaN` is always false and the configured upload
 * limit is silently disabled for Excel/ODS imports.
 *
 * Today (RED) an oversized file falls through to the loading path:
 * `values.filename` becomes the file name and the reader starts, because the
 * `file.size > NaN` guard never fires. After the fix these tests must pass:
 * an oversized file is rejected, `values.filename` is cleared and the
 * translated limit message is raised.
 *
 * Component state contract (mixins/importer.js + mixins/form.js):
 * `error` is a message string (empty when no error) and `values.filename`
 * holds the chosen file name.
 */
import { TestApp } from '@jadawel/test/helpers/testApp'
import TableExcelImporter from '@jadawel/modules/database/components/table/TableExcelImporter.vue'

// The component resolves its runtime config through `useRuntimeConfig()`
// from '#imports' in setup(), so the limit is controlled by mocking that
// import instead of relying on the real Nuxt runtime configuration.
let mockPublicConfig = {}
vi.mock('#imports', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useRuntimeConfig: () => ({ public: { ...mockPublicConfig } }),
  }
})

describe('TableExcelImporter upload limit', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.store
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mountImporter = (limitMb) => {
    mockPublicConfig = { jadawelMaxImportFileSizeMb: limitMb }
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

    // Post-fix contract: the file is rejected, the filename is cleared and
    // the translated limit error is shown. Fails today because the broken
    // guard accepts the file and starts loading it instead.
    expect(wrapper.vm.values.filename).toBe('')
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

    const oversized = fileOfSize(600 * 1024 * 1024)
    await wrapper.vm.select({ target: { files: [oversized] } })

    // The default documented in module.js is 512 MB, so a 600 MB file must
    // be rejected instead of silently passing the NaN comparison.
    expect(wrapper.vm.values.filename).toBe('')
    expect(wrapper.vm.error).not.toBe('')
  })
})
