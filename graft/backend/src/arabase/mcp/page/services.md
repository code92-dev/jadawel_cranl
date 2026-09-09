# backend/src/arabase/mcp/page/services.py

- _get_page_view · function · L29-L54 — def _get_page_view( user: AbstractUser, workspace: Workspace, view_id: int ) -> HtmlPageView
- _view_summary · function · L57-L68 — def _view_summary(view: HtmlPageView) -> dict
- list_page_views · function · L71-L78 — def list_page_views( user: AbstractUser, workspace: Workspace, table_id: int ) -> list[dict]
- get_page_view · function · L81-L195 — def get_page_view( user: AbstractUser, workspace: Workspace, view_id: int, include_rows: bool = True, endpoint=None, ) -> dict
- create_page_view · function · L199-L234 — def create_page_view( user: AbstractUser, workspace: Workspace, table_id: int, name: str, html: Optional[str] = None, endpoint=None, protected_field_ids: Optional[list[int]] = None, audience: str = "authenticated", ) -> dict
- update_page_view · function · L238-L289 — def update_page_view( user: AbstractUser, workspace: Workspace, view_id: int, html: Optional[str] = None, name: Optional[str] = None, allow_external_resources: Optional[bool] = None, row_limit: Optional[int] = None, endpoint=None, protected_field_ids: Optional[list[int]] = None, audience: str = "authenticated", ) -> dict
- list_page_revisions · function · L292-L306 — def list_page_revisions( user: AbstractUser, workspace: Workspace, view_id: int ) -> list[dict]
- restore_page_revision · function · L310-L341 — def restore_page_revision( user: AbstractUser, workspace: Workspace, view_id: int, revision_id: int, endpoint=None, protected_field_ids: Optional[list[int]] = None, audience: str = "authenticated", ) -> dict
