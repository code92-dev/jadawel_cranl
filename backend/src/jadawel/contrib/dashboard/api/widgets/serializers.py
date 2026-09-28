from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from jadawel.contrib.dashboard.widgets.models import Widget
from jadawel.contrib.dashboard.widgets.registries import widget_type_registry

APPEARANCE_MAX_KEYS = 16
APPEARANCE_MAX_STRING = 64


def validate_appearance(value):
    """
    Jadawel fork: `appearance` holds presentation options only the frontend
    interprets (accent colour, icon, number prefix…). The server does not know
    each widget's keys, so it bounds the shape instead: a flat dict of a few
    short scalar values, never markup or nested data.
    """

    if not isinstance(value, dict):
        raise serializers.ValidationError("Must be an object.")
    if len(value) > APPEARANCE_MAX_KEYS:
        raise serializers.ValidationError(
            f"At most {APPEARANCE_MAX_KEYS} appearance options."
        )
    for key, item in value.items():
        if not isinstance(key, str) or len(key) > 32:
            raise serializers.ValidationError(f"Invalid option name {key!r}.")
        if isinstance(item, str):
            if len(item) > APPEARANCE_MAX_STRING:
                raise serializers.ValidationError(
                    f"'{key}' is longer than {APPEARANCE_MAX_STRING} characters."
                )
        elif item is not None and not isinstance(item, (bool, int, float)):
            raise serializers.ValidationError(f"'{key}' must be a single value.")
    return value


class AppearanceField(serializers.JSONField):
    def __init__(self, **kwargs):
        kwargs.setdefault("validators", [validate_appearance])
        kwargs.setdefault(
            "help_text",
            "Presentation options such as the accent colour, icon and number format.",
        )
        super().__init__(**kwargs)


class WidgetSerializer(serializers.ModelSerializer):
    """
    Basic widget serializer mostly for returned values.
    """

    type = serializers.SerializerMethodField(help_text="The type of the widget.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return widget_type_registry.get_by_model(instance.specific_class).type

    class Meta:
        model = Widget
        fields = (
            "id",
            "title",
            "description",
            "dashboard_id",
            "type",
            "order",
            "width",
            "height",
            "appearance",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "title": {"read_only": True},
            "description": {"read_only": True},
            "dashboard_id": {"read_only": True},
            "type": {"read_only": True},
            "order": {"read_only": True, "help_text": "Lowest first."},
            "width": {"read_only": True},
            "height": {"read_only": True},
            "appearance": {"read_only": True},
        }


class CreateWidgetSerializer(serializers.ModelSerializer):
    """
    This serializer allow to set the type of the new widget.
    """

    type = serializers.ChoiceField(
        choices=lazy(widget_type_registry.get_types, list)(),
        required=True,
        help_text="The type of the widget.",
    )
    appearance = AppearanceField(required=False)

    class Meta:
        model = Widget
        fields = (
            "title",
            "description",
            "type",
            "width",
            "height",
            "appearance",
        )
        extra_kwargs = {
            "description": {"required": False, "allow_blank": True},
            "width": {"required": False},
            "height": {"required": False},
        }


class UpdateWidgetSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(
        choices=lazy(widget_type_registry.get_types, list)(),
        required=True,
        help_text="The type of the widget.",
    )
    order = serializers.DecimalField(
        max_digits=40,
        decimal_places=20,
        required=False,
        help_text="Indicates the position of the widget, lowest first and highest "
        "last.",
    )
    appearance = AppearanceField(required=False)

    class Meta:
        model = Widget
        fields = (
            "title",
            "description",
            "order",
            "width",
            "height",
            "appearance",
        )
        extra_kwargs = {
            "title": {"required": False, "allow_blank": False},
            "description": {"required": False, "allow_blank": True},
            "width": {"required": False},
            "height": {"required": False},
        }
