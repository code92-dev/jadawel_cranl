# backend/src/jadawel/contrib/database/api/views/utils.py

- get_public_view_authorization_token · function · L38-L51 — def get_public_view_authorization_token(request: Request) -> Optional[str]
- get_hidden_field_ids_for_view_user · function · L54-L65 — def get_hidden_field_ids_for_view_user( user: AbstractUser, view: View ) -> Optional[Set[int]]
- get_view_filtered_queryset · function · L68-L128 — def get_view_filtered_queryset( user: AbstractUser, view: Type[View], filters: Optional[AdHocFilters] = None, order_by: Optional[str] = None, query_params: Optional[Dict[str, Any]] = None, model: Optional[GeneratedTableModel] = None, hidden_field_ids: Optional[Set[int]] = None, ) -> QuerySet
- PublicViewFilteredQuerySet · class · L131-L134 — class PublicViewFilteredQuerySet(NamedTuple)
- get_public_view_filtered_queryset · function · L137-L181 — def get_public_view_filtered_queryset( view: Type[View], request: Request, query_params: Dict[str, Any] ) -> PublicViewFilteredQuerySet
- PaginatedData · class · L184-L187 — class PaginatedData(NamedTuple)
- _get_paginator · function · L190-L208 — def _get_paginator(request: Request) -> Pageable
- parse_limit_linked_items_params · function · L211-L229 — def parse_limit_linked_items_params(request) -> Optional[int]
- paginate_and_serialize_queryset · function · L232-L267 — def paginate_and_serialize_queryset( queryset: QuerySet[GeneratedTableModel], request: Request, field_ids: Optional[Iterable[int]], exclude_field_ids: Optional[Iterable[int]] = None, ) -> PaginatedData
- serialize_view_field_options · function · L270-L299 — def serialize_view_field_options( view: Type[View], model: GeneratedTableModel, create_if_missing: bool = True, context: Optional[Dict[str, Any]] = None, exclude_field_ids: Optional[Iterable[int]] = None, ) -> Dict[str, Any]
- serialize_rows_metadata · function · L302-L316 — def serialize_rows_metadata( user: AbstractUser, view: Type[View], rows: QuerySet[GeneratedTableModel] ) -> Dict[str, Any]
- serialize_single_row_metadata · function · L319-L332 — def serialize_single_row_metadata( user: AbstractUser, row: GeneratedTableModel ) -> Dict[str, Any]
- serialize_group_by_fields_metadata · function · L335-L344 — def serialize_group_by_fields_metadata( queryset: QuerySet[GeneratedTableModel], group_by_fields: List[Field], page: QuerySet[GeneratedTableModel], )
