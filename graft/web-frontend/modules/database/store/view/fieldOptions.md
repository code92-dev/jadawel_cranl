# web-frontend/modules/database/store/view/fieldOptions.js

- state · function · L14-L16 — state = ()
- REPLACE_ALL_FIELD_OPTIONS · method · L19-L21 — REPLACE_ALL_FIELD_OPTIONS(state, fieldOptions)
- UPDATE_ALL_FIELD_OPTIONS · method · L22-L24 — UPDATE_ALL_FIELD_OPTIONS(state, fieldOptions)
- UPDATE_FIELD_OPTIONS_OF_FIELD · method · L25-L33 — UPDATE_FIELD_OPTIONS_OF_FIELD(state, { fieldId, values })
- DELETE_FIELD_OPTIONS · method · L34-L38 — DELETE_FIELD_OPTIONS(state, fieldId)
- updateFieldOptionsOfField · method · L46-L81 — async updateFieldOptionsOfField( { commit, getters, rootGetters }, { field, values, oldValues, readOnly = false, undoRedoActionGroupId = null, } )
- setFieldOptionsOfField · method · L86-L91 — setFieldOptionsOfField({ commit }, { field, values })
- updateAllFieldOptions · method · L96-L117 — async updateAllFieldOptions( { dispatch, getters, rootGetters }, { newFieldOptions, oldFieldOptions, readOnly = false } )
- forceUpdateAllFieldOptions · method · L121-L123 — forceUpdateAllFieldOptions({ commit }, fieldOptions)
- updateFieldOptionsOrder · method · L128-L158 — async updateFieldOptionsOrder( { commit, getters, dispatch }, { order, readOnly = false } )
- forceDeleteFieldOptions · method · L162-L164 — forceDeleteFieldOptions({ commit }, fieldId)
- getAllFieldOptions · method · L168-L170 — getAllFieldOptions(state)
