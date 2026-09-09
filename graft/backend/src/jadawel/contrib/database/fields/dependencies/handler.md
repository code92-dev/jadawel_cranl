# backend/src/jadawel/contrib/database/fields/dependencies/handler.py

- FieldDependencyHandler · class · L32-L786 — class FieldDependencyHandler
- get_same_table_dependencies · method · L34-L48 — def get_same_table_dependencies(cls, field: Field) -> List[Field]
- rebuild_dependencies · method · L51-L63 — def rebuild_dependencies( cls, fields, field_cache: FieldCache ) -> List[FieldDependency]
- break_dependencies_delete_dependants · method · L66-L77 — def break_dependencies_delete_dependants(cls, fields)
- _get_all_dependent_fields · method · L80-L302 — def _get_all_dependent_fields( cls, table_id: int, field_ids: Iterable[int], field_cache: FieldCache, associated_relations_changed: bool, database_id_prefilter=None, ) -> Tuple[QuerySet[FieldDependency], Dict[int, Field]]
- queryset_hook · function · L283-L287 — def queryset_hook(model, queryset)
- group_dependencies_by_level · method · L305-L357 — def group_dependencies_by_level( cls, dependencies: Dict[int | str, Set[int | str]] ) -> List[List[int | str]]
- group_all_dependent_fields_by_level_from_fields · method · L360-L445 — def group_all_dependent_fields_by_level_from_fields( cls, fields: Iterable[Field], field_cache: FieldCache, associated_relations_changed: bool, database_id_prefilter=None, ) -> List[List[Tuple[int, Field]]]
- group_all_dependent_fields_by_level · method · L448-L534 — def group_all_dependent_fields_by_level( cls, table_id: int, field_ids: Iterable[int], field_cache: FieldCache, associated_relations_changed: bool, database_id_prefilter=None, ) -> List[FieldDependants]
- get_all_dependent_fields_with_type · method · L537-L603 — def get_all_dependent_fields_with_type( cls, table_id: int, field_ids: Iterable[int], field_cache: FieldCache, associated_relations_changed: bool, database_id_prefilter=None, ) -> FieldDependants
- get_dependant_fields_with_type · method · L606-L699 — def get_dependant_fields_with_type( cls, table_id: int, field_ids: Iterable[int], associated_relations_changed: bool, field_cache: FieldCache, starting_via_path_to_starting_table: Optional[str] = None, ) -> FieldDependants
- get_via_dependants_of_link_field · method · L702-L726 — def get_via_dependants_of_link_field(cls, field: "LinkRowField") -> FieldDependants
- rebuild_or_raise_if_user_doesnt_have_permissions_after · method · L729-L742 — def rebuild_or_raise_if_user_doesnt_have_permissions_after( cls, workspace: Workspace, user: AbstractUser, field: Field, field_cache: FieldCache, field_operation_name: str, )
- raise_if_user_doesnt_have_operation_on_dependencies_in_other_tables · method · L745-L786 — def raise_if_user_doesnt_have_operation_on_dependencies_in_other_tables( cls, workspace: Workspace, user: AbstractUser, field: Field, dependencies: List[FieldDependency], field_operation_name: str, )
