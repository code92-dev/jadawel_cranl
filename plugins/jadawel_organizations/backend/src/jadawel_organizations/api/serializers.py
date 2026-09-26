from typing import Any

from django.contrib.auth import get_user_model

from jadawel_billing.entitlements import get_effective_entitlements
from jadawel_billing.models import Plan, Subscription
from rest_framework import serializers

from jadawel.core.models import Workspace

from ..models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationWorkspace,
)


class OrganizationSerializer(serializers.ModelSerializer[Any]):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    effective_source = serializers.SerializerMethodField()
    effective_seat_limit = serializers.SerializerMethodField()
    pending_owner_email = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    subscription_period_end = serializers.SerializerMethodField()
    subscription_cancel_at_period_end = serializers.SerializerMethodField()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Several fields read the same entitlements and subscription, so each is
        # read once per organization. With many=True this child instance is
        # shared by every row of the page.
        self._effective_by_pk: dict[Any, dict[str, Any]] = {}
        self._subscription_by_pk: dict[Any, Any] = {}

    def _effective(self, organization: Organization) -> dict[str, Any]:
        if organization.pk not in self._effective_by_pk:
            self._effective_by_pk[organization.pk] = get_effective_entitlements(
                organization.billing_account_id
            )
        return self._effective_by_pk[organization.pk]

    def get_effective_source(self, organization: Organization) -> str:
        return self._effective(organization)["source"]

    def get_effective_seat_limit(self, organization: Organization) -> int:
        return self._effective(organization)["seat_limit"]

    def get_pending_owner_email(self, organization: Organization) -> str | None:
        invitation = organization.invitations.filter(
            role=OrganizationMembership.Role.OWNER,
            accepted_at__isnull=True,
            revoked_at__isnull=True,
        ).first()
        return invitation.email if invitation else None

    def _subscription(self, organization: Organization):
        if organization.pk not in self._subscription_by_pk:
            self._subscription_by_pk[organization.pk] = (
                Subscription.objects.filter(account_id=organization.billing_account_id)
                .order_by("-period_start", "-id")
                .first()
            )
        return self._subscription_by_pk[organization.pk]

    def get_subscription_status(self, organization: Organization) -> str | None:
        subscription = self._subscription(organization)
        return subscription.status if subscription else None

    def get_subscription_period_end(self, organization: Organization):
        subscription = self._subscription(organization)
        return subscription.period_end if subscription else None

    def get_subscription_cancel_at_period_end(
        self, organization: Organization
    ) -> bool | None:
        subscription = self._subscription(organization)
        return subscription.cancel_at_period_end if subscription else None

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "status",
            "provisioning_status",
            "owner",
            "owner_email",
            "pending_owner_email",
            "billing_account",
            "members_count",
            "effective_source",
            "effective_seat_limit",
            "subscription_status",
            "subscription_period_end",
            "subscription_cancel_at_period_end",
            "created_at",
        ]
        read_only_fields = fields


class CreateOrganizationSerializer(serializers.Serializer[Any]):
    name = serializers.CharField(max_length=160)
    owner = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    owner_email = serializers.EmailField(required=False, allow_blank=False)
    creation_key = serializers.UUIDField(required=False, allow_null=True)
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(kind="TEAM"), required=False, allow_null=True
    )
    seat_limit = serializers.IntegerField(min_value=1, max_value=100000, required=False)
    starts_at = serializers.DateTimeField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate(self, attrs: Any) -> Any:
        if bool(attrs.get("owner")) == bool(attrs.get("owner_email")):
            raise serializers.ValidationError({"owner": "choose_id_or_email"})
        if attrs.get("plan") is not None:
            if "seat_limit" not in attrs:
                raise serializers.ValidationError({"seat_limit": "required_with_plan"})
            if not attrs.get("reason", "").strip():
                raise serializers.ValidationError({"reason": "required_with_plan"})
        elif any(
            key in attrs for key in ("seat_limit", "starts_at", "expires_at", "reason")
        ):
            raise serializers.ValidationError({"plan": "required_with_access_fields"})
        if (
            attrs.get("starts_at")
            and attrs.get("expires_at")
            and attrs["expires_at"] <= attrs["starts_at"]
        ):
            raise serializers.ValidationError({"expires_at": "must_follow_start"})
        return attrs


class StartTeamSerializer(serializers.Serializer[Any]):
    name = serializers.CharField(max_length=160)
    # A client can retry a failed response without creating a second Team
    # account.  The same key is also accepted through the Idempotency-Key
    # header by StartTeamView.
    creation_key = serializers.UUIDField(required=False, allow_null=True)


class OrganizationUpdateSerializer(serializers.Serializer[Any]):
    name = serializers.CharField(max_length=160)


class MembershipSerializer(serializers.ModelSerializer[Any]):
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ["id", "user", "email", "name", "role", "suspended", "joined_at"]
        read_only_fields = ["id", "user", "email", "name", "joined_at"]


class InvitationSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = OrganizationInvitation
        fields = [
            "id",
            "email",
            "role",
            "expires_at",
            "accepted_at",
            "revoked_at",
            "created_at",
        ]
        read_only_fields = fields


class InviteSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=["admin", "member"], default="member")


class AddMemberSerializer(serializers.Serializer[Any]):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_active=True)
    )
    role = serializers.ChoiceField(choices=["admin", "member"], default="member")


class AcceptInvitationSerializer(serializers.Serializer[Any]):
    token = serializers.CharField(min_length=20, max_length=200)


class WorkspaceSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = Workspace
        fields = ["id", "name"]
        read_only_fields = fields


class OrganizationWorkspaceSerializer(serializers.ModelSerializer[Any]):
    workspace = WorkspaceSerializer(read_only=True)
    assigned_members = serializers.IntegerField(
        source="member_access.count", read_only=True
    )
    assignments = serializers.SerializerMethodField()

    def get_assignments(self, binding: OrganizationWorkspace) -> list[dict[str, Any]]:
        return [
            {
                "membership_id": access.membership_id,
                "email": access.membership.user.email,
                "permissions": access.permissions,
            }
            for access in binding.member_access.select_related(
                "membership__user"
            ).order_by("id")
        ]

    class Meta:
        model = OrganizationWorkspace
        fields = ["id", "workspace", "assigned_members", "assignments", "created_at"]
        read_only_fields = fields


class BindWorkspaceSerializer(serializers.Serializer[Any]):
    workspace = serializers.PrimaryKeyRelatedField(queryset=Workspace.objects.all())
    confirm_outsiders = serializers.BooleanField(required=False, default=False)


class WorkspaceMemberAssignmentSerializer(serializers.Serializer[Any]):
    permissions = serializers.ChoiceField(
        choices=["ADMIN", "MEMBER", "VIEWER"], required=False
    )


class MemberUpdateSerializer(serializers.Serializer[Any]):
    role = serializers.ChoiceField(choices=["owner", "admin", "member"], required=False)
    suspended = serializers.BooleanField(required=False)


class LifecycleSerializer(serializers.Serializer[Any]):
    action = serializers.ChoiceField(choices=["suspend", "reactivate", "archive"])


class OwnerSetupSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField(required=False, allow_blank=False)
