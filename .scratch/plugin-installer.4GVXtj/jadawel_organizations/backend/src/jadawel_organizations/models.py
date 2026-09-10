import hashlib
import uuid

from django.conf import settings
from django.db import models


class Organization(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active"
        SUSPENDED = "suspended"
        ARCHIVED = "archived"

    class ProvisioningStatus(models.TextChoices):
        READY = "ready"
        PENDING = "pending"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    billing_account = models.OneToOneField(
        "jadawel_billing.BillingAccount",
        on_delete=models.PROTECT,
        related_name="organization",
    )
    name = models.CharField(max_length=160)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="owned_organizations",
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.ACTIVE
    )
    provisioning_status = models.CharField(
        max_length=12,
        choices=ProvisioningStatus.choices,
        default=ProvisioningStatus.READY,
    )
    provisioning_error = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
    )
    creation_key = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner"
        ADMIN = "admin"
        MEMBER = "member"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    suspended = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="organizations_unique_member"
            ),
            models.UniqueConstraint(
                fields=["organization"],
                condition=models.Q(role="owner"),
                name="organizations_one_owner",
            ),
        ]


class OrganizationInvitation(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organization_invitations_sent",
    )
    role = models.CharField(
        max_length=10, choices=OrganizationMembership.Role.choices, default="member"
    )
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                condition=models.Q(accepted_at__isnull=True, revoked_at__isnull=True),
                name="organizations_one_pending_invite_email",
            )
        ]

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


class OrganizationWorkspace(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="workspaces"
    )
    workspace = models.OneToOneField(
        "core.Workspace",
        on_delete=models.PROTECT,
        related_name="organization_binding",
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organization_workspaces_added",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    managed_user_ids = models.JSONField(default=list)
    managed_user_permissions = models.JSONField(default=dict)


class OrganizationWorkspaceAccess(models.Model):
    binding = models.ForeignKey(
        OrganizationWorkspace, on_delete=models.CASCADE, related_name="member_access"
    )
    membership = models.ForeignKey(
        OrganizationMembership,
        on_delete=models.CASCADE,
        related_name="workspace_access",
    )
    permissions = models.CharField(max_length=10, default="MEMBER")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["binding", "membership"],
                name="organizations_unique_workspace_access",
            )
        ]


class OrganizationAuditEvent(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="audit_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=60)
    target = models.CharField(max_length=80)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
