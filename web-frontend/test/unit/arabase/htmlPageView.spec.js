import { mountSuspended } from '@nuxt/test-utils/runtime'
import { isReactive, reactive } from 'vue'

import HtmlPageView from '@jadawel/modules/arabase/views/components/HtmlPageView'

/**
 * The component's job is containment, so that is what is asserted: the frame is
 * sandboxed without same-origin, data goes out only by postMessage, and
 * messages arriving from anywhere other than the frame are ignored.
 */
describe('HtmlPageView', () => {
  const database = { id: 1, workspace: { id: 1 } }
  const table = { id: 1 }
  const defaultFields = [
    { id: 10, name: 'Name', type: 'text' },
    { id: 11, name: 'Amount', type: 'number' },
  ]

  const mountView = async ({
    html = '<h1>hi</h1>',
    rows = [],
    fields = defaultFields,
    readOnly = false,
  } = {}) => {
    const getters = {
      'view/html_page/getLoading': false,
      'view/html_page/getLoaded': true,
      'view/html_page/getRows': rows,
      'view/html_page/getCount': rows.length,
      'view/html_page/getRowLimit': 200,
      'view/html_page/getTruncated': false,
    }

    return await mountSuspended(HtmlPageView, {
      props: {
        database,
        table,
        view: {
          id: 3,
          name: 'Report',
          type: 'html_page',
          html,
          content_security_policy: "default-src 'none'; connect-src 'none'",
          field_options: {},
        },
        fields,
        readOnly,
        storePrefix: '',
      },
      global: {
        mocks: {
          $store: { getters },
          $i18n: { locale: 'ar', localeProperties: { dir: 'rtl' } },
        },
        // The onboarding panel is covered by its own spec, and mounting it here
        // would drag in SettingsModal and the auth store with it.
        stubs: { HtmlPageOnboarding: true },
      },
    })
  }

  test('the frame is sandboxed and never gets same-origin back', async () => {
    const wrapper = await mountView()
    const frame = wrapper.find('iframe')

    expect(frame.exists()).toBe(true)
    // allow-scripts together with allow-same-origin would hand the untrusted
    // document this app's origin, and with it the viewer's session token.
    expect(frame.attributes('sandbox')).toBe('allow-scripts')
    expect(frame.attributes('sandbox')).not.toContain('allow-same-origin')
  })

  test('the policy is applied to the document that is rendered', async () => {
    const wrapper = await mountView()

    expect(wrapper.find('iframe').attributes('srcdoc')).toContain(
      'Content-Security-Policy'
    )
  })

  test('an empty page shows its owner how to get one written', async () => {
    const wrapper = await mountView({ html: '' })

    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.findComponent({ name: 'HtmlPageOnboarding' }).exists()).toBe(
      true
    )
  })

  test('a visitor on an empty public page is not shown the setup steps', async () => {
    // The panel lists the workspace's MCP endpoint and offers to mint a key.
    // None of that is a visitor's business, and the endpoint list behind it
    // needs an account anyway.
    const wrapper = await mountView({ html: '', readOnly: true })

    expect(wrapper.findComponent({ name: 'HtmlPageOnboarding' }).exists()).toBe(
      false
    )
    expect(wrapper.find('.html-page-view__state').exists()).toBe(true)
  })

  test('rows are keyed by field name as the runtime contract promises', async () => {
    const wrapper = await mountView({
      rows: [{ id: 1, order: '1', field_10: 'Acme', field_11: '42' }],
    })

    const [row] = wrapper.vm.payload.rows
    expect(row.values).toEqual({ Name: 'Acme', Amount: '42' })
    expect(row.raw).toEqual({ field_10: 'Acme', field_11: '42' })
    expect(row.id).toBe(1)
  })

  test('a missing value arrives as null rather than undefined', async () => {
    const wrapper = await mountView({ rows: [{ id: 1, order: '1' }] })

    expect(wrapper.vm.payload.rows[0].values).toEqual({
      Name: null,
      Amount: null,
    })
  })

  test('hidden fields are kept out of the payload', async () => {
    const wrapper = await mountView()
    await wrapper.setProps({
      view: {
        ...wrapper.props('view'),
        field_options: { 11: { hidden: true, order: 1 } },
      },
    })

    expect(wrapper.vm.payload.fields.map((f) => f.name)).toEqual(['Name'])
  })

  test("without options on the view, the store's field options apply", async () => {
    // In the app the view object carries no `field_options`; the store loads
    // them next to the feed.
    const wrapper = await mountView()
    wrapper.vm.$store.getters['view/html_page/getAllFieldOptions'] = {
      10: { hidden: false, order: 2 },
      11: { hidden: false, order: 1 },
    }
    await wrapper.setProps({
      view: { ...wrapper.props('view'), field_options: undefined },
    })

    expect(wrapper.vm.payload.fields.map((f) => f.name)).toEqual([
      'Amount',
      'Name',
    ])
  })

  test('a click inside the frame closes the popups the header opened', async () => {
    // The frame keeps its clicks, so a header popup's click-outside handler
    // only hears one if the component replays it when focus moves in.
    const wrapper = await mountView()
    const frame = wrapper.find('iframe').element
    const clicks = vi.fn()
    frame.addEventListener('click', clicks)
    vi.spyOn(document, 'activeElement', 'get').mockReturnValue(frame)
    vi.useFakeTimers()

    window.dispatchEvent(new Event('blur'))
    vi.runAllTimers()

    vi.useRealTimers()
    vi.restoreAllMocks()
    expect(clicks).toHaveBeenCalledTimes(1)
  })

  test('the page is told which direction to render in', async () => {
    // Direction comes from `<html dir>`, which the arabase plugin drives from
    // the locale. Reading it off `$i18n.localeProperties` instead looked right
    // and silently pinned every page to ltr, Arabic included, because that
    // property is undefined in the Options API.
    const previous = document.documentElement.dir
    document.documentElement.dir = 'rtl'

    try {
      const wrapper = await mountView()
      expect(wrapper.vm.payload.view.dir).toBe('rtl')
      expect(wrapper.vm.payload.view.locale).toBe('ar')
    } finally {
      document.documentElement.dir = previous
    }
  })

  test('direction falls back to ltr when the document says nothing', async () => {
    const previous = document.documentElement.dir
    document.documentElement.dir = ''

    try {
      const wrapper = await mountView()
      expect(wrapper.vm.payload.view.dir).toBe('ltr')
    } finally {
      document.documentElement.dir = previous
    }
  })

  test('a height from the frame is applied but bounded', async () => {
    const wrapper = await mountView()
    const frame = wrapper.vm.$refs.frame

    wrapper.vm.onMessage({
      source: frame.contentWindow,
      data: { type: 'jadawel:height', height: 500 },
    })
    expect(frame.style.height).toBe('500px')

    // A page must not be able to stretch the app's layout without limit.
    wrapper.vm.onMessage({
      source: frame.contentWindow,
      data: { type: 'jadawel:height', height: 10 ** 9 },
    })
    expect(frame.style.height).toBe('20000px')
  })

  test('what is posted is plain data, not a reactive proxy', async () => {
    // Regression: `payload` is assembled from store state, so in the real app
    // its objects are Vue reactive Proxies. Chrome's postMessage refuses to
    // structured-clone a Proxy, so every send() threw DataCloneError and the
    // page received nothing — while every assertion about how `payload` is
    // *built* still passed.
    //
    // Asserted as "not reactive" rather than "structuredClone does not throw":
    // Node's structuredClone happily reads through a Proxy, so the browser's
    // actual failure cannot be reproduced here. Plainness is the property that
    // makes it safe, and it is checkable in both.
    //
    // The file field is the point. Scalar cells come out of the store as plain
    // strings and stay plain through `.map()`, so a fixture of text and number
    // columns cannot fail this — it is object-valued cells (file, select,
    // link_row) that arrive as reactive Proxies and poison the whole payload.
    const wrapper = await mountView({
      fields: [...defaultFields, { id: 12, name: 'Photo', type: 'file' }],
      rows: reactive([
        {
          id: 1,
          order: '1',
          field_10: 'Acme',
          field_11: '42',
          field_12: [{ url: 'https://files/a.png', visible_name: 'a.png' }],
        },
      ]),
    })
    const frame = wrapper.vm.$refs.frame
    const posted = []
    // The test environment gives a detached iframe a null contentWindow, so it
    // is stubbed rather than driven through a real frame.
    Object.defineProperty(frame, 'contentWindow', {
      value: { postMessage: (message) => posted.push(message) },
      configurable: true,
    })

    wrapper.vm.send()

    expect(posted).toHaveLength(1)
    const values = posted[0].payload.rows[0].values
    expect(isReactive(values.Photo)).toBe(false)
    expect(isReactive(values.Photo[0])).toBe(false)
    expect(values.Photo).toEqual([
      { url: 'https://files/a.png', visible_name: 'a.png' },
    ])
    expect(values.Name).toBe('Acme')
  })

  test('data is pushed on mount, without waiting for load or ready', async () => {
    // Regression: the public page is server-rendered, so the frame can finish
    // loading and post its `ready` before Vue hydrates and the component starts
    // listening. Relying on `ready` or on `@load` alone left the page stuck on
    // its placeholders in the real app, with no error anywhere to explain it.
    const original = HtmlPageView.methods.send
    const send = vi.fn(function (...args) {
      return original.apply(this, args)
    })
    HtmlPageView.methods.send = send

    try {
      await mountView()
      expect(send).toHaveBeenCalled()
    } finally {
      HtmlPageView.methods.send = original
    }
  })

  test('a message from another window is ignored', async () => {
    const wrapper = await mountView()
    const frame = wrapper.vm.$refs.frame

    // Establish a known height through the legitimate path first, so the
    // assertion below distinguishes "rejected" from "never worked at all".
    wrapper.vm.onMessage({
      source: frame.contentWindow,
      data: { type: 'jadawel:height', height: 400 },
    })
    expect(frame.style.height).toBe('400px')

    wrapper.vm.onMessage({
      source: window,
      data: { type: 'jadawel:height', height: 9000 },
    })

    expect(frame.style.height).toBe('400px')
  })
})
