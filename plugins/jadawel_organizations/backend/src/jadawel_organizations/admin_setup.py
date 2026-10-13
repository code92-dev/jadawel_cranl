"""One-step organization setup for the general administrator.

Creates the organization, its owner, its members and an optional managed
workspace in one transaction, with no invitation to accept. People whose email
has no account yet get one with a generated password that is returned once to
the administrator, who hands it over.

Builds on provisioning.py, members.py and workspace_access.py.
"""

import secrets
from dataclasses import dataclass, field
from typing import Any, Iterable
from uuid import UUID

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Q

from rest_framework.exceptions import PermissionDenied, ValidationError

from jadawel.core.models import Workspace
from jadawel.core.signals import workspace_created
from jadawel.core.user.handler import UserHandler
from jadawel.core.user.utils import normalize_email_address

from .access import User, _require_actor, audit
from .members import add_member
from .models import Organization, OrganizationMembership
from .provisioning import create_organization
from .workspace_access import assign_workspace_member, bind_workspace

MEMBER_ROLES = {OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.MEMBER}
DEFAULT_GRANT_REASON = "One-step organization setup by the general administrator"


@dataclass
class OrganizationSetup:
    organization: Organization
    workspace: Workspace | None = None
    # Only accounts created by this request; a replay returns none because the
    # passwords are never stored in clear text.
    credentials: list[dict[str, str]] = field(default_factory=list)


def _generate_password() -> str:
    password = secrets.token_urlsafe(12)
    validate_password(password)
    return password


def _get_or_create_user(email: str, name: str) -> tuple[Any, str | None]:
    """Return the account for an email, creating it when there is none."""
    user = User.objects.filter(
        Q(email__iexact=email) | Q(username__iexact=email)
    ).first()
    if user is not None:
        if not user.is_active:
            raise ValidationError({"email": f"inactive:{email}"})
        return user, None
    password = _generate_password()
    user = UserHandler().force_create_user(
        email=email, name=name or email.split("@")[0], password=password
    )
    # The general administrator vouches for the address, so an instance that
    # enforces email verification still lets the person sign in.
    user.profile.email_verified = True
    user.profile.save(update_fields=["email_verified"])
    return user, password


def _normalized_members(
    owner_email: str, members: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    seen = {owner_email}
    result = []
    for member in members:
        email = normalize_email_address(member["email"])
        role = member.get("role") or OrganizationMembership.Role.MEMBER
        if role not in MEMBER_ROLES:
            raise ValidationError({"role": f"invalid:{email}"})
        if email in seen:
            raise ValidationError({"members": f"duplicate_email:{email}"})
        seen.add(email)
        result.append({"email": email, "name": member.get("name", ""), "role": role})
    return result


@transaction.atomic
def setup_organization(
    actor: Any,
    *,
    name: str,
    owner_email: str,
    plan: Any,
    owner_name: str = "",
    members: Iterable[dict[str, Any]] = (),
    seat_limit: int | None = None,
    expires_at: Any | None = None,
    reason: str = "",
    create_workspace: bool = True,
    creation_key: UUID | None = None,
) -> OrganizationSetup:
    _require_actor(actor)
    if not actor.is_staff:
        raise PermissionDenied("general_admin_required")
    if creation_key:
        existing = Organization.objects.filter(creation_key=creation_key).first()
        if existing is not None:
            if existing.created_by_id != actor.pk:
                raise ValidationError({"creation_key": "already_used"})
            binding = existing.workspaces.select_related("workspace").first()
            return OrganizationSetup(existing, binding.workspace if binding else None)

    owner_email = normalize_email_address(owner_email)
    members = _normalized_members(owner_email, members)
    credentials = []

    owner, password = _get_or_create_user(owner_email, owner_name)
    if password:
        credentials.append({"email": owner_email, "password": password})
    member_users = []
    for member in members:
        user, password = _get_or_create_user(member["email"], member["name"])
        if password:
            credentials.append({"email": member["email"], "password": password})
        member_users.append((user, member["role"]))

    # Size the complimentary grant so every member fits; a smaller cap would
    # fail the additions below for capacity.
    seat_limit = max(seat_limit or 0, 1 + len(member_users))
    organization = create_organization(
        actor,
        name=name,
        owner=owner,
        creation_key=creation_key,
        plan=plan,
        seat_limit=seat_limit,
        expires_at=expires_at,
        reason=reason.strip() or DEFAULT_GRANT_REASON,
    )
    memberships = [
        add_member(actor, organization, user=user, role=role)
        for user, role in member_users
    ]

    workspace = None
    if create_workspace:
        workspace = Workspace.objects.create(name=organization.name)
        # The owner is given workspace administration while binding.
        binding = bind_workspace(actor, organization, workspace)
        for membership in memberships:
            assign_workspace_member(actor, organization, binding, membership)
        workspace_created.send(None, workspace=workspace, user=actor)

    audit(
        actor,
        organization,
        "organization.setup_completed",
        organization.pk,
        {
            "members": len(memberships),
            "accounts_created": [item["email"] for item in credentials],
            "workspace": workspace.pk if workspace else None,
        },
    )
    return OrganizationSetup(organization, workspace, credentials)
