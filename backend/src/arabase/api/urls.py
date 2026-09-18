from django.urls import re_path

from arabase.api.backup.views import (
    AdminBackupRestoreView,
    AdminBackupRunNowView,
    AdminBackupRunsView,
    AdminBackupView,
)
from arabase.api.contact import ContactFormView
from arabase.api.dashboard_share.public import (
    PublicDashboardAuthView,
    PublicDashboardDispatchView,
    PublicDashboardInfoView,
)
from arabase.api.dashboard_share.views import (
    DashboardSharePasswordView,
    DashboardShareRotateSlugView,
    DashboardShareView,
)
from arabase.api.mcp_protection.artifacts import (
    ArtifactDraftApprovalView,
    ArtifactDraftView,
    ArtifactRevokeView,
    ArtifactStateView,
)
from arabase.api.mcp_protection.views import (
    MCPEndpointProtectionSummariesView,
    MCPProtectionPolicyView,
    MCPProtectionReadinessView,
)
from arabase.api.table_access.views import TableAccessGuestView, TableAccessView
from arabase.api.views import WorkspaceActivityView, WorkspaceDatabaseStatsView

app_name = "arabase.api"

urlpatterns = [
    re_path(
        r"^mcp/protection/artifacts/drafts/$",
        ArtifactDraftView.as_view(),
        name="mcp_artifact_draft",
    ),
    re_path(
        r"^mcp/protection/artifacts/drafts/(?P<draft_id>[0-9]+)/approve/$",
        ArtifactDraftApprovalView.as_view(),
        name="mcp_artifact_draft_approve",
    ),
    re_path(
        r"^mcp/protection/artifacts/views/(?P<view_id>[0-9]+)/revoke/$",
        ArtifactRevokeView.as_view(),
        name="mcp_artifact_revoke",
    ),
    re_path(
        r"^mcp/protection/artifacts/views/(?P<view_id>[0-9]+)/$",
        ArtifactStateView.as_view(),
        name="mcp_artifact_state",
    ),
    re_path(
        r"^mcp/endpoints/$",
        MCPEndpointProtectionSummariesView.as_view(),
        name="mcp_endpoint_protection_summaries",
    ),
    re_path(
        r"^mcp/protection/readiness/$",
        MCPProtectionReadinessView.as_view(),
        name="mcp_protection_readiness",
    ),
    re_path(
        r"^mcp/endpoints/(?P<endpoint_id>[0-9]+)/protection-policy/$",
        MCPProtectionPolicyView.as_view(),
        name="mcp_protection_policy",
    ),
    re_path(
        r"^contact/$",
        ContactFormView.as_view(),
        name="contact_form",
    ),
    re_path(
        r"^workspace/(?P<workspace_id>[0-9]+)/database-stats/$",
        WorkspaceDatabaseStatsView.as_view(),
        name="workspace_database_stats",
    ),
    re_path(
        r"^workspace/(?P<workspace_id>[0-9]+)/table-access/$",
        TableAccessView.as_view(),
        name="table_access",
    ),
    re_path(
        r"^workspace/(?P<workspace_id>[0-9]+)/table-access/"
        r"(?P<workspace_user_id>[0-9]+)/$",
        TableAccessGuestView.as_view(),
        name="table_access_guest",
    ),
    re_path(
        r"^workspace/(?P<workspace_id>[0-9]+)/activity/$",
        WorkspaceActivityView.as_view(),
        name="workspace_activity",
    ),
    re_path(
        r"^dashboard/(?P<dashboard_id>[0-9]+)/share/$",
        DashboardShareView.as_view(),
        name="dashboard_share",
    ),
    re_path(
        r"^dashboard/(?P<dashboard_id>[0-9]+)/share/rotate-slug/$",
        DashboardShareRotateSlugView.as_view(),
        name="dashboard_share_rotate_slug",
    ),
    re_path(
        r"^dashboard/(?P<dashboard_id>[0-9]+)/share/password/$",
        DashboardSharePasswordView.as_view(),
        name="dashboard_share_password",
    ),
    re_path(
        r"^public/dashboard/(?P<slug>[-\w]+)/$",
        PublicDashboardInfoView.as_view(),
        name="public_dashboard",
    ),
    re_path(
        r"^public/dashboard/(?P<slug>[-\w]+)/auth/$",
        PublicDashboardAuthView.as_view(),
        name="public_dashboard_auth",
    ),
    re_path(
        r"^public/dashboard/(?P<slug>[-\w]+)/dispatch/(?P<data_source_id>[0-9]+)/$",
        PublicDashboardDispatchView.as_view(),
        name="public_dashboard_dispatch",
    ),
    re_path(
        r"^admin/backup/$",
        AdminBackupView.as_view(),
        name="admin_backup",
    ),
    re_path(
        r"^admin/backup/runs/$",
        AdminBackupRunsView.as_view(),
        name="admin_backup_runs",
    ),
    re_path(
        r"^admin/backup/run/$",
        AdminBackupRunNowView.as_view(),
        name="admin_backup_run_now",
    ),
    re_path(
        r"^admin/backup/restore/$",
        AdminBackupRestoreView.as_view(),
        name="admin_backup_restore",
    ),
]
