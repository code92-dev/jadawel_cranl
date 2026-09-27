import { match } from 'path-to-regexp'

/**
 * The application page path a builder route points at, without the leading
 * slash: '' for the home page, 'tasks', 'a/b'. Both builder routes catch it in
 * `:pathMatch(.*)*`. vue-router 5 leaves that param out entirely when it
 * matches nothing (vue-router 4 gave []), so the home page has none at all.
 */
export const getRoutePagePath = (route) => {
  const pathMatch = route.params.pathMatch ?? ''
  return Array.isArray(pathMatch) ? pathMatch.join('/') : pathMatch
}

export const resolveApplicationRoute = (pages, fullPath) => {
  if (fullPath === undefined || fullPath === null) {
    return undefined
  }

  for (const page of pages) {
    const matcher = match(page.path.slice(1))
    const matched = matcher(fullPath)

    if (matched) {
      // matched = { path, params, index? }
      return [page, matched.path, matched.params]
    }
  }

  return undefined
}
