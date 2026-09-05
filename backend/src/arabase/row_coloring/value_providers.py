from typing import Any, Dict, List, Union

from rest_framework import serializers

from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.fields.registries import field_type_registry
from jadawel.contrib.database.views.exceptions import (
    DecoratorValueProviderTypeNotCompatible,
)
from jadawel.contrib.database.views.models import ViewDecoration
from jadawel.contrib.database.views.registries import (
    DecoratorValueProviderType,
    view_filter_type_registry,
)

SINGLE_SELECT_FIELD_TYPE = "single_select"
COLOR_NAME_PATTERN = r"^[a-z-]+$"
FILTER_OPERATORS = ("AND", "OR")


class SingleSelectColorConfSerializer(serializers.Serializer):
    field_id = serializers.IntegerField(required=True)


def get_single_select_field_or_raise(view, conf) -> Field:
    """Resolve and validate the configured field for a view.

    Raises the compatibility error (mapped to 400 on both the create and
    update decoration endpoints) when the configuration points at a field
    that does not exist, lives on another table, or is not a single select.
    """
    field_id = (conf or {}).get("field_id")
    try:
        field = Field.objects.select_related("table").get(pk=field_id)
    except (Field.DoesNotExist, TypeError, ValueError):
        raise DecoratorValueProviderTypeNotCompatible(
            "The single select color configuration must reference a field."
        )
    if field.table_id != view.table_id:
        raise DecoratorValueProviderTypeNotCompatible(
            "The coloring field must belong to the view's table."
        )
    if (
        field_type_registry.get_by_model(field.specific_class).type
        != SINGLE_SELECT_FIELD_TYPE
    ):
        raise DecoratorValueProviderTypeNotCompatible(
            "Row coloring by option only supports single select fields."
        )
    return field


class SingleSelectColorValueProviderType(DecoratorValueProviderType):
    """Colors a row from the color of its single select option.

    OSS re-implementation of upstream's premium `single_select_color`
    provider. The configuration is `{"field_id": <id>}` — the same shape
    upstream used (see the Airtable import mapping) — and the color itself
    is resolved client-side from the already-loaded row value, so no extra
    query is needed per row.

    Note: core's create/update hooks receive the view but not the incoming
    configuration, so shape validation lives in the conf serializer above
    while field semantics are enforced when a stored configuration is
    adopted (update) and via the field lifecycle hooks below. A stale
    reference stays inert client-side: rows simply get no color.
    """

    type = "single_select_color"
    compatible_decorator_types = ["background_color", "left_border_color"]
    value_provider_conf_serializer_class = SingleSelectColorConfSerializer

    def before_update_decoration(self, view_decoration, user):
        conf = view_decoration.value_provider_conf or {}
        if not conf:
            return
        get_single_select_field_or_raise(view_decoration.view, conf)

    def set_import_serialized_value(
        self, value: Dict[str, Any], id_mapping: Dict[str, Dict[int, Any]]
    ) -> Dict[str, Any]:
        conf = value.get("value_provider_conf") or {}
        old_field_id = conf.get("field_id")
        new_field_id = id_mapping.get("database_fields", {}).get(old_field_id)
        # A field that was not imported must not keep pointing at a stale id
        # that could belong to another field in the target workspace.
        conf["field_id"] = new_field_id
        value["value_provider_conf"] = conf
        return value

    def _delete_decorations_for_fields(self, fields):
        """One DELETE for every configuration referencing any of ``fields``.

        ``field_id`` is a flat key in the conf, so Django's JSONField can
        filter it in SQL. Field ids are globally unique, so the table filter
        is only there to keep the query on the (table, type) index.
        """
        if not fields:
            return
        ViewDecoration.objects.filter(
            value_provider_type=self.type,
            view__table_id__in={field.table_id for field in fields},
            value_provider_conf__field_id__in=[field.id for field in fields],
        ).delete()

    def after_field_delete(self, deleted_field: Field):
        self._delete_decorations_for_fields([deleted_field])

    def after_fields_type_change(self, fields):
        stale = [
            field
            for field in fields
            if field_type_registry.get_by_model(field.specific_class).type
            != SINGLE_SELECT_FIELD_TYPE
        ]
        # Batched: core calls this hook once per registered provider type, so
        # a per-field loop would add one query per field per provider and
        # break core's num-queries assertions for the field change path.
        self._delete_decorations_for_fields(stale)

    def validate_conf_for_view(self, view, conf) -> Union[Field, None]:
        """Public entry point used by tests and future callers."""
        if not conf:
            return None
        return get_single_select_field_or_raise(view, conf)


class ConditionalColorFilterSerializer(serializers.Serializer):
    """One condition row of a conditional color rule.

    Reuses Jadawel's existing view filter operator vocabulary: `type` is a
    `view_filter_type_registry` key, evaluated client-side by the same
    operator implementations that power view filters.
    """

    id = serializers.CharField(required=True)
    type = serializers.CharField(required=True)
    field = serializers.IntegerField(required=True)
    value = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    group = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, default=None
    )

    def validate_type(self, value):
        known_types = {t.type for t in view_filter_type_registry.get_all()}
        if value not in known_types:
            raise serializers.ValidationError(f"{value} is not a valid filter type.")
        return value


