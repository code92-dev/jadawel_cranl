# web-frontend/modules/core/store/workspaceSearch.js

- state · function · L3-L7 — state = ()
- SET_SEARCH_TERM · method · L10-L12 — SET_SEARCH_TERM(state, term)
- SET_RESULTS · method · L14-L16 — SET_RESULTS(state, results)
- SET_LOADING · method · L18-L20 — SET_LOADING(state, loading)
- CLEAR_RESULTS · method · L22-L24 — CLEAR_RESULTS(state)
- search · method · L28-L73 — async search( { commit, state }, { workspaceId, searchTerm, types = null, limit = 20, offset = 0, append = false, } )
- clearSearch · method · L75-L78 — clearSearch({ commit })
