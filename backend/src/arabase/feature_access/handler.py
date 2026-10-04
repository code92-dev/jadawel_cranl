"""Who may use automations, applications and Sanad (docs/FEATURE_ACCESS.md).

A user may use a feature when they are instance staff, when an administrator
opened it to everyone, or when their email address is granted it. Changes reach
signed-in users at once through the ``user_data_updated`` realtime event, under
the ``arabase_features`` key the login response carries.
"""

from typing import Iterable, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models.functions import Lower

from arabase.feature_access.exceptions import (
    FeatureAccessGrantDoesNotExist,
    FeatureNotGranted,
    UnknownFeature,
)
from arabase.feature_access.models import Feature, FeatureAccess, FeatureAccessGrant
from jadawel.core.user.utils import normalize_email_address

USER_DATA_KEY = "arabase_features"

User = get_user_model()


def get_feature(name: str) -> Feature:
    """:raises UnknownFeature: when no gated feature has this name."""

    try:
        return Feature(name)
    except ValueError:
        raise UnknownFeature(name)


def get_user_features(user: Optional[AbstractUser]) -> dict[str, bool]:
    """Every gated feature, and whether this user may use it."""

    if user is None or not user.is_authenticated:
        return {feature: False for feature in Feature.values}
    if user.is_staff:
        return {feature: True for feature in Feature.values}
    available = set(
        FeatureAccess.objects.filter(everyone=True).values_list("feature", flat=True)
    )
    available.update(
        FeatureAccessGrant.objects.filter(
            email=normalize_email_address(user.email)
        ).values_list("feature", flat=True)
    )
    return {feature: feature in available for feature in Feature.values}


def has_feature(user: Optional[AbstractUser], feature: str) -> bool:
    if user is None or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return (
        FeatureAccess.objects.filter(feature=feature, everyone=True).exists()
        or FeatureAccessGrant.objects.filter(
            feature=feature, email=normalize_email_address(user.email)
        ).exists()
    )


def check_feature(user: Optional[AbstractUser], feature: str) -> None:
    """:raises FeatureNotGranted: when the user may not use the feature."""

    if not has_feature(user, feature):
        raise FeatureNotGranted(feature)


def list_feature_access() -> list[dict]:
    """Each feature's setting and grants, for the admin settings page. A grant
    whose address has no account yet carries ``user: None``."""

    everyone = set(
        FeatureAccess.objects.filter(everyone=True).values_list("feature", flat=True)
    )
    grants = list(FeatureAccessGrant.objects.all())
    users = {
        user.email_lower: user
        for user in User.objects.annotate(email_lower=Lower("email")).filter(
            email_lower__in={grant.email for grant in grants}
        )
    }
    result = []
    for feature in Feature.values:
        result.append(
            {
                "feature": feature,
                "everyone": feature in everyone,
                "grants": [
                    {
                        "id": grant.id,
                        "email": grant.email,
                        "created_on": grant.created_on,
                        "user": _describe_user(users.get(grant.email)),
                    }
                    for grant in grants
                    if grant.feature == feature
                ],
            }
        )
    return result


def _describe_user(user: Optional[AbstractUser]) -> Optional[dict]:
    if user is None:
        return None
    return {
        "id": user.id,
        "name": user.first_name,
        "is_staff": user.is_staff,
        "is_active": user.is_active,
    }


def set_everyone(actor: AbstractUser, feature: str, everyone: bool) -> None:
    """Open a feature to every user, or limit it to staff and its grants."""

    feature = get_feature(feature)
    with transaction.atomic():
        access, _ = FeatureAccess.objects.select_for_update().get_or_create(
            feature=feature
        )
        changed = access.everyone != everyone
        access.everyone = everyone
        access.updated_by = actor
        access.save()
    if changed:
        transaction.on_commit(lambda: _announce_everyone(feature, everyone))


def add_grants(actor: AbstractUser, feature: str, emails: Iterable[str]) -> list[str]:
    """Grant a feature to email addresses; returns the newly granted ones.

    An address already granted is left as it was.
    """

    feature = get_feature(feature)
    normalized = list(dict.fromkeys(normalize_email_address(e) for e in emails))
    with transaction.atomic():
        existing = set(
            FeatureAccessGrant.objects.filter(
                feature=feature, email__in=normalized
            ).values_list("email", flat=True)
        )
        new = [email for email in normalized if email not in existing]
        FeatureAccessGrant.objects.bulk_create(
            [
                FeatureAccessGrant(feature=feature, email=email, granted_by=actor)
                for email in new
            ],
            ignore_conflicts=True,
        )
    if new:
        transaction.on_commit(lambda: _announce_grants(feature, new, True))
    return new


def remove_grant(feature: str, grant_id: int) -> None:
    """:raises FeatureAccessGrantDoesNotExist: for a missing grant, or one of
    another feature."""

    feature = get_feature(feature)
    with transaction.atomic():
        try:
            grant = FeatureAccessGrant.objects.select_for_update().get(
                id=grant_id, feature=feature
            )
        except FeatureAccessGrant.DoesNotExist:
            raise FeatureAccessGrantDoesNotExist()
        email = grant.email
        grant.delete()
    transaction.on_commit(lambda: _announce_grants(feature, [email], False))


def _broadcast(user_ids: list[int], feature: str, value: bool, to_all=False):
    from jadawel.api.user.registries import UserDataType
    from jadawel.ws.tasks import broadcast_to_users

    if not user_ids and not to_all:
        return
    payload = UserDataType.realtime_message_to_update_user_data(
        {USER_DATA_KEY: {feature: value}}
    )
    broadcast_to_users.delay(user_ids, payload, send_to_all_users=to_all)


def _announce_everyone(feature: str, everyone: bool) -> None:
    if everyone:
        _broadcast([], feature, True, to_all=True)
        return
    # Only users left with neither staff status nor a grant lose the feature.
    granted = FeatureAccessGrant.objects.filter(feature=feature).values("email")
    user_ids = list(
        User.objects.annotate(email_lower=Lower("email"))
        .filter(is_staff=False, is_active=True)
        .exclude(email_lower__in=granted)
        .values_list("id", flat=True)
    )
    _broadcast(user_ids, feature, False)


def _announce_grants(feature: str, emails: list[str], granted: bool) -> None:
    if FeatureAccess.objects.filter(feature=feature, everyone=True).exists():
        return
    user_ids = list(
        User.objects.annotate(email_lower=Lower("email"))
        .filter(email_lower__in=emails, is_staff=False, is_active=True)
        .values_list("id", flat=True)
    )
    _broadcast(user_ids, feature, granted)


APPLICATION_TYPE_FEATURES = {
    Feature.AUTOMATION.value: Feature.AUTOMATION,
    Feature.BUILDER.value: Feature.BUILDER,
}


def refuse_ungranted_application(sender, user, workspace, type_name, **kwargs):
    """Receiver of core's ``before_application_created``: an automation or an
    application is only created for someone who may use that feature.

    Existing ones stay with the workspace's members, whoever made them.
    """

    feature = APPLICATION_TYPE_FEATURES.get(type_name)
    if feature is not None and user is not None:
        check_feature(user, feature)


def connect_feature_access_signals() -> None:
    from jadawel.core.signals import before_application_created

    before_application_created.connect(
        refuse_ungranted_application,
        dispatch_uid="arabase_refuse_ungranted_application",
    )
