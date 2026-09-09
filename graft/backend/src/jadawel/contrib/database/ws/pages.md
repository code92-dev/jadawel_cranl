# backend/src/jadawel/contrib/database/ws/pages.py

- TablePageType · class · L21-L52 — class TablePageType(PageType)
- can_add · method · L25-L46 — def can_add(self, user, web_socket_id, table_id, **kwargs)
- get_group_name · method · L48-L49 — def get_group_name(self, table_id, **kwargs)
- get_permission_channel_group_name · method · L51-L52 — def get_permission_channel_group_name(self, table_id, **kwargs)
- PublicViewPageType · class · L55-L88 — class PublicViewPageType(PageType)
- can_add · method · L59-L85 — def can_add(self, user, web_socket_id, slug, token=None, **kwargs)
- get_group_name · method · L87-L88 — def get_group_name(self, slug, **kwargs)
- RowPageType · class · L91-L129 — class RowPageType(PageType)
- can_add · method · L95-L123 — def can_add(self, user, web_socket_id, table_id, row_id, **kwargs)
- get_group_name · method · L125-L126 — def get_group_name(self, table_id, row_id, *args, **kwargs)
- get_permission_channel_group_name · method · L128-L129 — def get_permission_channel_group_name(self, table_id, **kwargs)
