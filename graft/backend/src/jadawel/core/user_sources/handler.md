# backend/src/jadawel/core/user_sources/handler.py

- UserSourceHandler · class · L28-L441 — class UserSourceHandler
- _get_user_source · method · L32-L59 — def _get_user_source( self, queryset: QuerySet, specific=True, ) -> UserSource
- get_user_source · method · L61-L83 — def get_user_source( self, user_source_id: int, base_queryset: Optional[QuerySet] = None, specific=True, ) -> UserSource
- get_user_source_by_uid · method · L85-L107 — def get_user_source_by_uid( self, user_source_uid: str, base_queryset: Optional[QuerySet] = None, specific=True, ) -> UserSource
- get_user_source_for_update · method · L109-L130 — def get_user_source_for_update( self, user_source_id: int, base_queryset: Optional[QuerySet] = None ) -> UserSourceForUpdate
- get_user_sources · method · L132-L167 — def get_user_sources( self, application: Optional[Application] = None, base_queryset: Optional[QuerySet] = None, specific: bool = True, ) -> Union[QuerySet[UserSource], Iterable[UserSource]]
- per_content_type_queryset_hook · function · L157-L159 — def per_content_type_queryset_hook(model, queryset)
- get_all_roles_for_application · method · L169-L176 — def get_all_roles_for_application(self, application: Application) -> List[str]
- create_user_source · method · L178-L226 — def create_user_source( self, user_source_type: UserSourceType, application: Application, before=None, **kwargs, ) -> UserSource
- update_user_source · method · L228-L255 — def update_user_source( self, user_source_type: UserSourceType, user_source: UserSourceForUpdate, **kwargs, ) -> UserSource
- delete_user_source · method · L257-L264 — def delete_user_source(self, user_source: UserSource)
- move_user_source · method · L266-L289 — def move_user_source( self, user_source: UserSourceForUpdate, before: Optional[UserSource] = None ) -> UserSource
- recalculate_full_orders · method · L291-L302 — def recalculate_full_orders( self, application: Application, )
- export_user_source · method · L304-L316 — def export_user_source( self, user_source, files_zip: Optional[ExportZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict] = None, )
- import_user_source · method · L318-L347 — def import_user_source( self, application, serialized_user_source, id_mapping, files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict] = None, )
- _generate_update_user_count_chunk_queryset · method · L349-L365 — def _generate_update_user_count_chunk_queryset( self, user_source_type: UserSourceType )
- update_all_user_source_counts · method · L367-L404 — def update_all_user_source_counts( self, user_source_type: Optional[str] = None, update_in_chunks: bool = False, raise_on_error: bool = False, )
- aggregate_user_counts · method · L406-L441 — def aggregate_user_counts( self, workspace: Optional[Workspace] = None, base_queryset: Optional[QuerySet] = None, ) -> int
