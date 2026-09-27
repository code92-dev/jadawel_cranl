import { createRouter, createMemoryHistory } from 'vue-router'
import {
  getRoutePagePath,
  resolveApplicationRoute,
} from '@jadawel/modules/builder/utils/routing'
import { routes } from '@jadawel/modules/builder/routes'

// The builder's own route patterns, resolved by the real vue-router.
const router = createRouter({
  history: createMemoryHistory(),
  routes: routes
    .filter(({ name }) =>
      ['application-builder-preview', 'application-builder-page'].includes(name)
    )
    .map(({ name, path }) => ({ name, path, component: {} })),
})

const pages = [
  { id: 1, path: '__shared__', shared: true },
  { id: 2, path: '/', shared: false },
  { id: 3, path: '/tasks', shared: false },
  { id: 4, path: '/projects/:id', shared: false },
]

const pageFor = (url) =>
  resolveApplicationRoute(pages, getRoutePagePath(router.resolve(url)))?.[0].id

describe('builder routing', () => {
  test.each([
    // Regression: vue-router 5 drops an empty catch-all param, so the home
    // page preview had no path at all and answered 404.
    ['/builder/44/preview/', 2],
    ['/builder/44/preview', 2],
    ['/builder/44/preview/tasks', 3],
    ['/builder/44/preview/projects/7', 4],
    ['/builder/44/preview/missing', undefined],
    // A published site on its own domain uses the same catch-all.
    ['/', 2],
    ['/tasks', 3],
    ['/projects/7', 4],
  ])('%s resolves to page %s', (url, pageId) => {
    expect(pageFor(url)).toBe(pageId)
  })

  test('the home page has an empty page path', () => {
    expect(getRoutePagePath(router.resolve('/builder/44/preview/'))).toBe('')
    expect(getRoutePagePath(router.resolve('/projects/7'))).toBe('projects/7')
  })
})
