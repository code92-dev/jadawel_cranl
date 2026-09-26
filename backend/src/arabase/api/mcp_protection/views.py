from django.db import transaction
from django.db.models import (
    Count,
    Exists,
    OuterRef,
    Prefetch,
    Q,
    prefetch_related_objects,
)

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from arabase.api.mcp_protection.serializers import (
    CreatedProtectedMCPEndpointSerializer,
    CreateProtectedMCPEndpointSerializer,
    MCPEndpointProtectionSummarySerializer,
    MCPProtectionPolicySerializer,
    ReactivateMCPProtectionPolicySerializer,
    UpdateMCPProtectionPolicySerializer,
)
from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionLifecycleStatus,
    MCPProtectionPolicy,
)
from arabase.mcp.protection.policy_commands import (
    MCPProtectionPolicyConflict,
    MCPProtectionPolicyNotReady,
    create_protected_mcp_endpoint,
    delete_ownerless_suspended_endpoint,
    reactivate_mcp_protection_policy,
    replace_mcp_protection_policy,
    validate_idempotency_key,
)
from arabase.mcp.protection.readiness import (
    MCPProtectionVaultNotReady,
    check_mcp_protection_policy_readiness,
)
from jadawel.api.decorators import map_exceptions, validate_body
from jadawel.api.errors import ERROR_GROUP_DOES_NOT_EXIST, ERROR_USER_NOT_IN_GROUP
from jadawel.api.mcp.errors import (
    ERROR_MAXIMUM_UNIQUE_ENDPOINT_TRIES,
    ERROR_MCP_ENDPOINT_DOES_NOT_EXIST,
)
from jadawel.api.schemas import get_error_schema
from jadawel.contrib.database.fields.operations import ReadFieldOperationType
from jadawel.core.exceptions import (
    PermissionException,
    UserNotInWorkspace,
    WorkspaceDoesNotExist,
)
from jadawel.core.handler import CoreHandler
from jadawel.core.mcp.exceptions import (
    MaximumUniqueEndpointTriesError,
    MCPEndpointDoesNotExist,
)
from jadawel.core.mcp.handler import MCPEndpointHandler
from jadawel.core.mcp.models import MCPEndpoint
from jadawel.core.models import WORKSPACE_USER_PERMISSION_ADMIN, WorkspaceUser

ERROR_MCP_PROTECTION_NOT_READY = (
    "ERROR_MCP_PROTECTION_NOT_READY",
    HTTP_400_BAD_REQUEST,
    "Field protection is not ready on this server ({e.safe_reason_code}), so no "
    "field was protected. An administrator can see the cause at "
    "/api/arabase/mcp/protection/readiness/.",
)


def _may_display_field_metadata(user, field) -> bool:
    try:
        CoreHandler().check_permissions(
            user,
            ReadFieldOperationType.type,
            workspace=field.table.database.workspace,
            context=field,
        )
    except PermissionException:
        return False
    return True


def _policy_response(user, policy: MCPProtectionPolicy) -> Response:
    """Serialize ``policy`` with the field metadata ``user`` may see."""

    prefetch_related_objects(
        [policy],
        Prefetch(
            "protected_fields",
            queryset=MCPProtectedField.objects.select_related(
                "field__table__database__workspace"
            ),
        ),
    )
    display_field_ids = {
        relation.field_id
        for relation in policy.protected_fields.all()
        if _may_display_field_metadata(user, relation.field)
    }
    return Response(
        MCPProtectionPolicySerializer(
            policy, context={"display_field_ids": display_field_ids}
        ).data
    )