class ConditionalColorGroupSerializer(serializers.Serializer):
    """A nested condition group of a conditional color rule."""

    id = serializers.CharField(required=True)
    filter_type = serializers.ChoiceField(choices=["AND", "OR"])
    parent_group = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, default=None
    )


class ConditionalColorRuleSerializer(serializers.Serializer):
    """One color rule: condition tree + the color it paints when matched.

    The shape deliberately matches what the Airtable import mapping emits
    for `conditional_color` (see `airtable.registry.py`), so imported
    views work without translation. An empty condition list always
    matches, which is how the default color for unmatched rows is
    expressed (last rule, first-match-wins).
    """

    filters = ConditionalColorFilterSerializer(many=True, required=False, default=list)
    filter_groups = ConditionalColorGroupSerializer(
        many=True, required=False, default=list
    )
    operator = serializers.ChoiceField(choices=["AND", "OR"])
    color = serializers.RegexField(COLOR_NAME_PATTERN)


class ConditionalColorConfSerializer(serializers.Serializer):
    colors = ConditionalColorRuleSerializer(many=True, required=True)


def get_conditional_color_problems(view, conf) -> List[str]:
    """Return human-readable problems with a conditional color configuration.

    Shape validation happens in the serializer above; this checks the
    semantics that need the database: every condition must reference a
    field that exists on the view's table.
    """

    problems = []
    table_fields = Field.objects.filter(table_id=view.table_id)
    known_field_ids = set(table_fields.values_list("id", flat=True))
    for rule in (conf or {}).get("colors", []):
        for condition in rule.get("filters", []):
            if condition.get("field") not in known_field_ids:
                problems.append(
                    f"Condition references field {condition.get('field')} "
                    "which does not exist on the view's table."
                )
    return problems


class ConditionalColorValueProviderType(DecoratorValueProviderType):
    """Colors a row from the first matching list of conditions.

    OSS re-implementation of upstream's `conditional_color` provider,
    same type string as the Airtable import mapping emits. Rules are
    evaluated in stored order client-side and the first match wins; a
    rule with no conditions matches every row and therefore acts as the
    default color for unmatched rows.
    """

    type = "conditional_color"
    compatible_decorator_types = ["background_color", "left_border_color"]
    value_provider_conf_serializer_class = ConditionalColorConfSerializer

    def before_update_decoration(self, view_decoration, user):
        conf = view_decoration.value_provider_conf or {}
        if not conf:
            return
        problems = get_conditional_color_problems(view_decoration.view, conf)
        if problems:
            raise DecoratorValueProviderTypeNotCompatible(problems[0])

    def set_import_serialized_value(
        self, value: Dict[str, Any], id_mapping: Dict[str, Dict[int, Any]]
    ) -> Dict[str, Any]:
        conf = value.get("value_provider_conf") or {}
        field_mapping = id_mapping.get("database_fields", {})
        for rule in conf.get("colors", []):
            kept = []
            for condition in rule.get("filters", []):
                new_field_id = field_mapping.get(condition.get("field"))
                # A field that was not imported must not keep pointing at
                # a stale id that could belong to another field in the
                # target workspace; drop the condition instead.
                if new_field_id is not None:
                    condition["field"] = new_field_id
                    kept.append(condition)
            rule["filters"] = kept
        value["value_provider_conf"] = conf
        return value

    def _delete_decorations_for_fields(self, fields):
        """Drop configurations whose conditions reference any of ``fields``.

        Condition references are nested inside a JSON array, which Django's
        JSONField cannot query, so the few decorations of these tables are
        matched in Python. One SELECT collects candidates and stale rows go
        out in a single DELETE.
        """
        if not fields:
            return
        field_ids = {field.id for field in fields}
        decorations = ViewDecoration.objects.filter(
            value_provider_type=self.type,
            view__table_id__in={field.table_id for field in fields},
        )
        stale_ids = [
            decoration.id
            for decoration in decorations
            if any(
                condition.get("field") in field_ids
                for rule in (decoration.value_provider_conf or {}).get("colors", [])
                for condition in rule.get("filters", [])
            )
        ]
        if stale_ids:
            ViewDecoration.objects.filter(id__in=stale_ids).delete()

    def after_field_delete(self, deleted_field: Field):
        self._delete_decorations_for_fields([deleted_field])

    def after_fields_type_change(self, fields):
        # After a type change the stored conditions may no longer be
        # compatible with the new field type (the operator set itself is
        # field-agnostic). Removing the stale configuration keeps views
        # predictable; users simply configure the coloring again.
        # Batched: core calls this hook once per registered provider type, so
        # a per-field loop would break core's num-queries assertions for the
        # field change path.
        self._delete_decorations_for_fields(fields)

    def validate_conf_for_view(self, view, conf) -> List[str]:
        """Public entry point used by tests and future callers."""
        if not conf:
            return []
        return get_conditional_color_problems(view, conf)
