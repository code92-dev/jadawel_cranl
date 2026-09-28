"""Model registry entry point for the ``arabase`` app.

Django only discovers models that are importable from ``<app>.models``, so every
model the fork adds is re-exported here even though it is defined next to the
code that uses it.
"""

from arabase.backup.models import BackupRun, BackupSchedule
from arabase.dashboard.share.models import DashboardShare
from arabase.dashboard.widgets.models import (
    ChartWidget,
    ProgressWidget,
    RecordsListWidget,
    TextWidget,
    UpcomingDatesWidget,
)
from arabase.generative_ai.models import GenerativeAIProviderSettings
from arabase.integrations.local_jadawel.models import (
    LocalJadawelGroupedAggregateRows,
    LocalJadawelTableServiceAggregationGroupBy,
    LocalJadawelTableServiceAggregationSeries,
    LocalJadawelTableServiceAggregationSortBy,
    LocalJadawelUpcomingRows,
)
from arabase.mcp.protection.models import (
    ArtifactApproval,
    ArtifactAudience,
    ArtifactAuditEvent,
    ArtifactDraft,
    ArtifactDraftStatus,
    ArtifactManifestField,
    ArtifactProvenance,
    HtmlPageArtifactState,
    MCPProtectedField,
    MCPProtectionCommand,
    MCPProtectionEditCommand,
    MCPProtectionLifecycleAudit,
    MCPProtectionMutationAudit,
    MCPProtectionPolicy,
)
from arabase.sanad.models import (
    SanadBudget,
    SanadChat,
    SanadMessage,
    SanadMessageRole,
    SanadMessageStatus,
    SanadUsage,
)
from arabase.table_access.models import (
    PendingTableGrant,
    TableAccessLevel,
    TableGrant,
)
from arabase.views.models import (
    HtmlPageView,
    HtmlPageViewFieldOptions,
    HtmlPageViewRevision,
)

__all__ = [
    "BackupRun",
    "BackupSchedule",
    "DashboardShare",
    "ChartWidget",
    "ProgressWidget",
    "RecordsListWidget",
    "TextWidget",
    "UpcomingDatesWidget",
    "LocalJadawelGroupedAggregateRows",
    "LocalJadawelTableServiceAggregationGroupBy",
    "LocalJadawelTableServiceAggregationSeries",
    "LocalJadawelTableServiceAggregationSortBy",
    "LocalJadawelUpcomingRows",
    "MCPProtectedField",
    "MCPProtectionCommand",
    "MCPProtectionEditCommand",
    "MCPProtectionLifecycleAudit",
    "MCPProtectionMutationAudit",
    "MCPProtectionPolicy",
    "ArtifactAudience",
    "ArtifactDraftStatus",
    "ArtifactProvenance",
    "HtmlPageArtifactState",
    "ArtifactDraft",
    "ArtifactManifestField",
    "ArtifactApproval",
    "ArtifactAuditEvent",
    "HtmlPageView",
    "HtmlPageViewFieldOptions",
    "HtmlPageViewRevision",
    "GenerativeAIProviderSettings",
    "PendingTableGrant",
    "SanadBudget",
    "SanadChat",
    "SanadMessage",
    "SanadMessageRole",
    "SanadMessageStatus",
    "SanadUsage",
    "TableAccessLevel",
    "TableGrant",
]
