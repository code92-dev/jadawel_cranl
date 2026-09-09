# backend/src/jadawel/contrib/database/ws/fields/signals.py

- field_created · function · L19-L30 — def field_created(sender, field, related_fields, user, **kwargs)
- field_restored · function · L34-L45 — def field_restored(sender, field, related_fields, user, **kwargs)
- field_updated · function · L49-L60 — def field_updated(sender, field, related_fields, user, **kwargs)
- field_deleted · function · L64-L78 — def field_deleted( sender, field_id, field, related_fields, user, before_return, **kwargs )
- RealtimeFieldMessages · class · L81-L172 — class RealtimeFieldMessages
- serialize_field_for_websockets · method · L88-L93 — def serialize_field_for_websockets( field: Field, field_serializer_class: Optional[Type[Serializer]] = None )
- serialize_fields_for_websockets · method · L96-L105 — def serialize_fields_for_websockets( fields: Iterable[Field], field_serializer_class: Optional[Type[Serializer]] = None, )
- field_created · method · L108-L121 — def field_created( field: Field, related_fields: Iterable[Field], field_serializer_class: Optional[Type[Serializer]] = None, )
- field_restored · method · L124-L139 — def field_restored( field: Field, related_fields: Iterable[Field], field_serializer_class: Optional[Type[Serializer]] = None, )
- field_updated · method · L142-L156 — def field_updated( field: Field, related_fields: Iterable[Field], field_serializer_class: Optional[Type[Serializer]] = None, )
- field_deleted · method · L159-L172 — def field_deleted( table_id: int, field_id: int, related_fields: Iterable[Field], field_serializer_class: Optional[Type[Serializer]] = None, )
