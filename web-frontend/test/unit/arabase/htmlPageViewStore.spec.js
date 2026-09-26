import {
  state,
  mutations,
  actions,
  getters,
} from '@jadawel/modules/arabase/views/store/htmlPageView'

/**
 * Characterizes the page view's row feed store together with the row service
 * it calls. The service is not mocked: the `$client` is the seam, so these
 * tests pin the exact request the store ends up making. Pinned before the
 * store and service are restructured.
 */
describe('htmlPageView store', () => {
  const feed = {
    results: [{ id: 1 }],
    count: 1,
    row_limit: 200,
    truncated: true,
  }

  let client
  let commit

  const fetch = (rootGetters, view = { id: 5 }) =>
    actions.fetch.call({ $client: client }, { commit, rootGetters }, { view })

  beforeEach(() => {
    client = { get: vi.fn().mockResolvedValue({ data: feed }) }
    commit = vi.fn()
  })

  test('fetches the authenticated feed and commits it between loading flags', async () => {
    await fetch({
      'page/view/public/getIsPublic': false,
      'page/view/public/getAuthToken': 'ignored',
    })

    expect(client.get).toHaveBeenCalledTimes(1)
    const [url, config] = client.get.mock.calls[0]
    expect(url).toBe('/database/views/html-page/5/')
    expect(Object.keys(config)).toEqual(['params'])
    expect(config.params).toBeInstanceOf(URLSearchParams)
    expect(config.params.toString()).toBe('')

    expect(commit.mock.calls).toEqual([
      ['SET_LOADING', true],
      [
        'SET_FEED',
        { rows: [{ id: 1 }], count: 1, rowLimit: 200, truncated: true },
      ],
      ['SET_LOADING', false],
    ])
  })

  test('treats an undefined public getter as an authenticated fetch', async () => {
    await fetch({})

    expect(client.get).toHaveBeenCalledTimes(1)
    const [url, config] = client.get.mock.calls[0]
    expect(url).toBe('/database/views/html-page/5/')
    expect(config).not.toHaveProperty('headers')
    expect(Object.keys(config)).toEqual(['params'])
  })

  test('fetches the public feed with the view authorization header', async () => {
    await fetch(
      {
        'page/view/public/getIsPublic': true,
        'page/view/public/getAuthToken': 'tok',
      },
      { id: 'slug' }
    )

    expect(client.get).toHaveBeenCalledTimes(1)
    const [url, config] = client.get.mock.calls[0]
    expect(url).toBe('/database/views/html-page/slug/public/rows/')
    expect(Object.keys(config)).toEqual(['params', 'headers'])
    expect(config.params.toString()).toBe('')
    expect(config.headers).toEqual({
      'Jadawel-View-Authorization': 'JWT tok',
    })
  })

  test('fetches the public feed without a header when there is no token', async () => {
    await fetch(
      {
        'page/view/public/getIsPublic': true,
        'page/view/public/getAuthToken': null,
      },
      { id: 'slug' }
    )

    expect(client.get).toHaveBeenCalledTimes(1)
    const [url, config] = client.get.mock.calls[0]
    expect(url).toBe('/database/views/html-page/slug/public/rows/')
    expect(config).not.toHaveProperty('headers')
    expect(Object.keys(config)).toEqual(['params'])
  })

  test('propagates a failed fetch and still clears the loading flag', async () => {
    const error = new Error('boom')
    client.get.mockRejectedValue(error)

    await expect(fetch({ 'page/view/public/getIsPublic': false })).rejects.toBe(
      error
    )

    expect(commit.mock.calls).toEqual([
      ['SET_LOADING', true],
      ['SET_LOADING', false],
    ])
  })

  test('SET_FEED marks the feed loaded and RESET restores the initial state', () => {
    const current = state()

    mutations.SET_LOADING(current, true)
    mutations.SET_FEED(current, {
      rows: [{ id: 1 }],
      count: 1,
      rowLimit: 200,
      truncated: true,
    })

    expect(current).toEqual({
      loading: true,
      loaded: true,
      rows: [{ id: 1 }],
      count: 1,
      rowLimit: 200,
      truncated: true,
    })

    mutations.RESET(current)

    expect(current).toEqual(state())
    expect(state()).toEqual({
      loading: false,
      loaded: false,
      rows: [],
      count: 0,
      rowLimit: 0,
      truncated: false,
    })
  })

  test('getters return their fields', () => {
    const current = {
      loading: true,
      loaded: true,
      rows: [{ id: 3 }],
      count: 4,
      rowLimit: 50,
      truncated: true,
    }

    expect(getters.getLoading(current)).toBe(true)
    expect(getters.getLoaded(current)).toBe(true)
    expect(getters.getRows(current)).toBe(current.rows)
    expect(getters.getCount(current)).toBe(4)
    expect(getters.getRowLimit(current)).toBe(50)
    expect(getters.getTruncated(current)).toBe(true)
  })

  test('reset commits RESET', () => {
    actions.reset({ commit })

    expect(commit.mock.calls).toEqual([['RESET']])
  })
})
