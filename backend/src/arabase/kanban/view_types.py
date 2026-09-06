"""The kanban view type: an OSS board grouped by a single select field.

Mirrors the core `GalleryViewType` surface (field options, export/import,
field lifecycle hooks) so the generic view CRUD, filters, sorts and the
decoration framework treat a kanban view exactly like any core view. The
rows endpoint lives in `arabase.api.kanban`.
"""

from typing import Any, Dict, Optional
from zipfile import ZipFile

from django.db.models import Case, F, Q, QuerySet, When
from django.urls import include, path

from rest_framework import serializers

from arabase.kanban.models import (
    KanbanView,
    KanbanViewFieldOptions,
)
from jadawel.contrib.database.api.fields.errors import (
    ERROR_FIELD_NOT_IN_TABLE,
    ERROR_INCOMPATIBLE_FIELD,
)
from jadawel.contrib.database.fields.exceptions import (
    FieldNotInTable,
    IncompatibleField,
)
from jadawel.contrib.database.fields.models import Field
from jadawel.contrib.database.fields.registries import field_type_registry
from jadawel.contrib.database.views.models import View
from jadawel.contrib.database.views.registries import ViewType
from jadawel.core.import_export.handler import ImportExportConfig
from jadawel.core.storage import ExportZipFile


class KanbanViewFieldOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanViewFieldOptions
        fields = ("hidden", "order")


