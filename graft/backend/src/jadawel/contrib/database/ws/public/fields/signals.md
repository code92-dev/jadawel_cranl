# backend/src/jadawel/contrib/database/ws/public/fields/signals.py

- _broadcast_payload_to_views_with_restricted_related_fields · function · L18-L32 — def _broadcast_payload_to_views_with_restricted_related_fields( payload: Dict[str, Any], serialized_related_fields: List[Dict[str, Any]], views_with_hidden_fields: List[Tuple[View, Set[int]]], )
- _send_payload_to_public_views_where_field_not_hidden · function · L35-L48 — def _send_payload_to_public_views_where_field_not_hidden( field: Field, payload: Dict[str, Any] )
- _get_public_views_with_hidden_fields · function · L51-L104 — def _get_public_views_with_hidden_fields( table_id: int, field_ids: Optional[List[int]] = None, ) -> List[Tuple[View, Set[int]]]
- _fetch · function · L66-L99 — def _fetch() -> List[Tuple[View, Set[int]]]
- _get_views_where_field_visible_and_hidden_fields_in_view · function · L107-L134 — def _get_views_where_field_visible_and_hidden_fields_in_view( field: Field, hidden_fields_field_ids_filter: Optional[Iterable[int]] = None, ) -> List[Tuple[View, Set[int]]]
- public_field_created · function · L138-L146 — def public_field_created(sender, field, related_fields, user, **kwargs)
- public_field_restored · function · L150-L158 — def public_field_restored(sender, field, related_fields, user, **kwargs)
- public_field_updated · function · L162-L170 — def public_field_updated(sender, field, related_fields, user, **kwargs)
- public_before_field_deleted · function · L174-L182 — def public_before_field_deleted(sender, field_id, field, user, **kwargs): # We have to check where the field is visible before it is deleted.
- public_field_deleted · function · L186-L203 — def public_field_deleted( sender, field_id, field, related_fields, user, before_return, **kwargs )
- send_deleted · function · L189-L201 — def send_deleted()
