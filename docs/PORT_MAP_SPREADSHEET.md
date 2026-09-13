# Excel/ODS import and XLSX/ODS export — port map (Baserow 2.3.3 → Jadawel fork)

Sources: `/tmp/up/x/baserow-2.3.3` (reference), `/tmp/up/x/baserow-2.2.2` (baseline),
`/root/workspace/projects/jadawel_cranl` (target). Upstream `baserow.` → `jadawel.`,
`@baserow/...` → `@jadawel/...`.

## Summary

Exhaustive port map for the Jadawel (2.2.2 fork) → upstream Baserow 2.3.3 Excel/ODS import + XLSX/ODS export port. Key findings: (1) the *import* side is an OSS frontend feature — SheetJS parses `.xlsx/.xls/.ods` in the browser and the existing `file_import` async job (which is a JSON-payload job, unchanged in shape) receives the resulting 2-D array; the backend delta is only two metadata fields (`importer_type`, `original_file_name`) plus migration 0210. (2) The *export* side does not exist in upstream OSS at all: `xlsx` export is a **premium** feature (`premium/backend/src/baserow_premium/export/exporter_types.py` → `ExcelTableExporter`), and **ODS export does not exist anywhere in 2.3.3**. The additive seam is `TableExporter` + `table_exporter_registry` + the pre-existing `ExportJob` celery pipeline (`run_export_job`, `PaginatedExportJobFileWriter`, `EXPORT_FILES_DIRECTORY`), all of which already exist in the fork. (3) Two real hard dependencies: the fork's core `JobType.can_schedule_or_raise` lacks the 2.3 `_get_running_jobs`/`_can_schedule_or_raise` split that the 2.3 `FileImportJobType` override calls via `super()`, and the fork's export `QuerysetSerializer` lacks `include_row_id`/`include_primary_field`. Both are trivially portable. (4) ODS export needs a brand-new Python writer dependency; `openpyxl` cannot write `.ods` and SheetJS is frontend-only. Report written to docs/PORT_MAP_SPREADSHEET.md.

## Architecture

Import: browser-only parsing (SheetJS via lazy `import('xlsx')` in modules/database/utils/excel.js) → TableExcelImporter.vue emits `getData` → ImportFileModal/CreateTable flatten to a JSON 2-D array → POST /database/tables/<id>/import/async/ or /database/tables/database/<id>/async/ with {data, configuration, importer_type, original_file_name} → FileImportJobType (core.jobs) writes a JSON file via after_job_creation → celery run_async_job → CreateTableActionType.ImportRowsActionType. The backend never sees a spreadsheet; only two metadata columns change (migration 0210). Export: POST /database/export/table/<table_id>/ → _validate_options picks the option serializer from table_exporter_registry.get_option_serializer_map() → ExportHandler.create_pending_export_job (permission check ExportTableOperationType='database.table.run_export', cancels prior jobs) → ExportJob row + transaction.on_commit(run_export_job.delay) → celery task on the `export` queue → _open_file_and_run_export resolves `table_exporter_registry.get(job.exporter_type)`, builds a QuerysetSerializer (via for_table/for_view), writes through PaginatedExportJobFileWriter (updates progress_percentage and raises ExportJobCanceledException on cancel/expire) → exported_file_name stored in EXPORT_FILES_DIRECTORY → GET /database/export/<job_id>/ serializes `url` through FileURLSerializerMixin → frontend ExportTableModal polls every 1 s and turns the finished job into a DownloadLink. An additive xlsx/ods exporter touches only: a new TableExporter subclass + QuerysetSerializer, an options serializer, one registration line in contrib/database/apps.py, one frontend TableExporterType + form component, one $registry.register('exporter', ...) line, and locale keys. No migration, no new job type, no new endpoint.

## Files

| Path | Description |
|---|---|
| `docs/PORT_MAP_SPREADSHEET.md` | Full 7-section port map (backend, frontend, migrations, hard dependencies, locale keys, risk notes, export seam). Not persisted by this read-only scout — content is in data.report and must be written by the caller. |
| `backend/src/jadawel/contrib/database/file_import/job_types.py` | Fork's FileImportJobType; needs importer_type/original_file_name serializer fields, max_count 1→3, and _can_schedule_or_raise override. |
| `backend/src/jadawel/core/jobs/registries.py` | Fork core JobType; needs the _get_running_jobs/_can_schedule_or_raise split ported before FileImportJobType can override it. |
| `backend/src/jadawel/contrib/database/export/registries.py` | table_exporter_registry + abstract TableExporter — the exact seam an additive xlsx/ods exporter implements; already identical to upstream. |
| `backend/src/jadawel/contrib/database/export/file_writer.py` | PaginatedExportJobFileWriter (progress + cancellation) and QuerysetSerializer; fork lacks include_row_id/include_primary_field. |
| `backend/src/jadawel/contrib/database/export/handler.py` | _open_file_and_run_export is the pipeline an xlsx/ods exporter plugs into; already calls exporter.queryset_serializer_class and PaginatedExportJobFileWriter. |
| `backend/src/jadawel/contrib/database/api/export/serializers.py` | BaseExporterOptionsSerializer + CsvExporterOptionsSerializer; an Excel/ODS options serializer goes here. |
| `web-frontend/modules/database/utils/excel.js` | New file to port verbatim (SheetJS lazy loader + ExcelParser + stringifyCell). |
| `web-frontend/modules/database/components/table/TableExcelImporter.vue` | New file to port (sheet picker, first-row-header, PREVIEW_ROW_LIMIT=50, lazy full re-parse in getData). |
| `web-frontend/modules/database/components/export/TableExcelExporter.vue` | New file, ported from premium minus the license gate. |
| `web-frontend/modules/database/exporterTypes.js` | Register ExcelTableExporterType (and an ODS type) — non-premium subclass of TableExporterType. |
| `web-frontend/modules/database/importerTypes.js` | Add ExcelImporterType + TableExcelImporter import. |
| `web-frontend/package.json` | Add the pinned SheetJS xlsx 0.20.3 tarball dependency. |