class MCPProtectionPolicyView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Arabase MCP protection"],
        operation_id="get_mcp_protection_policy",
        responses={
            200: MCPProtectionPolicySerializer,
            404: get_error_schema(["ERROR_MCP_ENDPOINT_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions({MCPEndpointDoesNotExist: ERROR_MCP_ENDPOINT_DOES_NOT_EXIST})
    def get(self, request: Request, endpoint_id: int) -> Response:
        endpoint = MCPEndpointHandler().get_endpoint(request.user, endpoint_id)
        policy = MCPProtectionPolicy.objects.get(endpoint=endpoint)
        return _policy_response(request.user, policy)

    @extend_schema(
        tags=["Arabase MCP protection"],
        operation_id="replace_mcp_protection_policy",
        request=UpdateMCPProtectionPolicySerializer,
        responses={
            200: MCPProtectionPolicySerializer,
            404: get_error_schema(["ERROR_MCP_ENDPOINT_DOES_NOT_EXIST"]),
        },
    )
    @validate_body(UpdateMCPProtectionPolicySerializer)
    @map_exceptions(
        {
            MCPEndpointDoesNotExist: ERROR_MCP_ENDPOINT_DOES_NOT_EXIST,
            MCPProtectionPolicyConflict: ("MCP_PROTECTION_REVISION_CONFLICT", 409),
            MCPProtectionVaultNotReady: ERROR_MCP_PROTECTION_NOT_READY,
        }
    )
    def patch(self, request: Request, endpoint_id: int, data: dict) -> Response:
        idempotency_key = validate_idempotency_key(
            request.headers.get("Idempotency-Key")
        )
        result = replace_mcp_protection_policy(
            user=request.user,
            endpoint_id=endpoint_id,
            idempotency_key=idempotency_key,
            **data,
        )
        return _policy_response(request.user, result.policy)

    # The policy is a full-set replacement; keep PATCH for existing clients and
    # accept PUT for clients that model replacement semantics explicitly.
    put = patch

    @extend_schema(
        tags=["Arabase MCP protection"],
        operation_id="reactivate_mcp_protection_policy",
        request=ReactivateMCPProtectionPolicySerializer,
        responses={
            200: MCPProtectionPolicySerializer,
            404: get_error_schema(["ERROR_MCP_ENDPOINT_DOES_NOT_EXIST"]),
        },
    )
    @validate_body(ReactivateMCPProtectionPolicySerializer)
    @map_exceptions(
        {
            MCPEndpointDoesNotExist: ERROR_MCP_ENDPOINT_DOES_NOT_EXIST,
            MCPProtectionPolicyConflict: ("MCP_PROTECTION_REVISION_CONFLICT", 409),
            MCPProtectionPolicyNotReady: ("MCP_PROTECTION_NOT_READY", 409),
        }
    )
    def post(self, request: Request, endpoint_id: int, data: dict) -> Response:
        policy = reactivate_mcp_protection_policy(
            user=request.user, endpoint_id=endpoint_id, **data
        )
        return _policy_response(request.user, policy)

    @extend_schema(
        tags=["Arabase MCP protection"],
        operation_id="delete_ownerless_mcp_endpoint",
        description=(
            "Allows a workspace administrator to delete only an ownerless "
            "suspended or protection-blocked endpoint."
        ),
        responses={
            204: None,
            404: get_error_schema(["ERROR_MCP_ENDPOINT_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions({MCPEndpointDoesNotExist: ERROR_MCP_ENDPOINT_DOES_NOT_EXIST})
    @transaction.atomic
    def delete(self, request: Request, endpoint_id: int) -> Response:
        delete_ownerless_suspended_endpoint(
            user=request.user,
            endpoint_id=endpoint_id,
        )
        return Response(status=204)


class MCPProtectionReadinessView(APIView):
    """Public, content-blind readiness probe for the protected-value boundary."""

    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Arabase MCP protection"],
        operation_id="mcp_protection_readiness",
        responses={200: dict, 503: dict},
    )
    def get(self, request: Request) -> Response:
        readiness = check_mcp_protection_policy_readiness()
        payload = {"ready": readiness.ready, "reason": readiness.safe_reason_code}
        return Response(
            payload,
            status=status.HTTP_200_OK
            if readiness.ready
            else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class MCPEndpointProtectionSummariesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Arabase MCP protection"],
        operation_id="list_mcp_endpoint_protection_summaries",
        responses={200: MCPEndpointProtectionSummarySerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        # Owners see their own endpoints. Workspace administrators additionally
        # receive the content-blind status/count projection for suspended or
        # blocked endpoints in their workspaces, which is all the cleanup path
        # needs and never includes a key or protected value.
        admin_workspace_ids = WorkspaceUser.objects.filter(
            user=request.user,
            permissions=WORKSPACE_USER_PERMISSION_ADMIN,
        ).values_list("workspace_id", flat=True)
        active_owner_membership = WorkspaceUser.objects.filter(
            user_id=OuterRef("user_id"),
            workspace_id=OuterRef("workspace_id"),
        )
        endpoints = (
            MCPEndpoint.objects.filter(
                Q(user=request.user)
                | Q(
                    workspace_id__in=admin_workspace_ids,
                    arabase_protection_policy__lifecycle_status__in=(
                        MCPProtectionLifecycleStatus.SUSPENDED,
                        MCPProtectionLifecycleStatus.PROTECTION_BLOCKED,
                    ),
                )
                & (
                    Q(user__is_active=False)
                    | Q(user__profile__to_be_deleted=True)
                    | ~Exists(active_owner_membership)
                )
            )
            .select_related("workspace", "arabase_protection_policy")
            .annotate(
                protected_field_count=Count(
                    "arabase_protection_policy__protected_fields",
                    filter=Q(
                        arabase_protection_policy__protected_fields__state=MCPProtectedFieldState.ACTIVE
                    ),
                )
            )
        )
        return Response(
            MCPEndpointProtectionSummarySerializer(endpoints, many=True).data
        )

    @extend_schema(
        tags=["Arabase MCP protection"],
        operation_id="create_protected_mcp_endpoint",
        request=CreateProtectedMCPEndpointSerializer,
        responses={201: CreatedProtectedMCPEndpointSerializer},
    )
    @validate_body(CreateProtectedMCPEndpointSerializer)
    @map_exceptions(
        {
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            WorkspaceDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            MaximumUniqueEndpointTriesError: ERROR_MAXIMUM_UNIQUE_ENDPOINT_TRIES,
            MCPProtectionVaultNotReady: ERROR_MCP_PROTECTION_NOT_READY,
        }
    )
    def post(self, request: Request, data: dict) -> Response:
        idempotency_key = validate_idempotency_key(
            request.headers.get("Idempotency-Key")
        )
        result = create_protected_mcp_endpoint(
            user=request.user,
            idempotency_key=idempotency_key,
            **data,
        )
        policy = result.endpoint.arabase_protection_policy
        display_field_ids = {
            relation.field_id for relation in policy.protected_fields.all()
        }
        body = CreatedProtectedMCPEndpointSerializer(
            result.endpoint,
            context={"display_field_ids": display_field_ids},
        ).data
        return Response(body, status=201)
