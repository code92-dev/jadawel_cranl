# Enhanced Group By — port map (Baserow 2.3.3 → Jadawel fork)

Sources: `/tmp/up/x/baserow-2.3.3` (reference), `/tmp/up/x/baserow-2.2.2` (baseline), `/root/workspace/projects/jadawel_cranl` (target).
All upstream `baserow.` Python imports become `jadawel.`; `@baserow/...` becomes `@jadawel/...`; `backend/src/baserow/` → `backend/src/jadawel/`. Premium/enterprise packages are absent from the fork, but **no group-by file in 2.3.3 imports premium or enterprise code** (grep for `premium|enterprise` over `contrib/database/views/` and `contrib/database/api/views/` returned nothing), so this port is OSS-only and self-contained.

---

## Backend files

| Upstream 2.3.3 path | Class | Target fork path | Adaptation | Specific hunks |
|---|---|---|---|---|
| `backend/src/baserow/contrib/database/views/constants.py` (5 lines) | **new file** | `backend/src/jadawel/contrib/database/views/constants.py` | none | Whole file: `GROUP_BY_DATA_DEFAULT_LIMIT = 40`. Fork has **no** `views/constants.py` (fork `views/` listing: `__init__ actions array_view_filters exceptions filters form_view_mode_types handler models notification_types object_scopes operations receivers registries row_checker service signals tasks usage_types utils validators view_aggregations view_filter_groups view_filters view_ownership_types view_types webhook_event_types`). |
| `views/models.py` | modified | `backend/src/jadawel/contrib/database/views/models.py` | none beyond imports (`core.mixins` already has `OrderableMixin` in fork at `core/mixins.py:25`) | (a) add module constant `MAX_ORDER_VALUE = 32767` with the comment that it must match `maxPossibleOrderValue` in `modules/database/utils/view.js` (2.3.3:46‑48; fork has no `MAX_ORDER_VALUE` anywhere in this file). (b) `class ViewSort(HierarchicalModelMixin, OrderableMixin, models.Model)` — 2.3.3:499 vs fork:504 `ViewSort(HierarchicalModelMixin, models.Model)`. (c) add `priority = models.PositiveSmallIntegerField(default=MAX_ORDER_VALUE, db_default=MAX_ORDER_VALUE, help_text="Position of this sorting in the ordering chain. The sorting with the lowest priority is applied first.")` — 2.3.3:521‑527. (d) `class Meta: ordering = ("priority", "id")` — 2.3.3:532‑533 (fork: `ordering = ("id",)`). (e) same for `ViewGroupBy` — class decl 2.3.3:546, `priority` 2.3.3:573‑579, Meta 2.3.3:584‑585. |
| `views/exceptions.py` | modified | `backend/src/jadawel/contrib/database/views/exceptions.py` | none | add `ViewSortNotInView` (2.3.3:89‑97, carries `view_sort_id`) and `ViewGroupByNotInView` (2.3.3:98‑107, carries `view_group_by_id`). Fork skips straight from `ViewSortFieldNotSupported`/`ViewGroupByFieldNotSupported` to `ViewDoesNotSupportFieldOptions` (`exceptions.py:104‑107`). |
| `views/signals.py` | modified | `backend/src/jadawel/contrib/database/views/signals.py` | none | add `view_sortings_prioritized = Signal()` (2.3.3:23) and `view_group_bys_prioritized = Signal()` (2.3.3:28). Fork currently jumps `view_sort_deleted` → `view_group_by_created` (lines 22‑24). |
| `views/operations.py` | modified | `backend/src/jadawel/contrib/database/views/operations.py` | none | add `PrioritizeViewSortOperationType` (`type = "database.table.view.prioritize_sortings"`, `object_scope_name = DatabaseViewSortObjectScopeType.type`) — 2.3.3:112‑114; add `PrioritizeViewGroupByOperationType` (`type = "database.table.view.prioritize_group_bys"`) — 2.3.3:142‑144. |
| `views/actions.py` | modified | `backend/src/jadawel/contrib/database/views/actions.py` | none | add `PrioritizeViewSortsActionType` (`type = "prioritize_view_sortings"`, descriptions `_("Prioritize view sortings")` / `_("View sortings priority changed")`, `do/reverse/redo` call `ViewHandler().prioritize_sortings`) — 2.3.3:1083‑1151; add `PrioritizeViewGroupBysActionType` (`type = "prioritize_view_group_bys"`) — 2.3.3:2392‑2466. Insert `PrioritizeViewSortsActionType` after `DeleteViewSortActionType` (2.3.3:1083) and `PrioritizeViewGroupBysActionType` after `DeleteViewGroupByActionType` (2.3.3:2392). |
| `views/handler.py` | **heavily modified** | `backend/src/jadawel/contrib/database/views/handler.py` | import renames; add missing stdlib/Django imports | (a) imports (2.3.3:1‑235): add `EmptyResultSet, FieldDoesNotExist` to the `django.core.exceptions` tuple (2.3.3:14‑18; fork has only `FieldDoesNotExist, ValidationError`), add `Case, ExpressionWrapper, F, IntegerField, Value, When` to `django.db.models` (2.3.3:20‑33; fork has `Count, Q, prefetch_related_objects`), keep `OrderBy`; add `from .constants import GROUP_BY_DATA_DEFAULT_LIMIT` (2.3.3:129); add `view_group_bys_prioritized, view_sortings_prioritized` to the `.signals` import block (2.3.3:198‑203); add `ViewGroupByNotInView, ViewSortNotInView` to `.exceptions`; add `django.db.transaction` (fork imports `connection, router`); `sql` must come from `jadawel.core.db`, which already re-exports it (fork `core/db.py:39` — `from jadawel.core.psycopg import is_deadlock_error, sql`). (b) add `GROUP_BY_DATA_ORDER_KEY_PREFIX = "_group_by_data_order_"` near line 226 (2.3.3:226). (c) add frozen dataclass `GroupByLevel(field, view_group_by)` at 2.3.3:232‑238. (d) add `_append_to_priority_chain(self, model, view, **create_kwargs)` — 2.3.3:2235‑2249 — and route `create_sort` (2.3.3:2316‑2318) and `create_group_by` (2.3.3:2609‑2611) through it. (e) add `prioritize_sortings` 2.3.3:2436‑2476 and `prioritize_group_bys` 2.3.3:2742‑2782. (f) add the group-by-data block: `get_group_by_fields` 4014‑4031, `get_group_by_data` 4033‑4139, `get_group_by_data_for_depth` 4141‑4216, `_resolve_view_group_bys` 4218‑4243, `_get_fields_from_group_by_levels` 4245‑4255, `_get_group_by_path_depth` 4257‑4273, `get_group_by_path_row_offset` 4275‑4294, `_get_group_by_path_row_offset` 4296‑4341, `_get_group_by_data_windowed_entry_for_path` 4343‑4375, `_get_group_by_data_window_order_sql` 4377‑4409, `_get_group_by_data_order_key_window_order_sql` 4411‑4445, `_is_group_by_data_order_key_order_by` 4447‑4451, `_get_group_by_data_table_references` 4453‑4467, `_prepare_group_by_data_window_query` 4469‑4498, `_fetch_group_by_data_rows` 4500‑4514, `_execute_group_by_data_windowed_query` 4516‑4600, `_execute_group_by_data_depth_windowed_query` 4602‑4690, `_execute_group_by_data_level_windowed_query` 4692‑4781, `get_group_by_data_for_parents` 4783‑4853, `_get_group_by_data_level_queryset` 4855‑4960, `_group_by_data_aggregation_alias` 4961‑4970, `_apply_group_by_data_aggregations` 4972‑5011, `_extract_group_by_aggregations` 5013‑5036, `_build_aggregations_only_page` 5038‑5081, `_add_group_by_data_order_key_annotations` 5083‑5115, `_get_group_by_data_order_key_order_by` 5117‑5137, `_build_group_by_data_path_filter_q` 5139‑5171, `_build_group_by_tree_order_by` 5173‑5208. This whole block is **absent** in fork (fork handler ends `get_group_by_metadata_in_rows` at 3784 and then goes to `restrict_row_for_view` at ~3820). |
| `views/view_types.py` | unchanged | `backend/src/jadawel/contrib/database/views/view_types.py` | none | Identical in both trees: `can_group_by = True` (line 86) and `get_visible_field_options_in_order` with `group_by_field_ids` (lines 286‑295). No hunk needed — listed only to close the file set. |
| `views/registries.py` | modified | `backend/src/jadawel/contrib/database/views/registries.py` | none | export side: add `"priority": sort.priority` to the sortings serialization (2.3.3:291, fork has only `{"id","field_id","order"}`) and `"priority": group_by.priority` to the group_bys serialization (2.3.3:302). **[UNVERIFIED]** the import/duplicate side (`import_serialized`, which recreates `ViewGroupBy`/`ViewSort`) was not read in either tree — the porter must confirm whether `priority` must also be replayed on import; upstream changed only the export block per the spans read (2.3.3:274‑323 vs fork:274‑323). |
| `apps.py` | modified | `backend/src/jadawel/contrib/database/apps.py` | import renames | import `PrioritizeViewGroupBysActionType, PrioritizeViewSortsActionType` (2.3.3:118‑119), register them (2.3.3:143, 147); import `PrioritizeViewGroupByOperationType, PrioritizeViewSortOperationType` (2.3.3:885‑886) and register them (2.3.3:968‑969). |
| `airtable/registry.py` | modified | `backend/src/jadawel/contrib/database/airtable/registry.py` | doc-string wording already says “Jadawel”; add the priority kwarg | 2.3.3:336 adds `priority=len(view_group_by) + 1` to the `ViewGroupBy(...)` constructed in `get_group_bys`; fork's block ends at `order=...` with no `priority` (fork:331‑334). (The sibling `priority=len(view_sorts)+1` for sorts at 2.3.3:262 belongs to the same migration but to the sort-reordering feature.) |
| `fields/registries.py` | **heavily modified** | `backend/src/jadawel/contrib/database/fields/registries.py` | none; required imports (`Subquery`, `OuterRef`, `Coalesce`, `ArrayAgg`, `Value`, `F`) were already present in 2.2.2 and remain in fork (fork `fields/registries.py:16,21‑41`) | (a) new `FieldType.get_group_by_order(...)` returning `self.get_order(...)` by default — 2.3.3:976‑1013 (fork has no `get_group_by_order` at all). (b) new `FieldType.get_group_by_display_values(field, field_name, raw_values) -> Optional[List[Any]]` returning `None` — 2.3.3:1923‑1957. (c) `ManyToManyGroupByMixin.get_group_by_field_unique_value` must become order-insensitive and tolerate both a manager and a plain list: `if value is None: return tuple()` / `hasattr(value, "all")` / `tuple(sorted(ids))` — 2.3.3:2264‑2277 (fork:2183‑2186 is `tuple([v.id for v in value.all()])`). (d) add `ManyToManyGroupByMixin.get_group_by_order` recomputing the ordering as correlated subqueries via `Subquery(...OuterRef("id")...)`/`OptionallyAnnotatedOrderBy` — 2.3.3:2284‑2308. (e) `get_group_by_aggregated_order` comment change at 2.3.3:2279‑2282. (f) `ManyToManyGroupByMixin.get_group_by_field_filters_and_annotations` body: `Coalesce(Subquery(through_model.objects.filter(...OuterRef("id")...).annotate(res=ArrayAgg(F(f"{related_field}_id"), order_by=self.get_group_by_aggregated_order(related_field))).values("res")[:1]), Value([], output_field=ArrayField(IntegerField())))` — 2.3.3:2311‑2348; fork's existing version at the same span differs only in this expression. |
| `fields/field_types.py` | modified | `backend/src/jadawel/contrib/database/fields/field_types.py` | none | (a) `DateFieldType.get_group_by_field_filters_and_annotations` — 2.3.3:1578‑1581 (fork has `get_group_by_field_unique_value` at 1523 but not this). (b) `LinkRowFieldType.get_group_by_display_values` resolving linked-row ids to `{"id","value"}` in one `id__in` query — 2.3.3:2575‑… (fork has `LinkRowFieldType._get_group_by_agg_expression` at 2416 but no display-values method). (c) `SingleSelectFieldType.get_group_by_display_values` using `_get_select_option_display_map` — 2.3.3:4642‑4644; also `SingleSelectFieldType.get_group_by_serializer_field` — 2.3.3:4833‑… (fork has a `get_group_by_serializer_field` at 4714, offsets differ; reconcile by method name, not line). (d) `MultipleSelectFieldType.get_group_by_display_values` (list per group) — 2.3.3:5357‑… (e) `MultipleCollaboratorsFieldType.get_group_by_display_values` resolving user ids to `{id, first_name}` — 2.3.3:7319‑… (f) the helper `_get_select_option_display_map` is referenced at 2.3.3:4643 and 5358 and **has no occurrence in the fork's `fields/` package** (grep `_get_select_option_display_map` → no matches) — it must be added; its definition line was not located, so read `SelectOptionBaseFieldType` in 2.3.3 `field_types.py` (class starts 2.3.3:4130) to lift it. |
| `api/views/serializers.py` | modified | `backend/src/jadawel/contrib/database/api/views/serializers.py` | none | (a) `ViewSortSerializer.Meta.fields` → `("id","view","field","order","type","priority")` with `extra_kwargs = {"id": {"read_only": True}, "priority": {"read_only": True}}` — 2.3.3:237‑242 (fork:237‑243 has no `priority`). (b) `ViewGroupBySerializer` add `"priority"` + read-only kwarg — 2.3.3:266‑281 (fork:263‑270). (c) `PublicViewSortSerializer` — 2.3.3:656‑661. (d) `PublicViewGroupBySerializer` — 2.3.3:675‑681 (fork:632‑652). (e) add `PrioritizeViewSortingsSerializer` — 2.3.3:622‑631 and `PrioritizeViewGroupBysSerializer` — 2.3.3:633‑641. |
| `api/views/errors.py` | modified | `backend/src/jadawel/contrib/database/api/views/errors.py` | none | add `ERROR_VIEW_SORT_NOT_IN_VIEW` (2.3.3:62‑66) and `ERROR_VIEW_GROUP_BY_NOT_IN_VIEW` (2.3.3:87‑91). Fork's file has neither (grep `NOT_IN_VIEW` → no matches). |
| `api/views/urls.py` | modified | `backend/src/jadawel/contrib/database/api/views/urls.py` | none | import `PrioritizeViewGroupBysView, PrioritizeViewSortingsView` (2.3.3:8‑9) and add the two routes: `r"(?P<view_id>[0-9]+)/sortings/prioritize/$"` name `prioritize_sortings`, and `r"(?P<view_id>[0-9]+)/group_bys/prioritize/$"` name `prioritize_group_bys` — 2.3.3:88‑99 (fork has neither). |
| `api/views/views.py` | modified | `backend/src/jadawel/contrib/database/api/views/views.py` | none | add class `PrioritizeViewSortingsView` — 2.3.3:1506‑1550 (body: `@transaction.atomic @map_exceptions({..., ViewSortNotInView: ERROR_VIEW_SORT_NOT_IN_VIEW})`, `post` dispatches `PrioritizeViewSortsActionType`) and class `PrioritizeViewGroupBysView` — 2.3.3:2242‑2290 (same shape with `ViewGroupByNotInView`/`PrioritizeViewGroupBysActionType`); add the corresponding imports of the two exceptions (2.3.3:117‑127), the two serializers (`PrioritizeViewGroupBysSerializer` 2.3.3:188, `PrioritizeViewSortingsSerializer`), the two error constants (2.3.3:166‑170) and the two action types (2.3.3:88). |
| `api/views/utils.py` | modified | `backend/src/jadawel/contrib/database/api/views/utils.py` | add `from decimal import Decimal`, `from ...fields.models import Field`, `from ...fields.registries import field_type_registry` | append after `serialize_group_by_fields_metadata` (fork ends the file at 344; 2.3.3 ends at 574): `_resolve_page_display_lists` 2.3.3:349‑379, `_resolve_group_by_display_lists` 2.3.3:381‑423, `json_safe_aggregation_value` 2.3.3:425‑433, `serialize_group_by_data` 2.3.3:435‑534, `serialize_group_by_data_pages` 2.3.3:536‑574. `serialize_group_by_fields_metadata` is byte-identical in both trees (2.3.3:337‑346 / fork:335‑344). |
| `api/views/grid/serializers.py` | modified | `backend/src/jadawel/contrib/database/api/views/grid/serializers.py` | none | append `GridViewGroupByDataGroupSerializer` (2.3.3:58‑113: `path`, `display`, `depth`, `row_count`, `children_count`, `sibling_index`, `row_offset`, `aggregations`), `GridViewGroupByDataPageSerializer` (2.3.3:115‑123), `GridViewGroupByDataSerializer` (2.3.3:125‑140: `pages`, `truncated`, `aggregations`). Fork's file ends at `GridViewFilterSerializer` (line 55). |
| `api/views/grid/utils.py` (778 lines) | **new file** | `backend/src/jadawel/contrib/database/api/views/grid/utils.py` | import renames + `from jadawel.config.settings.utils import str_to_bool, try_int` (both exist in fork, `config/settings/utils.py:122,126`) | module constants `GROUP_BY_DATA_DESCENDANT_MAX_GROUPS = 2000` and `GROUP_BY_DATA_DESCENDANT_MAX_PAGES = GROUP_BY_DATA_DESCENDANT_MAX_GROUPS` (2.3.3:43‑47); `parse_adhoc_view_group_bys` 50‑110; `parse_non_negative_int` 113‑125; `deserialize_group_by_path_object` 128‑180; `deserialize_group_by_parent_requests` 183‑265; `empty_group_by_data_page` 268‑292; `get_group_by_data_parent_path` 294‑317; `hashable_group_by_data_value` 319‑339; `group_by_data_page_key` 342‑364; `split_group_by_depth_page_by_parent` 366‑406; `group_by_data_page_request_key` 409‑430; `get_group_by_data_pages` 433‑651; `get_grid_view_group_by_aggregations` 654‑678; `build_group_by_data_response` 680‑778. Consumes `settings.ROW_PAGE_SIZE_LIMIT` at 242, 712, 717 (see Risk notes). |
| `api/views/grid/views.py` | modified | `backend/src/jadawel/contrib/database/api/views/grid/views.py` | import renames | (a) add to the `.serializers` import `GridViewGroupByDataSerializer`, to `.utils` import `build_group_by_data_response, empty_group_by_data_page, get_grid_view_group_by_aggregations, parse_adhoc_view_group_bys` — 2.3.3:107‑113; add `str_to_bool` — 2.3.3:18; add `ERROR_VIEW_GROUP_BY_FIELD_NOT_SUPPORTED` — 2.3.3:53; add `ViewGroupByFieldNotSupported` — 2.3.3:87. (b) add the OpenApiParameter constants `GROUP_BY_DATA_PARENTS_API_PARAM … GROUP_BY_DATA_INCLUDE_TOTALS_API_PARAM` — 2.3.3:120‑196. (c) add `class GridViewGroupByDataView` — 2.3.3:469‑613 (GET only, `get_permissions` returns `[AllowAny()]` for GET; body at 574‑612: `parse_adhoc_view_group_bys(request.GET.get("group_by"), queryset.model)`, fell back to the view's saved `viewgroupby_set` when the param is absent, `get_group_by_fields`, `get_grid_view_group_by_aggregations`, optional `include_totals`, then `build_group_by_data_response`). (d) add `class PublicGridViewGroupByDataView` — 2.3.3:939‑1069 (mirror of the above with `allowed_field_ids=visible_field_ids` at 1024‑1028). |
| `api/views/grid/urls.py` | modified | `backend/src/jadawel/contrib/database/api/views/grid/urls.py` | none | import `GridViewGroupByDataView, PublicGridViewGroupByDataView` and add `r"(?P<view_id>[0-9]+)/group-by-data/$"` name `group-by-data` (2.3.3:27‑30) and `r"(?P<slug>[-\w]+)/public/group-by-data/$"` name `public-group-by-data` (2.3.3:37‑40). |
| `ws/views/signals.py` | modified | `backend/src/jadawel/contrib/database/ws/views/signals.py` | none | add `@receiver(view_signals.view_sortings_prioritized)` — 2.3.3:305‑311 (payload `view_sortings_prioritized`, `view_id`, `view_sort_ids`) and `@receiver(view_signals.view_group_bys_prioritized)` — 2.3.3:348‑354 (payload `view_group_bys_prioritized`, `view_id`, `view_group_by_ids`). Fork's file has neither (grep `prioritiz` → no matches). |
| `application_types.py`, `views/registries.py` export prefetch | unchanged | same | none | Fork already prefetches `view_set__viewsort_set` / `view_set__viewgroupby_set` (`application_types.py:250‑251` fork / 2.3.3:250‑251). No hunk. |

---

## Frontend files

| Upstream 2.3.3 path | Class | Target fork path | Adaptation | Specific hunks |
|---|---|---|---|---|
| `web-frontend/modules/database/constants.js` | modified | `web-frontend/modules/database/constants.js` | none | add after the `LINKED_ITEMS_*` block: `// Soft UI cap on the number of group-bys a view can add. Views created with more (e.g. via the API) keep working; the UI just stops offering to add new ones.` + `export const MAX_GROUP_BYS = 5` — 2.3.3:22‑23. Fork's file has no `MAX_GROUP_BYS` (ends at `FIELD_CONSTRAINT_ERROR_CODES`). |
[…39ln elided…]

```python
dependencies = [
    ("database", "0210_fileimportjob_importer_type_and_more"),
]
```

Operations verbatim (2.3.3 lines 8‑37):

```python
operations = [
    migrations.AddField(
        model_name="viewsort",
        name="priority",
        field=models.PositiveSmallIntegerField(
            db_default=32767,
            default=32767,
            help_text="Position of this sorting in the ordering chain. The "
            "sorting with the lowest priority is applied first.",
        ),
    ),
    migrations.AddField(
        model_name="viewgroupby",
        name="priority",
        field=models.PositiveSmallIntegerField(
            db_default=32767,
            default=32767,
            help_text="Position of this group by in the ordering chain. The "
            "group by with the lowest priority is applied first.",
        ),
    ),
    migrations.AlterModelOptions(
        name="viewsort",
        options={"ordering": ("priority", "id")},
    ),
    migrations.AlterModelOptions(
        name="viewgroupby",
        options={"ordering": ("priority", "id")},
    ),
]
```

**Fork adaptation.** The upstream dependency `0210_fileimportjob_importer_type_and_more` does **not** exist in the fork (fork's `0210` is `0210_jadawel_rename_default_grid_views.py`). Fork database-app migration chain (verified by glob + dependency reads):

- `0208_gridview_frozen_column_count`
- `0209_alter_formview_mode` → depends on `("database", "0208_gridview_frozen_column_count")`
- `0210_jadawel_rename_default_grid_views` → depends on `("database", "0209_alter_formview_mode")` + `("core", "0116_jadawel_arabic_english_only")`
- **`0211_jadawel_rename_table_usage_functions` → depends on `("database", "0210_jadawel_rename_default_grid_views")` — this is the current head of the `database` app** (no `0212+` exists in the fork).

So the new fork migration must be numbered after the local head, e.g. `backend/src/jadawel/contrib/database/migrations/0212_viewgroupby_viewsort_priority.py`, with:

```python
dependencies = [
    ("database", "0211_jadawel_rename_table_usage_functions"),
]
```

and the identical four operations (upstream's `db_default=32767, default=32767` values, not `MAX_ORDER_VALUE`, since a migration must not import live model constants). Do **not** reuse the name `0211_viewsort_viewgroupby_priority` — that number is taken in the fork.

Cross-app dependents on the fork head that already exist and are unaffected (all depend on `0211_jadawel_rename_table_usage_functions`, so a new leaf `0212` in `database` is safe): `arabase/migrations/0006_html_page_view.py:13`, `arabase/migrations/0007_mcp_protection_policy.py:25`, `arabase/migrations/0013_artifactapproval_artifactdraft_artifactauditevent_and_more.py:15`, `arabase/migrations/0016_kanban_view.py:14`, `jadawel/contrib/integrations/migrations/0029_alter_localjadaweltableservicefieldmapping_service_and_more.py:11`.

The `AlterModelOptions` operations must stay in lockstep with the `models.py` `Meta.ordering` change (backend table row above); if only one lands, Django will generate a spurious follow-up migration. Also note the pre-existing duplicate numbers `0207_add_view_default_values` / `0207_fix_data_sync_missing_primary_field` in the fork are resolved by a `0208` merge dependency in upstream 2.2.2 (`0207_fix_data_sync_missing_primary_field` depends on `0207_add_view_default_values`); do not disturb that.

---

## Hard dependencies

### Trivially portable helpers (small, pure, no new subsystem)

| Dependency | Evidence in 2.3.3 | Absence in fork |
|---|---|---|
| `Frontend/modules/database/utils/rowLifecycle.js` | imported by the new grid store (`store/view/grid.js:5‑11`); exports `createRowLifecycleContext` (27), `reapplyMatchFlags` (71), `handleRowDeleted` (86), `handleRowUpdated` (118), `handleRowCreated` (184) | file does not exist (`glob` of `web-frontend/modules/database/utils/rowLifecycle.js` → not found, in both fork and 2.2.2) |
| `utils/row.js` helpers `isSkeletonRow` (11), `resolveBeforeRow` (27), `buildNewRowDefaults` (132), `computeRowMatchFlags` (187), `computeMultiSelectPosition` (242), `computeRowInsertPosition` (361) | same file | fork `utils/row.js` has none of these names (grep of all six → no matches); it has `prepareRowForRequest`, `prepareNewOldAndUpdateRequestValues`, `extractRowReadOnlyValues`, `extractChangedFields`, `updateRowMetadataType`, `getRowMetadata` |
| `utils/view.js` `isAdhocGroupBy` (507) and `viewHasRulesThatCanMoveOrHideRows` (563) | 2.3.3 `utils/view.js` | fork `utils/view.js` has `isAdhocSorting` (494) and `isAdhocFiltering` (561) but neither group-by twin (grep → no matches) |
| `viewAggregationTypes.js` `isAllowedInGroupBy` | base 2.3.3:100‑103, distribution override 2.3.3:915‑918 | fork file has `isAllowedInView` (95‑97, 155‑158) and no `isAllowedInGroupBy` anywhere |
| `views/constants.py` (`GROUP_BY_DATA_DEFAULT_LIMIT = 40`) | 2.3.3 `views/constants.py` | fork `views/` has no `constants.py` |
| `str_to_bool` / `try_int` | used by the new `api/views/grid/utils.py` | **already present** in fork `config/settings/utils.py:122` and `:126` — no work |
| PostgreSQL `sql` composer in the handler | 2.3.3 `views/handler.py` uses `sql.SQL/Identifier/Composable` throughout the windowed query builders (e.g. 4360‑4590) and imports it via `from baserow.core.db import ... sql ...` (2.3.3:105) | fork `core/db.py:39` already does `from jadawel.core.psycopg import is_deadlock_error, sql` → `from jadawel.core.db import sql` works unchanged |
| `django.core.exceptions.EmptyResultSet` | 2.3.3 handler imports it at 15 and catches it at 4488 | fork handler imports only `FieldDoesNotExist, ValidationError` (fork:17) — one-line import addition |
| `OrderableMixin.order_objects` | used by `_append_to_priority_chain` (2.3.3:2247) and `prioritize_*` (2.3.3:2469, 2775) | **already present** in fork `core/mixins.py:25` + `order_objects` at `:45` |
| `collaboratorName` mixin | used by `GridViewGroupValueMultipleCollaborators.vue` | **already present** at fork `modules/database/mixins/collaboratorName.js` |
| `v-sortable` directive | used by the new drag handles | **already present**: fork `modules/core/directives/sortable.js` registered in `plugins/global.js:117`; fork's sidebar already uses it (`SidebarWithWorkspace.vue:30`) |
| `GroupTaskQueue` | used by `store/view.js` (2.3.3:19‑20) and the grid store | **already present** at fork `modules/core/utils/queue.js:103` |

### Large subsystems (porting is the bulk of the work, not a dependency lookup)

1. **Group-by-data backend engine** — `views/handler.py` 2.3.3:4014‑5208 (≈1,200 lines): windowed SQL group enumeration with sibling indexes, absolute `row_offset`s, per-level partitioned windows (`_execute_group_by_data_depth_windowed_query`, `_execute_group_by_data_level_windowed_query`), path filters (`_build_group_by_data_path_filter_q`), order-key annotations, descendant budgets and aggregations. Nothing comparable exists in the fork (fork handler's group-by surface ends at `get_group_by_metadata_in_rows`).
2. **`api/views/grid/utils.py`** — 778 lines, entirely new: ad-hoc `group_by` parsing into unsaved `ViewGroupBy` objects, path serialization/deserialization, page keys, depth-page splitting, batched descendant fetching, aggregation resolution and response assembly.
3. **`api/views/utils.py` group-by serialization** — `_resolve_group_by_display_lists` / `serialize_group_by_data` / `serialize_group_by_data_pages` (2.3.3:349‑574), which introduce a `display` map contract for reference fields and JSON-safe aggregation values.
4. **Frontend grouped-grid data model** — `utils/gridGroupBy.js` (1,321 lines) + `utils/gridGroupByRender.js` (710 lines) + the rewritten `store/view/grid.js` (6,674 lines). The fork's grid store is 2.2-style flat buffering with `groupByMetadata`, so this is a replacement, not an insertion.
5. **Field-type display/order hooks** — `get_group_by_display_values` (LinkRow 2575, SingleSelect 4642, MultipleSelect 5357, MultipleCollaborators 7319) and `get_group_by_order` (base 976, M2M 2284) plus the `_get_select_option_display_map` helper referenced at 4643/5358 but absent from the fork's `fields/` package (grep → no matches; definition line not located, read `SelectOptionBaseFieldType` 2.3.3:4130+ to lift it). Without these the `display` map and set-based M2M group ordering are wrong, not merely missing.

### Verified NON-dependencies

- **No premium/enterprise imports** anywhere in the 2.3.3 group-by surface (grep `premium|enterprise` over `contrib/database/views/` and `contrib/database/api/views/` → no matches). The upstream premium `LocalBaserowGroupedAggregateRows` data source is a *different* feature and is not required.
- `views/view_types.py` and `application_types.py` need **no** changes (fork already has `can_group_by = True` and the `viewsort_set`/`viewgroupby_set` prefetches).
- The upstream 2.3 `presence`, Excel import, builder, code-runner and workflow-node subsystems are **not** referenced by any group-by file.

### Items the porter must verify locally (not fully traced)

- `settings.ROW_PAGE_SIZE_LIMIT` — consumed by `api/views/grid/utils.py` at 2.3.3:242, 712, 717 and defined upstream at `config/settings/base.py:853` as `int(os.getenv("BASEROW_ROW_PAGE_SIZE_LIMIT", 200))`. The fork's settings module was **not** read in this pass; confirm the equivalent exists (the frontend already consumes `$config.public.jadawelRowPageSizeLimit`, so it is likely `JADAWEL_ROW_PAGE_SIZE_LIMIT`). If absent, add it (mirroring the existing `get_max_result_limit` plumbing) before porting `grid/utils.py`.
- `ViewType.get_aggregations(view)` — called by `get_grid_view_group_by_aggregations` (2.3.3:673‑678). The fork's `GridViewFieldAggregationsView` exists, which strongly implies it, but the method name was not read in the fork.
- `FieldType.get_group_by_serializer_field` — present in fork (`fields/registries.py:1856`, M2M `:2230`) and used by the new `serialize_group_by_data`; confirm signatures match 2.3.3:1907/2350 (they do per the spans read).
- `views/registries.py` import/duplicate side for `priority` (see the backend table row marked **[UNVERIFIED]**).

---

## Locale keys

**Path correction:** the group-by UI strings live in **`web-frontend/modules/database/locales/`**, not `modules/core/locales/`. The fork has `modules/database/locales/en.json` (1,194 lines) and `modules/database/locales/ar.json`; `modules/core/locales/` contains only `en.json`/`ar.json` and **no** `viewGroupByContext`/`viewGroupBy` keys (grep `GroupBy|groupBy` → no matches). Upstream 2.3.3 has the same split (`modules/database/locales/*.json` carries `viewGroupByContext`, `viewGroupBy`, `gridViewGroupByBanner`) and ships **no** `ar.json` (its locale list: cs, de, en, es, fa, fi, fr, hu, id, it, ja, ko, mr, nb_NO, nl, pl, pt_BR, pt_PT, ru, uk, zh_Hans), so the Arabic strings below are authored for Jadawel and need native review.

### `web-frontend/modules/database/locales/en.json`

Add inside the existing `"viewGroupByContext"` object (fork currently at lines 560‑567; upstream at 579‑589), after `"addGroupBy"` and before `"hiddenFieldWarning"`:

```json
"maxGroupBysReached": "You can group by up to {count} fields.",
"collapseAllGroups": "Collapse all",
"expandAllGroups": "Expand all",
```

Add inside the existing `"gridViewFieldType"` object (fork at 671+; upstream at 701‑710), after `"sortField": "Sort",`:

```json
"groupByField": "Group by",
"ungroupByField": "Don't group by",
```

Add a new top-level object immediately after `"viewGroupBy"` (fork `viewGroupBy` is at 568‑570; upstream puts the new block at 593‑597):

```json
"gridViewGroupByBanner": {
  "emptyValue": "(Empty)",
  "expandGroup": "Expand group",
  "collapseGroup": "Collapse group"
},
```

### `web-frontend/modules/database/locales/ar.json`

The fork's existing `"viewGroupByContext"` block (lines 929‑936) already reads `"groupBy": "مجموعة حسب"`, `"thenBy": "ثم حسب"`, `"addGroupBy": "اختر حقلًا للتجميع حسبه"`, `"hiddenFieldWarning": "يشير تجميع واحد أو أكثر إلى حقول مخفية …"`; `"gridViewFieldType"` is at 959‑969. Add (authored, not copied from upstream — flag for review):

```json
"maxGroupBysReached": "يمكنك التجميع حسب ما يصل إلى {count} حقول.",
"collapseAllGroups": "طيّ الكل",
"expandAllGroups": "توسيع الكل",
```

inside `viewGroupByContext`;

```json
"groupByField": "التجميع حسب",
"ungroupByField": "إلغاء التجميع حسب",
```

inside `gridViewFieldType`;

```json
"gridViewGroupByBanner": {
  "emptyValue": "(فارغ)",
  "expandGroup": "توسيع المجموعة",
  "collapseGroup": "طيّ المجموعة"
},
```

as a new top-level object after `"viewGroupBy"` (fork lines 937‑939). Keep the fork's existing Arabic term for the group-by concept (`مجموعة حسب` / `تجميع`) so the new strings agree with `viewGroupByContext.groupBy`; `PATCHES.md:648‑650` records that `fieldType.rollup` deliberately still uses `تجميع` for a different concept, so do **not** rename anything there.

---

## Risk notes

1. **The grid store is a replacement, not an insertion.** `web-frontend/modules/database/store/view/grid.js` goes 3,907 → 6,674 lines and the fork's copy already diverges from upstream 2.2.2 (`REFRESH_ROW_DELAY` vs upstream's `REFRESH_ROW_DELAY_MS`, local `RefreshCancelledError` handling, no `adhocGrouping`, `getRowSortFunction`/`matchSearchFilters` via `utils/view` instead of `rowLifecycle`). Dropping the 2.3.3 file in wholesale will silently revert those fork-local fixes and drop the local error/abort semantics. Diff both files against 2.2.2 before merging, and re-apply the fork deltas explicitly.
2. **`utils/groupBy.js` must be deleted, not kept.** 2.3.3 has no `fieldValuesAreEqualInObjects` anywhere in `modules/` (grep → no matches). Its two fork consumers (`GridViewSection.vue:178`, `store/view/grid.js:31`) are both rewritten here. Leaving the file plus a compatibility import would be exactly the “second convention beside the existing” the fork should not carry.
3. **Migration numbering and the models `Meta` change must land together.** The upstream dependency `0210_fileimportjob_importer_type_and_more` does not exist in the fork, so a literal copy of `0211_viewsort_viewgroupby_priority.py` will fail to resolve. The new migration (suggested `0212_viewgroupby_viewsort_priority`, dependency `("database", "0211_jadawel_rename_table_usage_functions")`) must be paired with the `models.py` `MAX_ORDER_VALUE` + `priority` + `Meta.ordering = ("priority", "id")` change in the same commit, or `makemigrations` will detect drift. Note also that other fork apps already depend on `0211_jadawel_rename_table_usage_functions` (`arabase` 0006/0007/0013/0016, `integrations` 0029) — adding a `0212` leaf is safe, but do not renumber `0211`.
4. **`db_default=32767` vs `MAX_ORDER_VALUE`.** The migration must inline `32767`; the model must reference `MAX_ORDER_VALUE` (which the comment pins to `maxPossibleOrderValue` in `modules/database/utils/view.js:9`). Both frontend and backend treat `32767` as the “place last” sentinel, and `_append_to_priority_chain` renumbers to a dense `1..N` to avoid smallint overflow (the historical `smallint out of range` error documented at 2.3.3:2237‑2241). Existing rows all get `32767`, so the first reorder of any view must go through `order_objects`, not a hand-rolled incremental counter.
5. **Priority ordering is now load-bearing for row order.** `ViewGroupBy.Meta.ordering` changes from `("id",)` to `("priority", "id")`; `View.get_all_sorts` chains group-bys before sorts (identical in both trees, 2.3.3:226‑251 / fork:222‑247). Any code path that relied on creation order implicitly still works (all defaults are equal → falls back to `id`), but any code that *sorts in Python* over `viewgroupby_set` must not re-sort arbitrarily.
6. **Grouped mode changes the rows-endpoint contract on the client.** In grouped mode the grid no longer uses `state.rows`/`bufferStartIndex`; `getAllRows`/`getRowsLength`/`getRowIndexById` route through the group layout, and the *viewport* viewport math must be pixel-consistent with rendered header/row/gap heights. `gridGroupByRender.js` exports `HEADER_HEIGHT = 48`, `ROW_HEIGHT = 33`, `GROUP_GAP = 8`, `ADD_ROW_HEIGHT = ROW_HEIGHT`; the SCSS block (2.3.3 `grid.scss:486‑832`) must match those constants exactly or scroll math drifts. This coupling is documented in the upstream design note `docs/technical/collapsible-grid-group-by.md` (which is worth porting alongside).
7. **The two layers must agree.** The group metadata endpoint and the rows endpoint must apply identical filters, search, sorts and group ordering. Upstream enforces this by having `GridViewGroupByDataView` build its queryset through the same `get_public_*_queryset_and_field_ids` / `get_queryset` path (2.3.3 `grid/views.py:574‑586` and `1024‑1038`). If the fork's rows endpoint and the new group endpoint diverge (e.g. a fork-local filter tweak), `row_offset` will place rows in the wrong group — this is called out as the top invariant in the upstream design doc.
8. **RTL.** The fork has an explicit RTL pass (`PATCHES.md:315‑339` converted the grid/group-by panels to CSS logical properties). The new 2.3.3 SCSS uses physical `left:` for the banner (`grid.scss:488`), and `GridViewGroupByBanner.vue` uses `paddingLeft` and `left: position - 1 + 'px'` for separators, and `gridGroupByRender.js` computes indents from `rowDetailsWidth` assuming an inline-start lane. These must be re-localized (`inset-inline-start`, `padding-inline-start`) and the `groupBannerIndentPx` caller must be checked under `dir="rtl"`, exactly as the earlier pass did for `group_bys.scss`.
9. **`group_bys.scss` and the context component must move together.** The drag handle, the always-visible footer (`canAddGroupBy || view.group_bys.length > 0`) and the collapse/expand buttons are one visual unit; the footer change also alters which buttons render for read-only viewers, so it must be checked against restricted/read-only views (the `disableGroupBy` prop path).
10. **Public/shared views.** `PublicGridViewGroupByDataView` (2.3.3:939‑1069) is a separate class with `AllowAny` and `allowed_field_ids=visible_field_ids`; the fork's `PublicGridViewRowsView` already exists, so the new class is additive — but the frontend must select `public/group-by-data/` via the `publicUrl` flag in `fetchGroupByData`, otherwise shared grouped grids will 401/404. The upstream `PublicViewGroupBySerializer` also gains `priority` (2.3.3:675‑681), which the public frontend ordering depends on.
11. **Tests.** Upstream ships regression coverage that should be ported with the code (not optional, given the size of the engine): backend `tests/baserow/contrib/database/api/views/test_view_group_by.py`, `api/views/grid/test_grid_view_group_by_data.py`, `api/views/grid/test_grid_view_group_by_utils.py`, `view/test_view_handler_group_by_data.py`, `view/actions/test_view_group_by_actions.py`; frontend `test/unit/database/utils/gridGroupBy.spec.js`, `utils/gridGroupByRender.spec.js`, `components/view/grid/gridViewGroupByAggregation.spec.js`, `gridViewGroupByBanner.spec.js`, `gridViewGroupValueBoolean.spec.js`, `gridViewGroupValueMultipleCollaborators.spec.js`, `gridViewGroupValueMultipleSelect.spec.js`, `fieldTypes/formulaFieldTypeGroupBy.spec.js`. The fork currently has no group-by test equivalents for these paths (grep for `grid_view_group_by|GridViewGroupBy|gridGroupBy` under `backend/tests/jadawel` and `web-frontend/test` → only the unrelated Airtable import tests).
12. **Out-of-scope neighbours that will look like group-by work.** Upstream `GridRowContextItems.vue` and `utils/rowLifecycle.js` arrive in the same release but only the latter is a grid-store dependency; `0210_fileimportjob_importer_type_and_more`, `0212_data_sync_delete_unmatched_rows`, the Excel importer and the presence subsystem must not be dragged in. Conversely, the KANBAN 2.3 features are absent from the fork and are not required here.


[You have received this identical output 3 times. Re-reading 'agent://ScoutGroupBy?q=.report' will not change it — use a narrower selector (path:A-B), or proceed with the edit.]

[Showing lines 1-43 and 83-268 of 268; 39 middle lines (20.8KB) elided. Read artifact://262 for full output]