# backend/src/jadawel/core/action/scopes.py

- RootActionScopeType · class · L12-L28 — class RootActionScopeType(ActionScopeType)
- value · method · L16-L17 — def value(cls) -> ActionScopeStr
- get_request_serializer_field · method · L19-L25 — def get_request_serializer_field(self) -> serializers.Field
- valid_serializer_value_to_scope_str · method · L27-L28 — def valid_serializer_value_to_scope_str(self, value) -> Optional[ActionScopeStr]
- WorkspaceActionScopeType · class · L31-L50 — class WorkspaceActionScopeType(ActionScopeType)
- value · method · L35-L36 — def value(cls, workspace_id: int) -> ActionScopeStr
- get_request_serializer_field · method · L38-L45 — def get_request_serializer_field(self) -> serializers.Field
- valid_serializer_value_to_scope_str · method · L47-L50 — def valid_serializer_value_to_scope_str( self, value: int ) -> Optional[ActionScopeStr]
- ApplicationActionScopeType · class · L53-L72 — class ApplicationActionScopeType(ActionScopeType)
- value · method · L57-L58 — def value(cls, application_id: int) -> ActionScopeStr
- get_request_serializer_field · method · L60-L67 — def get_request_serializer_field(self) -> serializers.Field
- valid_serializer_value_to_scope_str · method · L69-L72 — def valid_serializer_value_to_scope_str( self, value: int ) -> Optional[ActionScopeStr]
