# backend/src/jadawel/contrib/database/views/utils.py

- AnnotatedAggregation · class · L16-L30 — class AnnotatedAggregation
- __init__ · method · L23-L30 — def __init__(self, annotations: Dict[str, Any], aggregation: Aggregate)
- DistributionAggregation · class · L33-L62 — class DistributionAggregation
- __init__ · method · L39-L45 — def __init__(self, group_by)
- calculate · method · L47-L62 — def calculate(self, queryset, limit=10)
- serialize_row_for_action · function · L65-L89 — def serialize_row_for_action(row, model) -> Tuple[Dict[str, Any], Dict[str, Any]]
- check_permissions_with_view_fallback · function · L92-L172 — def check_permissions_with_view_fallback( table_operation: OperationType, view_operation: OperationType, user: AbstractUser, table: "Table", view: Optional["View"], row_ids: Optional[List[int]] = None, )
