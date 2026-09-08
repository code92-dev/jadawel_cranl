from typing import Any

from django.db.models import Q

from jadawel.core.exceptions import (
    OperationTypeDoesNotExist,
    PermissionDenied,
    UserNotInWorkspace,
)
from jadawel.core.registries import PermissionManagerType, operation_type_registry
from jadawel.core.subjects import UserSubjectType
from jadawel.contrib.database.tokens.subjects import TokenSubjectType

from .models import Organization, OrganizationWorkspaceAccess


class OrganizationPermissionManagerType(PermissionManagerType):
    """Enforce organization membership and restricted billing access in core APIs."""

    type = "organization"
    supported_actor_types = [UserSubjectType.type, TokenSubjectType.type]

    READ_OPERATIONS = {
        "application.integration.read",
        "application.list_integrations",
        "application.list_snapshots",
        "application.list_user_sources",
        "application.read",
        "application.read_trash",
        "application.user_source.read",
        "automation.list_workflows",
        "automation.node.read",
        "automation.workflow.list_nodes",
        "automation.workflow.read",
        "builder.domain.read",
        "builder.list_domains",
        "builder.list_pages",
        "builder.page.data_source.read",
        "builder.page.element.read",
        "builder.page.list_data_sources",
        "builder.page.list_elements",
        "builder.page.list_workflow_actions",
        "builder.page.read",
        "builder.page.workflow_action.read",
        "dashboard.data_source.read",
        "dashboard.list_data_sources",
        "dashboard.list_widgets",
        "dashboard.widget.read",
        "database.data_sync.get",
        "database.data_sync.list_properties",
        "database.list_tables",
        "database.table.field.read",
        "database.table.field_rules.read_field_rules",
        "database.table.formula.type",
        "database.table.list_fields",
        "database.table.list_row_names",
        "database.table.list_rows",
        "database.table.list_views",
        "database.table.listen_to_all",
        "database.table.list_webhooks",
        "database.table.read",
        "database.table.read_adjacent_row",
        "database.table.read_row",
        "database.table.read_row_history",
        "database.table.read_view_order",
        "database.table.view.decoration.read",
        "database.table.view.filter.read",
        "database.table.view.filter_group.read",
        "database.table.view.group_by.read",
        "database.table.view.list_aggregations",
        "database.table.view.list_comments",
        "database.table.view.list_decoration",
        "database.table.view.list_fields",
        "database.table.view.list_filter",
        "database.table.view.list_group_bys",
        "database.table.view.list_rows",
        "database.table.view.list_sort",
        "database.table.view.read",
        "database.table.view.read_adjacent_row",
        "database.table.view.read_aggregation",
        "database.table.view.read_default_values",
        "database.table.view.read_field_options",
        "database.table.view.read_row",
        "database.table.view.sort.read",
        "database.table.webhook.read",
        "invitation.read",
        "list_workspaces",
        "workspace.list_applications",
        "workspace.list_invitations",
        "workspace.list_notifications",
        "workspace.list_workspace_users",
        "workspace.mcp_endpoint.read",
        "workspace.read",
        "workspace.read_trash",
        "workspace.token.read",
    }
    WRITE_OPERATIONS = {
        "workspace.update",
        "workspace.delete",
        "workspace.create_application",
        "workspace.create_invitation",
        "workspace.order_applications",
        "application.update",
        "application.duplicate",
        "application.delete",
        "database.table.update_row",
        "database.table.delete_row",
        "database.table.restore_row",
        "workspace.export",
        "workspace.restore",
    }

    @classmethod
    def is_read_operation(cls, operation_name: str) -> bool:
        """Allow only registered operations explicitly classified as reads.

        Unknown operations fail closed.  An explicit set prevents mutation names
        such as ``workspace.mark_notification_as_read`` from being mistaken for
        safe reads because of their suffix.
        """
        try:
            operation_type_registry.get(operation_name)
        except OperationTypeDoesNotExist:
            return False
        return operation_name in cls.READ_OPERATIONS

    def _binding(self, workspace: Any):
        if workspace is None:
            return None
        return Organization.objects.filter(
            workspaces__workspace_id=workspace.pk
        ).first()

    def _allowed(self, actor: Any, organization: Organization, workspace: Any) -> bool:
        user = getattr(actor, "user", actor)
        if getattr(user, "is_staff", False):
            return True
        return OrganizationWorkspaceAccess.objects.filter(
            binding__organization=organization,
            binding__workspace_id=workspace.pk,
            membership__user_id=user.pk,
            membership__suspended=False,
            binding__organization__status=Organization.Status.ACTIVE,
        ).exists()

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        if workspace is None:
            # ``create_workspace`` is a global operation in Jadawel and has no
            # workspace context for the core permission pipeline to inspect.
            # A restricted organization must still block creation while leaving
            # already existing personal workspaces untouched.
            from jadawel_billing.entitlements import get_effective_entitlements

            result = {}
            for check in checks:
                user = getattr(check.actor, "user", check.actor)
                if getattr(user, "is_staff", False):
                    result[check] = True
                    continue
                if check.operation_name != "create_workspace":
                    continue
                organizations = Organization.objects.filter(
                    memberships__user_id=getattr(user, "pk", None),
                    memberships__suspended=False,
                    status=Organization.Status.ACTIVE,
                ).values_list("billing_account_id", flat=True)
                if any(
                    get_effective_entitlements(account_id)["source"]
                    in {"restricted", "suspended"}
                    for account_id in organizations
                ):
                    result[check] = PermissionDenied(check.actor)
            return result
        organization = self._binding(workspace)
        if organization is None:
            return {}
        from jadawel_billing.entitlements import get_effective_entitlements

        source = get_effective_entitlements(organization.billing_account_id).get(
            "source"
        )
        restricted = source in {"restricted", "suspended"}
        result = {}
        for check in checks:
            if not self._allowed(check.actor, organization, workspace):
                result[check] = UserNotInWorkspace(check.actor, workspace)
            elif restricted and (
                source == "suspended"
                or not self.is_read_operation(check.operation_name)
            ):
                result[check] = PermissionDenied(check.actor)
        return result

    def get_permissions_object(self, actor, workspace=None):
        if workspace is None:
            return None
        organization = self._binding(workspace)
        if organization is None:
            return None
        from jadawel_billing.entitlements import get_effective_entitlements

        entitlements = get_effective_entitlements(organization.billing_account_id)
        return {
            "organization_id": str(organization.pk),
            "status": organization.status,
            "source": entitlements["source"],
            "read_operations": sorted(self.READ_OPERATIONS),
            "write_operations": sorted(self.WRITE_OPERATIONS),
        }

    def filter_queryset(self, actor, operation_name, queryset, workspace=None):
        if queryset.model.__name__ not in {"Workspace", "WorkspaceUser"}:
            return None
        if getattr(getattr(actor, "user", actor), "is_staff", False):
            return queryset
        actor_user_id = getattr(getattr(actor, "user", actor), "pk", None)
        if queryset.model.__name__ == "WorkspaceUser":
            queryset = queryset.filter(
                Q(workspace__organization_binding__isnull=True)
                | Q(
                    workspace__organization_binding__organization__memberships__user_id=actor_user_id,
                    workspace__organization_binding__organization__memberships__suspended=False,
                    workspace__organization_binding__organization__status=Organization.Status.ACTIVE,
                )
            )
        else:
            queryset = queryset.filter(
                Q(organization_binding__isnull=True)
                | Q(
                    organization_binding__organization__memberships__user_id=actor_user_id,
                    organization_binding__organization__memberships__suspended=False,
                    organization_binding__organization__status=Organization.Status.ACTIVE,
                )
            )
        return queryset.distinct()
