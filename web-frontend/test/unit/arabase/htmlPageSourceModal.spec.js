import { mountSuspended } from '@nuxt/test-utils/runtime'
import { nextTick } from 'vue'

import HtmlPageSourceModal from '@jadawel/modules/arabase/views/components/HtmlPageSourceModal'

/**
 * Characterizes the source modal: how the textarea is seeded from the view,
 * when Save is available, what a save emits, and what read-only hides. Pinned
 * before the HTML page components are restructured.
 */
describe('HtmlPageSourceModal', () => {
  const mountModal = async ({ view, readOnly = false } = {}) => {
    const wrapper = await mountSuspended(HtmlPageSourceModal, {
      props: { view, readOnly },
      attachTo: document.body,
      global: {
        mocks: {
          $t: (key, params) =>
            params ? `${key}:${JSON.stringify(params)}` : key,
        },
      },
    })
    await wrapper.vm.show()
    await nextTick()
    return wrapper
  }

  const textarea = (wrapper) => wrapper.get('textarea')
  const saveButton = (wrapper) =>
    wrapper.find('.html-page-source__footer button')

  let wrapper = null

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
      wrapper = null
    }
  })

  test('seeds an LTR, non-spellchecked, editable textarea from the view', async () => {
    wrapper = await mountModal({ view: { id: 1, html: '<p>a</p>' } })

    const editor = textarea(wrapper)
    expect(editor.element.value).toBe('<p>a</p>')
    expect(editor.attributes('dir')).toBe('ltr')
    expect(editor.attributes('spellcheck')).toBe('false')
    expect(editor.attributes('readonly')).toBeUndefined()
    expect(editor.element.readOnly).toBe(false)
  })

  test('shows the size of the current source in characters', async () => {
    wrapper = await mountModal({ view: { id: 1, html: '<p>a</p>' } })

    expect(wrapper.get('.html-page-source__size').text()).toBe(
      'htmlPageSourceModal.size:{"bytes":8}'
    )
  })

  test('enables Save only after an edit, then emits the source and closes', async () => {
    wrapper = await mountModal({ view: { id: 1, html: '<p>a</p>' } })

    expect(saveButton(wrapper).exists()).toBe(true)
    expect(saveButton(wrapper).attributes('disabled')).toBeDefined()

    await textarea(wrapper).setValue('<p>b</p>')
    expect(saveButton(wrapper).attributes('disabled')).toBeUndefined()

    await saveButton(wrapper).trigger('click')
    expect(wrapper.emitted('save')).toEqual([['<p>b</p>']])

    // The modal closes on the next tick of the timer queue.
    await new Promise((resolve) => setTimeout(resolve))
    await nextTick()
    expect(wrapper.vm.$refs.modal.isOpen()).toBe(false)
    expect(wrapper.find('textarea').exists()).toBe(false)
  })

  test('seeds an empty string when the view has no html', async () => {
    wrapper = await mountModal({ view: { id: 1, html: null } })

    expect(textarea(wrapper).element.value).toBe('')
    expect(wrapper.vm.html).toBe('')
    expect(wrapper.get('.html-page-source__size').text()).toBe(
      'htmlPageSourceModal.size:{"bytes":0}'
    )
  })

  test('replaces a local edit when the stored html changes', async () => {
    wrapper = await mountModal({ view: { id: 1, html: '<p>a</p>' } })

    await textarea(wrapper).setValue('<p>local</p>')
    expect(wrapper.vm.html).toBe('<p>local</p>')

    await wrapper.setProps({ view: { id: 1, html: '<p>remote</p>' } })
    await nextTick()

    expect(wrapper.vm.html).toBe('<p>remote</p>')
    expect(textarea(wrapper).element.value).toBe('<p>remote</p>')
    expect(saveButton(wrapper).attributes('disabled')).toBeDefined()
  })

  test('read-only makes the textarea readonly and hides Save', async () => {
    wrapper = await mountModal({
      view: { id: 1, html: '<p>a</p>' },
      readOnly: true,
    })

    expect(textarea(wrapper).attributes('readonly')).toBeDefined()
    expect(textarea(wrapper).element.readOnly).toBe(true)
    expect(saveButton(wrapper).exists()).toBe(false)
    expect(wrapper.find('button.button').exists()).toBe(false)
  })
})
