# backend/src/jadawel/contrib/dashboard/widgets/handler.py

- WidgetHandler · class · L21-L234 — class WidgetHandler
- get_widget · method · L22-L45 — def get_widget( self, widget_id: int, base_queryset: QuerySet | None = None ) -> Widget
- get_widget_for_update · method · L47-L71 — def get_widget_for_update( self, widget_id: int, base_queryset: QuerySet | None = None ) -> WidgetForUpdate
- get_widgets · method · L73-L107 — def get_widgets( self, dashboard: Dashboard, base_queryset: QuerySet | None = None, specific: bool = True, ) -> QuerySet[Widget] | Iterable[Widget]
- create_widget · method · L109-L139 — def create_widget( self, widget_type: WidgetType, dashboard: Dashboard, **kwargs, ) -> Widget
- update_widget · method · L141-L165 — def update_widget(self, widget: WidgetForUpdate, **kwargs) -> UpdatedWidget
- delete_widget · method · L167-L176 — def delete_widget(self, widget: Widget)
- export_widget · method · L178-L202 — def export_widget( self, widget: Widget, files_zip: ExportZipFile | None = None, storage: Storage | None = None, cache: dict[str, any] | None = None, ) -> WidgetDict
- import_widget · method · L204-L234 — def import_widget( self, dashboard: Dashboard, serialized_widget: WidgetDict, id_mapping: dict[str, dict[int, int]], files_zip: ExportZipFile | None = None, storage: Storage | None = None, cache: dict[str, any] | None = None, ) -> Widget
