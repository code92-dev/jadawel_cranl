# web-frontend/modules/arabase/kanban/viewType.js

- KanbanViewType · class · L11-L144 — class KanbanViewType extends ViewType
- getType · method · L12-L14 — static getType()
- getIconClass · method · L16-L18 — getIconClass()
- getColorClass · method · L20-L22 — getColorClass()
- getName · method · L24-L27 — getName()
- getDescription · method · L29-L32 — getDescription()
- canFilter · method · L34-L36 — canFilter()
- canSort · method · L38-L40 — canSort()
- canShare · method · L42-L44 — canShare()
- getComponent · method · L46-L48 — getComponent()
- getHeaderComponent · method · L50-L52 — getHeaderComponent()
- refresh · method · L54-L57 — refresh(context, database, view, fields, storePrefix = '')
- rowCreated · method · L59-L68 — rowCreated(context, tableId, fields, values, metadata, storePrefix)
- rowUpdated · method · L70-L124 — async rowUpdated( context, tableId, fields, rowBeforeUpdate, row, metadata, updatedFieldIds, storePrefix )
- stackIdOf · function · L90-L93 — stackIdOf = (aRow)
- rowDeleted · method · L126-L143 — rowDeleted(context, tableId, fields, row, storePrefix)
