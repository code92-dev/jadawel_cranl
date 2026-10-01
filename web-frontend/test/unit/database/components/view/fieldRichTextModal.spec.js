import { flushPromises } from '@vue/test-utils'

import { TestApp } from '@jadawel/test/helpers/testApp'
import FieldRichTextModal from '@jadawel/modules/database/components/view/FieldRichTextModal'

describe('FieldRichTextModal', () => {
  let testApp

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('appends the editor menu to the body, not inside the modal', async () => {
    const wrapper = await testApp.mount(FieldRichTextModal, {
      props: {
        field: { id: 1, name: 'Notes' },
        modelValue: 'Hello',
      },
    })

    wrapper.vm.toggle()
    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve))

    // Jadawel fork: the modal mixin has no getTeleportedElement helper.
    const modal = document.querySelector('.modal__wrapper')
    const floatingMenu = document.querySelector(
      '.rich-text-editor__floating-menu'
    )

    expect(floatingMenu).not.toBeNull()
    // Body-level, not inside the positioned modal, so floating-ui positions it correctly.
    expect(document.body.contains(floatingMenu)).toBe(true)
    expect(modal.contains(floatingMenu)).toBe(false)
  })
})
