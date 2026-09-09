# web-frontend/modules/builder/store/dataSourceContent.js

- SET_CONTENT · method · L10-L25 — SET_CONTENT(state, { page, dataSourceId, value })
- CLEAR_CONTENTS · method · L26-L28 — CLEAR_CONTENTS(state, { page })
- CLEAR_CONTENT · method · L30-L34 — CLEAR_CONTENT(state, { page, dataSourceId })
- SET_LOADING · method · L35-L37 — SET_LOADING(state, { page, value })
- fetchPageDataSourceContent · method · L44-L78 — async fetchPageDataSourceContent( { commit }, { page, data: queryData, mode } )
- fetchPageDataSourceContentById · method · L80-L112 — async fetchPageDataSourceContentById( { commit }, { page, dataSourceId, dispatchContext, mode, replace = false } )
- debouncedFetchPageDataSourceContent · method · L114-L128 — debouncedFetchPageDataSourceContent( { dispatch }, { page, data: queryData, mode } )
- clearDataSourceContent · method · L130-L132 — clearDataSourceContent({ commit }, { page, dataSourceId })
- clearDataSourceContents · method · L134-L136 — clearDataSourceContents({ commit }, { page })
