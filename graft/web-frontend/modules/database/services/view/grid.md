# web-frontend/modules/database/services/view/grid.js

- fetchRows · method · L9-L105 — fetchRows({ gridId, limit = 100, offset = null, signal = null, includeFieldOptions = false, includeRowMetadata = true, search = '', searchMode = '', publicUrl = false, publicAuthToken = null, groupBy = '', orderBy = null, filters = {}, includeFields = [], excludeFields = [], excludeCount = false, limitLinkedItems = null, rowIds = [], })
- fetchCount · method · L106-L143 — fetchCount({ gridId, search = '', searchMode = '', signal = null, publicUrl = false, publicAuthToken = null, filters = {}, })
- filterRows · method · L144-L152 — filterRows({ gridId, rowIds, fieldIds = null })
- fetchFieldAggregations · method · L153-L182 — fetchFieldAggregations({ gridId, filters = {}, search = '', searchMode = '', signal = null, })
- fetchPublicFieldAggregations · method · L183-L219 — fetchPublicFieldAggregations({ slug, publicAuthToken = null, filters = {}, search = '', searchMode = '', signal = null, })
