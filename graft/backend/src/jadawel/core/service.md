# backend/src/jadawel/core/service.py

- CoreService · class · L18-L145 — class CoreService
- __init__ · method · L19-L20 — def __init__(self)
- _enhance_and_filter_application_queryset · method · L22-L27 — def _enhance_and_filter_application_queryset( self, user: AbstractUser, workspace: Workspace )
- list_workspaces · method · L29-L40 — def list_workspaces(self, user: AbstractUser) -> QuerySet[Workspace]
- get_workspace · method · L42-L61 — def get_workspace(self, user: AbstractUser, workspace_id: int) -> Workspace
- list_applications_in_workspace · method · L63-L101 — def list_applications_in_workspace( self, user: AbstractUser, workspace: Workspace, specific: bool = True, base_queryset: Optional[QuerySet] = None, ) -> QuerySet[Application]
- get_application · method · L103-L145 — def get_application( self, user: AbstractUser, application_id: int, specific: bool = True, base_queryset: Optional[QuerySet] = None, ) -> Application
