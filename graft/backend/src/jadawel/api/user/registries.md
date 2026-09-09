# backend/src/jadawel/api/user/registries.py

- UserDataType · class · L13-L63 — class UserDataType(Instance)
- get_user_data · method · L43-L57 — def get_user_data(self, user, request) -> dict
- realtime_message_to_update_user_data · method · L60-L63 — def realtime_message_to_update_user_data( cls, user_data: Dict[str, Any] ) -> Dict[str, Any]
- UserDataRegistry · class · L66-L85 — class UserDataRegistry(Registry[UserDataType])
- get_all_user_data · method · L69-L85 — def get_all_user_data(self, user, request) -> dict
- MemberDataType · class · L88-L124 — class MemberDataType(Instance)
- get_request_serializer_field · method · L96-L106 — def get_request_serializer_field( self, ) -> Union[serializers.Field, Dict[str, serializers.Field]]
- annotate_serialized_workspace_members_data · method · L108-L115 — def annotate_serialized_workspace_members_data( self, workspace: "Workspace", serialized_data: dict, user: AbstractUser ) -> dict
- annotate_serialized_admin_users_data · method · L117-L124 — def annotate_serialized_admin_users_data( self, user_ids: List[int], serialized_data: dict, user: AbstractUser ) -> dict
- MemberDataRegistry · class · L127-L128 — class MemberDataRegistry(Registry)
