import DatabaseAppLayoutPreview from '@jadawel/modules/database/components/onboarding/DatabaseAppLayoutPreview'
import { DatabaseOnboardingType } from '@jadawel/modules/database/onboardingTypes'
import { TestApp } from '@jadawel/test/helpers/testApp'

vi.stubGlobal(
  'ResizeObserver',
  class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
)

// The database onboarding step highlights an element in the preview's fake
// sidebar via `data-highlight`. The sidebar was flattened (see PATCHES.md,
// "Sidebar simplification"), so the highlight target must be one the flat
// sidebar still renders — otherwise Highlight.update() gets an empty element
// list and the preview crashes.
describe('DatabaseAppLayoutPreview', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test("highlights an element the preview's sidebar actually renders", async () => {
    const { highlightDataName } = new DatabaseOnboardingType(
      testApp.getApp()
    ).getAdditionalPreviewProps()

    const wrapper = await testApp.mount(DatabaseAppLayoutPreview, {
      props: { data: {}, highlightDataName },
    })

    expect(
      wrapper.find(`[data-highlight='${highlightDataName}']`).exists()
    ).toBe(true)
  })
})
