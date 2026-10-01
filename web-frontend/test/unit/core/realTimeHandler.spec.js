import { vi, describe, test, expect } from 'vitest'

import { RealTimeHandler } from '@jadawel/modules/core/plugins/realTimeHandler'

vi.mock('#imports', () => ({
  useRuntimeConfig: () => ({
    public: { publicBackendUrl: 'http://localhost' },
  }),
}))

function makeStore() {
  const dispatched = []
  return {
    getters: {
      'auth/token': 'token',
      'auth/webSocketId': 'test-ws-id',
      'workspace/isLoaded': true,
    },
    dispatch(name, value) {
      dispatched.push([name, value])
      return Promise.resolve()
    },
    subscribe() {},
    _dispatched: dispatched,
  }
}

function makeHandler() {
  const store = makeStore()
  const context = { store, app: { router: {} } }
  const handler = new RealTimeHandler(context)
  return { handler, store, context }
}

function fire(handler, type, data) {
  return Promise.all(
    (handler.events[type] || []).map((cb) => cb(handler.context, data))
  )
}

describe('RealTimeHandler last_viewed_updated', () => {
  const fireFor = (application, lastViewed) => {
    const { handler, store } = makeHandler()
    store.getters['application/get'] = (id) =>
      application?.id === id ? application : undefined
    fire(handler, 'last_viewed_updated', {
      type: 'last_viewed_updated',
      item_type: 'database_view',
      item_id: 7,
      application_id: 3,
      workspace_id: 1,
      last_viewed: lastViewed,
    })
    return store._dispatched
  }

  test('applies a newer timestamp to the application', () => {
    const application = { id: 3, last_viewed: '2026-01-01T12:00:00Z' }
    expect(fireFor(application, '2026-01-01T12:05:00Z')).toEqual([
      [
        'application/forceUpdate',
        { application, data: { last_viewed: '2026-01-01T12:05:00Z' } },
      ],
    ])
  })

  test('applies the first timestamp of a never viewed application', () => {
    const application = { id: 3, last_viewed: null }
    expect(fireFor(application, '2026-01-01T12:00:00Z')).toHaveLength(1)
  })

  test('compares as moments, not as strings', () => {
    // A fractional second sorts before a whole one as a string, yet is later.
    const application = { id: 3, last_viewed: '2026-01-01T12:00:00Z' }
    expect(fireFor(application, '2026-01-01T12:00:00.500000Z')).toHaveLength(1)
  })

  test('ignores an older or equal timestamp, so late events cannot go back', () => {
    const application = { id: 3, last_viewed: '2026-01-01T12:05:00Z' }
    expect(fireFor(application, '2026-01-01T12:00:00Z')).toEqual([])
    expect(fireFor(application, '2026-01-01T12:05:00Z')).toEqual([])
  })

  test('ignores an application that is not in the store', () => {
    expect(fireFor(undefined, '2026-01-01T12:05:00Z')).toEqual([])
  })
})
