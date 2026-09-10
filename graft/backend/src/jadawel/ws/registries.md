# backend/src/jadawel/ws/registries.py

- PageType · class · L7-L139 — class PageType(Instance)
- can_add · method · L29-L46 — def can_add(self, user, web_socket_id, **kwargs)
- get_group_name · method · L48-L63 — def get_group_name(self, **kwargs)
- get_permission_channel_group_name · method · L65-L79 — def get_permission_channel_group_name(self, **kwargs) -> Optional[str]
- broadcast · method · L81-L105 — def broadcast( self, payload, ignore_web_socket_id=None, exclude_user_ids=None, **kwargs )
- broadcast_many · method · L107-L139 — def broadcast_many( self, payloads_with_groups: list[tuple[dict, dict]], ignore_web_socket_id: str | None = None, exclude_user_ids: list[int] | None = None, **kwargs, )
- PageRegistry · class · L142-L143 — class PageRegistry(Registry)
