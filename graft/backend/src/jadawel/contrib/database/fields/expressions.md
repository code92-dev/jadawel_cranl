# backend/src/jadawel/contrib/database/fields/expressions.py

- extract_jsonb_list_values_to_array · function · L23-L96 — def extract_jsonb_list_values_to_array( queryset: QuerySet, array_elements_expr: Union[Combinable, Expression], path_to_value_in_jsonb_list: Optional[List[Expression]] = None, transform_value_to_text_func: Optional[Callable[[Expression], Expression]] = None, extract_as_text: bool = True, ) -> Expression
- transform_value_to_text_func · function · L76-L77 — def transform_value_to_text_func(x)
- json_extract_path · function · L99-L105 — def json_extract_path(expr, path_to_value_in_jsonb_list, extract_as_text=True)
- extract_jsonb_array_values_to_single_string · function · L108-L165 — def extract_jsonb_array_values_to_single_string( field: "Field", queryset: QuerySet, path_to_value_in_jsonb_list: Optional[List[Expression]] = None, transform_value_to_text_func: Optional[Callable[[Expression], Expression]] = None, extract_as_text: bool = True, delimiter: str = " ", )
