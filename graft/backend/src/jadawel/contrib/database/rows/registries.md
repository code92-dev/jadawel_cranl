# backend/src/jadawel/contrib/database/rows/registries.py

- RowMetadataRegistry · class · L15-L73 — class RowMetadataRegistry(Registry)
- generate_and_merge_metadata_for_row · method · L23-L33 — def generate_and_merge_metadata_for_row( self, user, table, row_id: int ) -> Dict[str, Any]
- generate_and_merge_metadata_for_rows · method · L35-L73 — def generate_and_merge_metadata_for_rows( self, user, table, row_ids: Generator[int, None, None] ) -> Dict[int, Dict[str, Any]]
- RowMetadataType · class · L76-L115 — class RowMetadataType(Instance, abc.ABC)
- generate_metadata_for_rows · method · L89-L103 — def generate_metadata_for_rows( self, user, table, row_ids: List[int] ) -> Dict[int, Any]
- get_example_serializer_field · method · L106-L115 — def get_example_serializer_field(self) -> Field
- ChangeRowHistoryRegistry · class · L118-L124 — class ChangeRowHistoryRegistry(Registry)
- ChangeRowHistoryType · class · L127-L141 — class ChangeRowHistoryType(Instance, abc.ABC)
- apply_to_list_queryset · method · L129-L141 — def apply_to_list_queryset( self, queryset: QuerySet[RowHistory], workspace: Workspace, table_id: int, row_id: int, ) -> QuerySet[RowHistory]
- RowHistoryProviderType · class · L144-L155 — class RowHistoryProviderType(Instance, abc.ABC)
- get_row_history · method · L152-L155 — def get_row_history(self, user: AnyUser, params: ActionData) -> list[RowHistory]
- RowHistoryProviderRegistry · class · L158-L159 — class RowHistoryProviderRegistry(Registry[RowHistoryProviderType])
