# backend/src/jadawel/api/workspaces/users/serializers.py

- WorkspaceUserSerializer · class · L16-L53 — class WorkspaceUserSerializer(serializers.ModelSerializer)
- Meta · class · L25-L37 — class Meta
- get_name · method · L40-L41 — def get_name(self, object)
- get_email · method · L44-L45 — def get_email(self, object)
- get_two_factor_auth · method · L47-L53 — def get_two_factor_auth(self, object)
- get_member_data_types_request_serializer · function · L56-L85 — def get_member_data_types_request_serializer()
- Meta · class · L76-L77 — class Meta
- get_list_workspace_user_serializer · function · L88-L107 — def get_list_workspace_user_serializer()
- ListWorkspaceUsersWithMemberDataSerializer · class · L98-L105 — class ListWorkspaceUsersWithMemberDataSerializer( MemberDataTypeSerializer, WorkspaceUserSerializer )
- Meta · class · L101-L105 — class Meta(WorkspaceUserSerializer.Meta)
- WorkspaceUserWorkspaceSerializer · class · L110-L152 — class WorkspaceUserWorkspaceSerializer(serializers.Serializer)
- get_generative_ai_models_enabled · method · L149-L152 — def get_generative_ai_models_enabled(self, object)
- UpdateWorkspaceUserSerializer · class · L155-L158 — class UpdateWorkspaceUserSerializer(serializers.ModelSerializer)
- Meta · class · L156-L158 — class Meta
- GetWorkspaceUsersViewParamsSerializer · class · L161-L163 — class GetWorkspaceUsersViewParamsSerializer(serializers.Serializer)
