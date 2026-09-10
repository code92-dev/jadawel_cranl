# web-frontend/modules/database/services/field.js

- fetchAll · method · L5-L13 — fetchAll(tableId, viewId)
- create · method · L14-L17 — create(tableId, values, undoRedoActionGroupId = null)
- get · method · L18-L20 — get(fieldId)
- getUniqueRowValues · method · L21-L36 — getUniqueRowValues(fieldId, limit = 10, splitCommaSeparated = false)
- update · method · L37-L39 — update(fieldId, values)
- delete · method · L40-L42 — delete(fieldId)
- asyncDuplicate · method · L43-L54 — asyncDuplicate( fieldId, duplicateData = false, undoRedoActionGroupId = null )
- changePrimary · method · L55-L62 — changePrimary(tableId, newPrimaryFieldId)
