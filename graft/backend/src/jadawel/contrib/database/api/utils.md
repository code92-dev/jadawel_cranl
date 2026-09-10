# backend/src/jadawel/contrib/database/api/utils.py

- get_include_exclude_field_ids · function · L26-L54 — def get_include_exclude_field_ids(table, include=None, exclude=None)
- get_include_exclude_fields · function · L57-L105 — def get_include_exclude_fields( table, include=None, exclude=None, user_field_names=False, queryset=None )
- extract_field_names_from_string · function · L109-L121 — def extract_field_names_from_string(value)
- extract_field_ids_from_list · function · L124-L144 — def extract_field_ids_from_list( list_of_field_names: List[str], strict: bool = True ) -> List[int]
- extract_field_ids_from_string · function · L147-L162 — def extract_field_ids_from_string(value)
- extract_user_field_names_from_params · function · L165-L179 — def extract_user_field_names_from_params(query_params)
- extract_send_webhook_events_from_params · function · L182-L193 — def extract_send_webhook_events_from_params(query_params) -> bool
- LinkedTargetField · class · L197-L205 — class LinkedTargetField
- __eq__ · method · L202-L205 — def __eq__(self, other): # compare only field_id # for test purposes
- LinkRowJoin · class · L209-L212 — class LinkRowJoin
- extract_link_row_joins_from_request · function · L215-L297 — def extract_link_row_joins_from_request( request, link_row_fields: QuerySet["Field"], user_field_names: bool = False ) -> list[LinkRowJoin]
- get_thousand_and_decimal_separator · function · L300-L307 — def get_thousand_and_decimal_separator(value)
