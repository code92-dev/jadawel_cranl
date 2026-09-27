import { HtmlPageViewType } from '@jadawel/modules/arabase/views/viewTypes'

describe('page view type', () => {
  const app = { $i18n: { t: (key) => key }, $registry: { get: () => ({}) } }
  const viewType = new HtmlPageViewType({ app })

  test('shares, but offers no Filter or Sort in the header', () => {
    // The page's own code decides what it shows and in what order.
    expect(viewType.canShare).toBe(true)
    expect(viewType.canFilter).toBe(false)
    expect(viewType.canSort).toBe(false)
  })

  test('visible fields come from the page store, in order', () => {
    // Core's share popup calls this. It once read a getter the page store did
    // not have and crashed with "reading '<field id>'".
    const store = {
      getters: {
        'view/html_page/getAllFieldOptions': {
          1: { hidden: false, order: 2 },
          2: { hidden: true, order: 0 },
          3: { hidden: false, order: 1 },
        },
      },
    }
    const fields = [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }]

    const visible = viewType.getVisibleFieldsInOrder(
      { $store: store },
      fields,
      { id: 9 }
    )

    // Field 4 has no options yet, which the feed treats as visible.
    expect(visible.map((field) => field.id)).toEqual([4, 3, 1])
  })

  test('works before any field options are loaded', () => {
    const store = { getters: {} }

    const visible = viewType.getVisibleFieldsInOrder(
      { $store: store },
      [{ id: 363 }],
      { id: 9 }
    )

    expect(visible.map((field) => field.id)).toEqual([363])
  })

  test('opening the page loads its field options with the feed', async () => {
    const store = { dispatch: vi.fn() }
    const view = { id: 9 }

    await viewType.fetch({ store }, {}, view, [], '')

    expect(store.dispatch).toHaveBeenCalledWith('view/html_page/fetch', {
      view,
      fieldOptions: true,
    })
  })
})
