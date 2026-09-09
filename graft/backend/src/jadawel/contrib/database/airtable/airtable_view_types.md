# backend/src/jadawel/contrib/database/airtable/airtable_view_types.py

- GridAirtableViewType · class · L23-L72 — class GridAirtableViewType(AirtableViewType)
- prepare_view_object · method · L27-L72 — def prepare_view_object( self, field_mapping, view: GridView, raw_airtable_table, raw_airtable_view, raw_airtable_view_data, config, import_report, ): # Airtable doesn't have this option, and by default it is count.
- GalleryAirtableViewType · class · L75-L182 — class GalleryAirtableViewType(AirtableViewType)
- get_cover_column · method · L79-L123 — def get_cover_column( self, field_mapping: dict, view: GalleryView, raw_airtable_table: dict, raw_airtable_view_data: dict, import_report: AirtableImportReport, ) -> Optional[str]
- prepare_view_object · method · L125-L182 — def prepare_view_object( self, field_mapping, view: GalleryView, raw_airtable_table, raw_airtable_view, raw_airtable_view_data, config, import_report, )
