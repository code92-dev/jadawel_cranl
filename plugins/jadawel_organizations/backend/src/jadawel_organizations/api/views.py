from typing import Any
from uuid import UUID

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..handlers import (
    accept_invitation,
    add_member,
    assign_workspace_member,
    bind_workspace,
    change_organization_lifecycle,
    create_organization,
    create_pending_team,
    invite_member,
    organization_snapshot,
    reassign_owner_setup,
    resend_owner_setup,
    revoke_invitation,
    remove_member,
    unbind_workspace,
    update_member,
    workspace_binding_preview,
    transition_to_personal,
    update_organization,
)
from ..models import (
    Organization,
    OrganizationAuditEvent,
    OrganizationMembership,
    OrganizationWorkspace,
)
from .serializers import (
    AcceptInvitationSerializer,
    AddMemberSerializer,
    BindWorkspaceSerializer,
    CreateOrganizationSerializer,
    InvitationSerializer,
    InviteSerializer,
    LifecycleSerializer,
    MemberUpdateSerializer,
    MembershipSerializer,
    OrganizationSerializer,
    OrganizationWorkspaceSerializer,
    OrganizationUpdateSerializer,
    OwnerSetupSerializer,
    StartTeamSerializer,
    WorkspaceMemberAssignmentSerializer,
)


def get_org(organization_id: UUID) -> Organization:
    return get_object_or_404(
        Organization.objects.select_related("owner"), pk=organization_id
    )


def require_viewer(request: Request, organization: Organization) -> None:
    if request.user.is_staff:
        return
    if organization.status != Organization.Status.ACTIVE:
        raise ValidationError({"organization": "inactive"})
    if not OrganizationMembership.objects.filter(
        organization=organization, user=request.user, suspended=False
    ).exists():
        raise PermissionDenied("organization_membership_required")


class OrganizationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        organizations = (
            Organization.objects.filter(
                memberships__user=request.user, memberships__suspended=False
            )
            .distinct()
            .select_related("owner")
        )
        return Response([organization_snapshot(org) for org in organizations])


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        require_viewer(request, organization)
        payload = organization_snapshot(organization)
        payload["members"] = MembershipSerializer(
            organization.memberships.select_related("user").order_by("role", "id"),
            many=True,
        ).data
        payload["workspaces"] = OrganizationWorkspaceSerializer(
            organization.workspaces.select_related("workspace"), many=True
        ).data
        return Response(payload)

    def patch(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        serializer = OrganizationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = update_organization(
            request.user, organization, **serializer.validated_data
        )
        return Response(organization_snapshot(organization))


class AdminOrganizationListView(generics.ListAPIView[Any]):
    permission_classes = [IsAdminUser]
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.select_related("owner").annotate(
        members_count=Count("memberships", filter=Q(memberships__suspended=False))
    )


class AdminOrganizationCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request: Request) -> Response:
        serializer = CreateOrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = create_organization(request.user, **serializer.validated_data)
        owner_setup_token = getattr(organization, "_owner_setup_token", None)
        payload = organization_snapshot(organization)
        if owner_setup_token:
            payload["owner_setup_token"] = owner_setup_token
        return Response(payload, status=status.HTTP_201_CREATED)


class AdminOwnerSetupView(APIView):
    """Resend or reassign the restricted owner setup invitation."""

    permission_classes = [IsAdminUser]

    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        serializer = OwnerSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("email"):
            token = reassign_owner_setup(
                request.user, organization, serializer.validated_data["email"]
            )
        else:
            token = resend_owner_setup(request.user, organization)
        return Response({"owner_setup_token": token})


class StartTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = StartTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = create_pending_team(request.user, **serializer.validated_data)
        return Response(
            organization_snapshot(organization), status=status.HTTP_201_CREATED
        )


class MemberListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        require_viewer(request, organization)
        return Response(
            MembershipSerializer(
                organization.memberships.select_related("user"), many=True
            ).data
        )

    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = add_member(request.user, organization, **serializer.validated_data)
        return Response(MembershipSerializer(membership).data, status=201)


class MemberDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(
        self, request: Request, organization_id: UUID, membership_id: int
    ) -> Response:
        organization = get_org(organization_id)
        membership = get_object_or_404(
            OrganizationMembership.objects.select_related("user"), pk=membership_id
        )
        serializer = MemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = update_member(
            request.user, organization, membership, **serializer.validated_data
        )
        return Response(MembershipSerializer(member).data)

    def delete(
        self, request: Request, organization_id: UUID, membership_id: int
    ) -> Response:
        organization = get_org(organization_id)
        membership = get_object_or_404(OrganizationMembership, pk=membership_id)
        remove_member(request.user, organization, membership)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        require_viewer(request, organization)
        invitations = organization.invitations.order_by("-created_at")
        return Response(InvitationSerializer(invitations, many=True).data)

    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, token = invite_member(
            request.user, organization, **serializer.validated_data
        )
        data = InvitationSerializer(invitation).data
        data["token"] = token
        return Response(data, status=status.HTTP_201_CREATED)


class InvitationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(
        self, request: Request, organization_id: UUID, invitation_id: int
    ) -> Response:
        organization = get_org(organization_id)
        invitation = get_object_or_404(organization.invitations, pk=invitation_id)
        revoke_invitation(request.user, organization, invitation)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AcceptInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = accept_invitation(request.user, serializer.validated_data["token"])
        return Response(MembershipSerializer(membership).data)


class WorkspaceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        require_viewer(request, organization)
        return Response(
            OrganizationWorkspaceSerializer(
                organization.workspaces.select_related("workspace"), many=True
            ).data
        )


class WorkspaceBindView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        serializer = BindWorkspaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        binding = bind_workspace(
            request.user, organization, **serializer.validated_data
        )
        return Response(
            OrganizationWorkspaceSerializer(binding).data,
            status=status.HTTP_201_CREATED,
        )

    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        workspace_id = request.query_params.get("workspace")
        if not workspace_id:
            raise serializers.ValidationError({"workspace": "required"})
        from jadawel.core.models import Workspace

        workspace = get_object_or_404(Workspace, pk=workspace_id)
        return Response(
            workspace_binding_preview(request.user, organization, workspace)
        )


class WorkspaceBindingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(
        self, request: Request, organization_id: UUID, binding_id: int
    ) -> Response:
        organization = get_org(organization_id)
        binding = get_object_or_404(OrganizationWorkspace, pk=binding_id)
        unbind_workspace(request.user, organization, binding)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceMemberAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(
        self,
        request: Request,
        organization_id: UUID,
        binding_id: int,
        membership_id: int,
    ) -> Response:
        organization = get_org(organization_id)
        binding = get_object_or_404(OrganizationWorkspace, pk=binding_id)
        membership = get_object_or_404(OrganizationMembership, pk=membership_id)
        serializer = WorkspaceMemberAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assign_workspace_member(
            request.user,
            organization,
            binding,
            membership,
            **serializer.validated_data,
        )
        return Response({"assigned": True})


class LifecycleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        serializer = LifecycleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        organization = change_organization_lifecycle(
            request.user, organization, action=action
        )
        return Response(organization_snapshot(organization))


class TransitionToPersonalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = get_org(organization_id)
        personal = transition_to_personal(request.user, organization)
        return Response({"personal_billing_account": str(personal.pk)})


class AuditView(generics.ListAPIView[Any]):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    def get_queryset(self) -> Any:
        organization = get_org(self.kwargs["organization_id"])
        require_viewer(self.request, organization)
        return OrganizationAuditEvent.objects.filter(
            organization=organization
        ).order_by("-created_at")

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        rows = self.get_queryset().values(
            "id", "actor_id", "action", "target", "details", "created_at"
        )
        return Response(list(rows))
