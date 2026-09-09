# web-frontend/modules/database/services/row.js

- get · method · L11-L21 — get(tableId, rowId, includeMetadata = true, viewId = null)
- fetchAll · method · L22-L47 — fetchAll({ tableId, page = 1, size = 10, search = null, viewId = null, searchMode = null, })
- getIds · method · L75-L77 — getIds(tableId, rowNames)
- create · method · L78-L90 — create(tableId, values, beforeId = null, viewId = null)
- batchCreate · method · L91-L114 — batchCreate( tableId, rows, beforeId = null, undoRedoActionGroupId = null, viewId = null )
- update · method · L115-L127 — update(tableId, rowId, values, viewId = null)
- batchUpdate · method · L128-L141 — batchUpdate(tableId, items, undoRedoActionGroupId = null, viewId = null)
- move · method · L147-L159 — move(tableId, rowId, beforeRowId = null)
- delete · method · L160-L168 — delete(tableId, rowId, viewId)
- batchDelete · method · L169-L183 — batchDelete(tableId, items, viewId = null)
- getAdjacent · method · L184-L201 — getAdjacent({ tableId, rowId, viewId = null, previous = false, search = null, searchMode = null, })
