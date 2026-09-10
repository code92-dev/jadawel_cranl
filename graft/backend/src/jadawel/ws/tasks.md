# backend/src/jadawel/ws/tasks.py

- force_disconnect_users · function · L7-L31 — def force_disconnect_users( self, user_ids: List[int], ignore_web_socket_ids: Optional[List[str]] = None )
- send_message_to_channel_group · function · L34-L53 — async def send_message_to_channel_group( channel_layer, channel_group_name: str, message: dict )
- broadcast_to_users · function · L57-L92 — def broadcast_to_users( self, user_ids: List[int], payload: Dict[Any, Any], ignore_web_socket_id: Optional[int] = None, send_to_all_users: bool = False, )
- broadcast_to_permitted_users · function · L96-L162 — def broadcast_to_permitted_users( self, workspace_id: int, operation_type: str, scope_name: str, scope_id: int, payload: Dict[str, any], ignore_web_socket_id: Optional[int] = None, )
- broadcast_to_users_individual_payloads · function · L166-L192 — def broadcast_to_users_individual_payloads( self, payload_map: Dict[str, any], ignore_web_socket_id: Optional[int] = None )
- broadcast_many_to_channel_group · function · L196-L230 — def broadcast_many_to_channel_group( self, payloads: list[tuple[str, dict]], ignore_web_socket_id: str | None = None, exclude_user_ids: list[int] | None = None, )
- broadcast_to_channel_group · function · L234-L272 — def broadcast_to_channel_group( self, channel_group_name, payload, ignore_web_socket_id=None, exclude_user_ids=None, )
- broadcast_to_group · function · L276-L303 — def broadcast_to_group(self, workspace_id, payload, ignore_web_socket_id=None)
- broadcast_to_groups · function · L307-L332 — def broadcast_to_groups( self, workspace_ids: Iterable[int], payload: dict, ignore_web_socket_id: str = None )
- broadcast_application_created · function · L336-L392 — def broadcast_application_created( self, application_id: int, ignore_web_socket_id: Optional[int] = None )
