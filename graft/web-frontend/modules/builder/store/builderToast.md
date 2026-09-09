# web-frontend/modules/builder/store/builderToast.js

- state · function · L3-L5 — state = ()
- ADD · method · L8-L10 — ADD(state, toast)
- REMOVE · method · L11-L14 — REMOVE(state, toast)
- add · method · L21-L29 — add({ commit }, { type, title = null, message = null, ...rest })
- infoNeutral · method · L30-L32 — infoNeutral({ dispatch }, { title, message })
- info · method · L33-L35 — info({ dispatch }, { title, message })
- error · method · L36-L38 — error({ dispatch }, { title, message, details })
- warning · method · L39-L41 — warning({ dispatch }, { title, message, details })
- success · method · L42-L44 — success({ dispatch }, { title, message })
- remove · method · L45-L47 — remove({ commit }, toast)
- all · method · L51-L53 — all(state)
