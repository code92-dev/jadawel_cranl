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
import databaseEnRaw from '@jadawel/modules/database/locales/en.json?raw'
import databaseArRaw from '@jadawel/modules/database/locales/ar.json?raw'

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

  test('a negative runtime value falls back to the documented default', async () => {
    const wrapper = await mountImporter(-5)

    const oversized = fileOfSize(
      (DEFAULT_MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
    )
    await wrapper.vm.select({ target: { files: [oversized] } })

    expect(wrapper.vm.values.filename).toBeFalsy()
    expect(wrapper.vm.error).not.toBe('')
  })

  test('a non-numeric runtime value falls back to the documented default', async () => {
    const wrapper = await mountImporter('1abc')

    const oversized = fileOfSize(
      (DEFAULT_MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
    )
    await wrapper.vm.select({ target: { files: [oversized] } })

    expect(wrapper.vm.values.filename).toBeFalsy()
    expect(wrapper.vm.error).not.toBe('')
  })

  test('a NaN runtime value falls back to the documented default', async () => {
    const wrapper = await mountImporter('NaN')

    const oversized = fileOfSize(
      (DEFAULT_MAX_IMPORT_FILE_SIZE_MB + 1) * 1024 * 1024
    )
    await wrapper.vm.select({ target: { files: [oversized] } })

    expect(wrapper.vm.values.filename).toBeFalsy()
    expect(wrapper.vm.error).not.toBe('')
  })

  test('accepts a file exactly at the configured limit', async () => {
    const wrapper = await mountImporter(1)

    const exact = fileOfSize(1024 * 1024)
    await wrapper.vm.select({ target: { files: [exact] } })

    expect(wrapper.vm.error).toBe('')
  })

  test('rejects a file one byte over the configured limit', async () => {
    const wrapper = await mountImporter(1)

    const oneByteOver = fileOfSize(1024 * 1024 + 1)
    await wrapper.vm.select({ target: { files: [oneByteOver] } })

    expect(wrapper.vm.values.filename).toBeFalsy()
    expect(wrapper.vm.error).not.toBe('')
  })

  test.each([
    { locale: 'en', name: 'English' },
    { locale: 'ar', name: 'Arabic' },
  ])(
    'the rejection message interpolates the limit in $name',
    async ({ locale }) => {
      // Both catalogues must carry the key with the {limit} placeholder so
      // the interpolated limit reaches the user in each language.
      const messages = JSON.parse(
        locale === 'en' ? databaseEnRaw : databaseArRaw
      )
      expect(messages.tableExcelImporter.limitFileSize).toContain('{limit}')
      // The component must reject through the localized key, passing the
      // resolved configured limit as the interpolation parameter.
      const tCalls = []
      const wrapper = await testApp.mount(TableExcelImporter, {
        props: { importData: null, application: null },
        global: {
          mocks: {
            $t: (key, params) => {
              tCalls.push({ key, params })
              return key
            },
          },
        },
      })
      publicConfig.jadawelMaxImportFileSizeMb = 1
      const oversized = fileOfSize(2 * 1024 * 1024)
      await wrapper.vm.select({ target: { files: [oversized] } })

      const call = tCalls.find(
        ({ key }) => key === 'tableExcelImporter.limitFileSize'
      )
      expect(call).toBeTruthy()
      expect(call.params).toEqual({ limit: 1 })
    }
  )
})
