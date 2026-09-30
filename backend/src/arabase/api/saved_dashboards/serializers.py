from rest_framework import serializers

from arabase.saved_dashboards.handler import Status
from arabase.saved_dashboards.models import SavedDashboardSource


class SavedDashboardSerializer(serializers.Serializer):
    """A card on the user's "My dashboards" page."""

    id = serializers.IntegerField(source="saved.id")
    source = serializers.ChoiceField(
        source="saved.source", choices=SavedDashboardSource.choices
    )
    title = serializers.CharField(source="saved.title")
    preview = serializers.JSONField(
        source="saved.preview", help_text="`[{type, width, height}]` per widget."
    )
    status = serializers.ChoiceField(
        choices=[Status.OK, Status.PASSWORD, Status.UNAVAILABLE, Status.UNREACHABLE],
        help_text="Whether the dashboard can be opened now, and if not, why.",
    )
    source_name = serializers.CharField(
        help_text="The workspace's name, the other server's host, or empty."
    )
    dashboard_id = serializers.IntegerField(
        source="saved.dashboard_id",
        allow_null=True,
        help_text="`workspace` only: to open the dashboard in its workspace.",
    )


class AddWorkspaceDashboardSerializer(serializers.Serializer):
    dashboard_id = serializers.IntegerField()


class AddDashboardLinkSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=2000, trim_whitespace=True)
    # Not length-checked, as on the public link's own password prompt: this is
    # the guess, not the policy.
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=256,
        trim_whitespace=False,
        default="",
    )


class SavedDashboardPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=256, trim_whitespace=False)


class OrderSavedDashboardsSerializer(serializers.Serializer):
    saved_dashboard_ids = serializers.ListField(
        child=serializers.IntegerField(), max_length=1000
    )


class AvailableDashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    saved = serializers.BooleanField(help_text="Already on the user's page.")


class AvailableWorkspaceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    dashboards = AvailableDashboardSerializer(many=True)
