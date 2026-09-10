# web-frontend/modules/database/store/rowModalNavigation.js

- state · function · L12-L27 — state = ()
- CLEAR_ROW · method · L30-L32 — CLEAR_ROW(state)
- SET_LOADING · method · L33-L35 — SET_LOADING(state, value)
- SET_ROW · method · L36-L38 — SET_ROW(state, row)
- SET_FAILED_TO_FETCH_TABLE_ROW_ID · method · L39-L42 — SET_FAILED_TO_FETCH_TABLE_ROW_ID(state, tableAndRowId)
- clearRow · method · L45-L48 — clearRow({ commit })
- setRow · method · L49-L52 — setRow({ commit }, row)
- fetchRow · method · L53-L68 — async fetchRow({ commit }, { tableId, rowId, viewId = null })
- fetchAdjacentRow · method · L69-L100 — async fetchAdjacentRow( { commit, dispatch, state }, { tableId, viewId, previous, activeSearchTerm } )
- getLoading · method · L103-L105 — getLoading(state)
- getRow · method · L106-L108 — getRow(state)
- getFailedToFetchTableRowId · method · L109-L111 — getFailedToFetchTableRowId(state)