class KanbanViewType(ViewType):
    type = "kanban"
    model_class = KanbanView
    field_options_model_class = KanbanViewFieldOptions
    field_options_serializer_class = KanbanViewFieldOptionsSerializer
    allowed_fields = ["single_select_field", "card_cover_image_field"]
    field_options_allowed_fields = ["hidden", "order"]
    serializer_field_names = ["single_select_field", "card_cover_image_field"]
    serializer_field_overrides = {
        "single_select_field": serializers.PrimaryKeyRelatedField(
            queryset=Field.objects.all(),
            required=False,
            default=None,
            allow_null=True,
            help_text="References a single select field of which the options become "
            "the board's columns.",
        ),
        "card_cover_image_field": serializers.PrimaryKeyRelatedField(
            queryset=Field.objects.all(),
            required=False,
            default=None,
            allow_null=True,
            help_text="References a file field of which the first image must be "
            "shown as card cover image.",
        ),
    }
    api_exceptions_map = {
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
        IncompatibleField: ERROR_INCOMPATIBLE_FIELD,
    }

    # Row colors work on kanban cards through the same decoration machinery
    # as grid and gallery: `RowCard` renders `decorationsByPlace`.
    can_decorate = True
    can_filter = True
    can_sort = True
    can_share = False
    can_list_rows = True
    has_public_info = False
    can_group_by = False
    can_aggregate_field = False
    can_set_default_values = False

    def get_api_urls(self):
        from arabase.api.kanban import urls as api_urls

        return [
            path("kanban/", include(api_urls, namespace=self.type)),
        ]

    def prepare_values(self, values, table, user):
        """Validate the two field references against the view's table."""

        for name, check in [
            (
                "single_select_field",
                lambda field: field_type_registry.get_by_model(
                    field.specific_class
                ).type
                == "single_select",
            ),
            (
                "card_cover_image_field",
                lambda field: field_type_registry.get_by_model(
                    field.specific_class
                ).can_represent_files(field),
            ),
        ]:
            if values.get(name, None) is not None:
                if isinstance(values[name], int):
                    values[name] = Field.objects.get(pk=values[name])

                if not check(values[name]):
                    raise IncompatibleField(
                        f"The provided field cannot be used as the {name} of a "
                        "kanban view."
                    )
                if values[name].table_id != table.id:
                    raise FieldNotInTable(
                        f"The provided {name} id does not belong to the kanban "
                        "view's table."
                    )

        return super().prepare_values(values, table, user)

    def export_prepared_values(self, view: KanbanView) -> Dict[str, Any]:
        """Export the two field references as ids, not model instances.

        ``prepare_values`` swaps the incoming id for a ``Field`` instance so
        the handler can assign it to the model, and the base export then
        hands those instances to the undo/redo action recorder, whose JSON
        serialization 500s on them. Mirror the gallery: export the ids, which
        ``prepare_values`` accepts back on undo/redo.
        """

        values = super().export_prepared_values(view)
        values["single_select_field"] = view.single_select_field_id
        values["card_cover_image_field"] = view.card_cover_image_field_id
        return values

    def after_field_delete(self, field):
        """Drop the two field references when their field is deleted.

        Trashed fields are not hard-deleted, so the ``SET_NULL`` foreign keys
        do not fire; the references are cleared here instead. Filtering by id
        (not by the instance) because the signal can pass an unsaved model
        after a type conversion replaced it.
        """

        KanbanView.objects.filter(single_select_field_id=field.id).update(
            single_select_field_id=None
        )
        KanbanView.objects.filter(card_cover_image_field_id=field.id).update(
            card_cover_image_field_id=None
        )

    def after_fields_type_change(self, fields):
        """Clear references that no longer match the expected field type.

        One UPDATE for both references, so a field-type change costs the
        same one query per registered view type as the gallery's, keeping
        core's num-queries budgets for the field change path stable.
        """

        stale_single_ids = [
            field.id
            for field in fields
            if field_type_registry.get_by_model(field.specific_class).type
            != "single_select"
        ]
        stale_cover_ids = [
            field.id
            for field in fields
            if not field_type_registry.get_by_model(
                field.specific_class
            ).can_represent_files(field)
        ]

        if not stale_single_ids and not stale_cover_ids:
            return

        KanbanView.objects.filter(
            Q(single_select_field_id__in=stale_single_ids)
            | Q(card_cover_image_field_id__in=stale_cover_ids)
        ).update(
            single_select_field=Case(
                When(single_select_field_id__in=stale_single_ids, then=None),
                default=F("single_select_field"),
            ),
            card_cover_image_field=Case(
                When(card_cover_image_field_id__in=stale_cover_ids, then=None),
                default=F("card_cover_image_field"),
            ),
        )

    def view_created(self, view):
        """Show the first three fields on new cards, like the gallery does."""

        field_options = view.get_field_options(create_if_missing=True).order_by(
            "-field__primary", "field__id"
        )
        ids_to_update = [f.id for f in field_options[0:3]]

        if ids_to_update:
            KanbanViewFieldOptions.objects.filter(id__in=ids_to_update).update(
                hidden=False
            )

    def get_visible_field_options_in_order(self, kanban_view: KanbanView) -> QuerySet:
        return (
            kanban_view.get_field_options(create_if_missing=True)
            .filter(
                Q(hidden=False)
                | Q(field__id=kanban_view.card_cover_image_field_id)
                | Q(field__id=kanban_view.single_select_field_id)
            )
            .order_by("order", "field__id")
        )

    def get_hidden_fields(
        self,
        view: KanbanView,
        field_ids_to_check=None,
    ):
        hidden_field_ids = set()
        fields = view.table.field_set.all()
        field_options = view.kanbanviewfieldoptions_set.all()

        if field_ids_to_check is not None:
            fields = [f for f in fields if f.id in field_ids_to_check]

        for field in fields:
            # The stacking field and the cover field are always visible.
            if field.id in (
                view.single_select_field_id,
                view.card_cover_image_field_id,
            ):
                continue

            field_option_matching = None
            for field_option in field_options:
                if field_option.field_id == field.id:
                    field_option_matching = field_option

            if field_option_matching is None or field_option_matching.hidden:
                hidden_field_ids.add(field.id)

        return hidden_field_ids

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("kanbanviewfieldoptions_set")

    def export_serialized(
        self,
        kanban: View,
        import_export_config: ImportExportConfig,
        cache: Dict,
        files_zip: Optional[ExportZipFile] = None,
        storage=None,
    ):
        serialized = super().export_serialized(
            kanban, import_export_config, cache, files_zip, storage
        )

        if kanban.single_select_field_id:
            serialized["single_select_field_id"] = kanban.single_select_field_id
        if kanban.card_cover_image_field_id:
            serialized["card_cover_image_field_id"] = kanban.card_cover_image_field_id

        serialized_field_options = []
        for field_option in kanban.get_field_options():
            serialized_field_options.append(
                {
                    "id": field_option.id,
                    "field_id": field_option.field_id,
                    "hidden": field_option.hidden,
                    "order": field_option.order,
                }
            )
        serialized["field_options"] = serialized_field_options
        return serialized

    def import_serialized(
        self,
        table,
        serialized_values: Dict[str, Any],
        import_export_config: ImportExportConfig,
        id_mapping: Dict[str, Any],
        cache: Dict,
        files_zip: Optional[ZipFile] = None,
        storage=None,
    ) -> Optional[View]:
        serialized_copy = serialized_values.copy()

        if serialized_copy.get("single_select_field_id", None):
            serialized_copy["single_select_field_id"] = id_mapping["database_fields"][
                serialized_copy["single_select_field_id"]
            ]
        if serialized_copy.get("card_cover_image_field_id", None):
            serialized_copy["card_cover_image_field_id"] = id_mapping[
                "database_fields"
            ][serialized_copy["card_cover_image_field_id"]]

        field_options = serialized_copy.pop("field_options")

        kanban_view = super().import_serialized(
            table,
            serialized_copy,
            import_export_config,
            id_mapping,
            cache,
            files_zip,
            storage,
        )

        if kanban_view is not None:
            if "database_kanban_view_field_options" not in id_mapping:
                id_mapping["database_kanban_view_field_options"] = {}

            for field_option in field_options:
                field_option_copy = field_option.copy()
                field_option_id = field_option_copy.pop("id")
                field_option_copy["field_id"] = id_mapping["database_fields"][
                    field_option["field_id"]
                ]
                field_option_object = KanbanViewFieldOptions.objects.create(
                    kanban_view=kanban_view, **field_option_copy
                )
                id_mapping["database_kanban_view_field_options"][field_option_id] = (
                    field_option_object.id
                )

        return kanban_view
