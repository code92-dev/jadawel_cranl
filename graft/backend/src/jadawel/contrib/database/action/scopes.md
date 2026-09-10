# backend/src/jadawel/contrib/database/action/scopes.py

- TableActionScopeType · class · L25-L44 — class TableActionScopeType(ActionScopeType)
- value · method · L29-L30 — def value(cls, table_id: int) -> ActionScopeStr
- get_request_serializer_field · method · L32-L39 — def get_request_serializer_field(self) -> serializers.Field
- valid_serializer_value_to_scope_str · method · L41-L44 — def valid_serializer_value_to_scope_str( self, value: int ) -> Optional[ActionScopeStr]
- ViewActionScopeType · class · L47-L66 — class ViewActionScopeType(ActionScopeType)
- value · method · L51-L52 — def value(cls, view_id: int) -> ActionScopeStr
- get_request_serializer_field · method · L54-L61 — def get_request_serializer_field(self) -> serializers.Field
- valid_serializer_value_to_scope_str · method · L63-L66 — def valid_serializer_value_to_scope_str( self, value: int ) -> Optional[ActionScopeStr]
