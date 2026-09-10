# web-frontend/modules/builder/store/elementContent.js

- SET_CONTENT · method · L11-L40 — SET_CONTENT(state, { element, value, range = null })
- SET_HAS_MORE_PAGE · method · L41-L43 — SET_HAS_MORE_PAGE(state, { element, value })
- CLEAR_CONTENT · method · L45-L48 — CLEAR_CONTENT(state, { element })
- TRIGGER_RESET · method · L49-L51 — TRIGGER_RESET(state, { element })
- SET_LOADING · method · L52-L54 — SET_LOADING(state, { element, value })
- fetchElementContent · method · L73-L219 — async fetchElementContent( { commit, getters }, { page, element, dataSource, range, filters = {}, sortings = null, search = '', searchMode = '', mode, data: dispatchContext, replace = false, } )
- clearElementContent · method · L220-L222 — clearElementContent({ commit }, { element })
- triggerElementContentReset · method · L224-L226 — triggerElementContentReset({ commit }, { element })
