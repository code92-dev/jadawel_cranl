# backend/src/jadawel/contrib/database/airtable/import_report.py

- ImportReportFailedItem · class · L79-L84 — class ImportReportFailedItem
- AirtableImportReport · class · L87-L228 — class AirtableImportReport
- __init__ · method · L88-L89 — def __init__(self)
- add_failed · method · L91-L94 — def add_failed(self, object_name, scope, table, error_type, message)
- get_jadawel_export_table · method · L96-L182 — def get_jadawel_export_table(self, order: int) -> dict: # Create an empty grid view because the importing of views doesn't work # yet. It's a bit quick and dirty, but it will be replaced soon.
- append_items_to_exported_table · method · L184-L228 — def append_items_to_exported_table( self, exported_database: dict, items: list ) -> None
