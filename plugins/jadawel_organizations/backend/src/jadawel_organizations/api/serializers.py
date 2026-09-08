from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from jadawel.core.models import Workspace
from jadawel_billing.models import Plan

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

    def _effective(self, organization: Organization) -> dict[str, Any]:
        from jadawel_billing.entitlements import get_effective_entitlements

        return get_effective_entitlements(organization.billing_account_id)

    def get_effective_source(self, organization: Organization) -> str:
        return self._effective(organization)["source"]

    def get_effective_seat_limit(self, organization: Organization) -> int:
        return self._effective(organization)["seat_limit"]

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "status",
            "provisioning_status",
            "owner",
            "owner_email",
            "billing_account",
            "members_count",
            "effective_source",
            "effective_seat_limit",
            "created_at",
        ]
        read_only_fields = fields


class CreateOrganizationSerializer(serializers.Serializer[Any]):
    name = serializers.CharField(max_length=160)
    owner = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_active=True)
    )
    creation_key = serializers.UUIDField(required=False, allow_null=True)
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(kind="TEAM"), required=False, allow_null=True
    )
    seat_limit = serializers.IntegerField(min_value=1, max_value=100000, required=False)
    starts_at = serializers.DateTimeField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate(self, attrs: Any) -> Any:
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

    class Meta:
        model = OrganizationWorkspace
        fields = ["id", "workspace", "assigned_members", "created_at"]
        read_only_fields = fields


class BindWorkspaceSerializer(serializers.Serializer[Any]):
    workspace = serializers.PrimaryKeyRelatedField(queryset=Workspace.objects.all())


class MemberUpdateSerializer(serializers.Serializer[Any]):
    role = serializers.ChoiceField(choices=["owner", "admin", "member"], required=False)
    suspended = serializers.BooleanField(required=False)


class LifecycleSerializer(serializers.Serializer[Any]):
    action = serializers.ChoiceField(choices=["suspend", "reactivate", "archive"])
