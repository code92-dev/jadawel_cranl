# web-frontend/modules/arabase/dashboard/store/publicDashboardApplication.js

- state · function · L18-L22 — state = ()
- SET_PUBLIC_SOURCE · method · L26-L29 — SET_PUBLIC_SOURCE(state, { slug, authToken })
- setPublicSource · method · L34-L36 — setPublicSource({ commit }, { slug, authToken = null })
- fetchInitial · method · L43-L67 — async fetchInitial({ commit, dispatch }, { slug, authToken = null })
- dispatchDataSource · method · L68-L79 — async dispatchDataSource({ commit, state }, dataSourceId)
- getSlug · method · L84-L86 — getSlug(state)
- getAuthToken · method · L87-L89 — getAuthToken(state)
