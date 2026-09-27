"""Sanad's element-level tools for application-builder pages, and the theme.

``app_tools`` builds pages from a few intents (content, a table, a form). These
tools reach every element the editor offers — columns, containers, repeats,
links drawn as buttons, headers, menus — plus data sources and the app's theme,
so an app can be designed, not only assembled. They are offered only once the
``app-builder`` skill is loaded, because using them well needs its guidance.

Every value is validated by the serializer the editor's own API uses, so what
the editor would reject is rejected here too, with the same message.
"""

from typing import Literal, Optional

from django.db import transaction

from pydantic import BaseModel, Field

from arabase.sanad.tools import SanadEndpoint, SanadTool

SKILL = "app-builder"

ELEMENT_DESCRIPTIONS = {
    "heading": "A title; level 1 (page title) to 6.",
    "text": "A paragraph; format 'plain' or 'markdown'.",
    "link": "Goes to a page of the app or a URL; variant 'button' draws it as a "
    "button. The way to make navigation buttons.",
    "image": "An image from a URL (image_source_type 'url'), with alt text.",
    "button": "A button whose click runs actions added in the editor; for "
    "navigation use a link with variant 'button' instead.",
    "column": "Side-by-side columns (column_amount 1-6). Put children in it with "
    "parent_element_id and place_in_container '0', '1', ...",
    "simple_container": "A box grouping its children, e.g. a card with a background.",
    "table": "A table of a list data source's rows, one column per entry of fields.",
    "repeat": "Repeats its children once per row of a list data source: cards, "
    "galleries, lists. Children read the row with get('current_record.field_<id>').",
    "record_selector": "Pick a row of a list data source, inside a form.",
    "form_container": "A form. Prefer add_form_to_page, which also saves submissions.",
    "input_text": "A text, number or email input in a form.",
    "choice": "A dropdown, radio or checkbox list in a form.",
    "checkbox": "A single checkbox in a form.",
    "datetime_picker": "A date (and time) input in a form.",
    "rating": "Shows a value as stars.",
    "rating_input": "A star rating input in a form.",
    "iframe": "Embeds a URL or HTML.",
    "header": "Shown at the top of several pages (share_type 'all', 'only' or "
    "'except' with pages). Created on the app's shared page automatically.",
    "footer": "Like header, at the bottom of pages.",
    "menu": "Navigation links to pages, horizontal or vertical; usually inside a "
    "header.",
}

MULTI_PAGE_TYPES = ("header", "footer")

STYLE_NOTE = (
    "Every element also takes box styles: style_padding_top/bottom/left/right and "
    "style_margin_top/bottom/left/right (px), style_border_<side>_size and "
    "style_border_<side>_color, style_border_radius, style_background ('none' or "
    "'color') with style_background_color, style_background_radius, and "
    "style_width ('full', 'full-width', 'normal', 'medium', 'small'). Colours are "
    "#rrggbb or a theme colour name: 'primary', 'secondary', 'border', "
    "'success', 'warning', 'error', 'transparent'."
)


def _get_page(endpoint: SanadEndpoint, page_id: int):
    from arabase.sanad.app_tools import _get_page as get_page

    return get_page(endpoint, page_id)


def _get_element(endpoint: SanadEndpoint, element_id: int):
    from jadawel.contrib.builder.elements.exceptions import ElementDoesNotExist
    from jadawel.contrib.builder.elements.service import ElementService

    element = ElementService().get_element(endpoint.user, element_id)
    if element.page.builder.workspace_id != endpoint.workspace.id:
        raise ElementDoesNotExist(element_id)
    return element.specific


def _request_serializer(element_type):
    """The serializer the editor's API validates this element type with."""

    from jadawel.contrib.builder.api.elements.serializers import (
        CreateElementSerializer,
    )

    return element_type.get_serializer_class(
        base_class=CreateElementSerializer, request_serializer=True
    )()


def _formula_fields(element_type) -> set[str]:
    from jadawel.core.formula.serializers import FormulaSerializerField

    serializer = _request_serializer(element_type)
    return {
        name
        for name, field in serializer.fields.items()
        if isinstance(field, FormulaSerializerField)
    }


def _as_formulas(element_type, settings: dict) -> dict:
    """Plain text given for a formula setting becomes that literal text.

    Models often pass "Welcome" where a formula is expected; that is not a valid
    formula, and the only sensible reading is the text itself. Anything that
    parses (``'Welcome'``, ``get('page_parameter.id')``) is kept as a formula.
    """

    from arabase.sanad.app_tools import formula_literal
    from jadawel.core.formula.parser.parser import get_parse_tree_for_formula

    settings = dict(settings)
    for name in _formula_fields(element_type) & settings.keys():
        value = settings[name]
        if not isinstance(value, str) or not value:
            continue
        try:
            get_parse_tree_for_formula(value)
        except Exception:  # noqa: BLE001 - any parse failure means plain text
            settings[name] = formula_literal(value)
    return settings


def _ordered_menu_items(items: list) -> list:
    """Menu items numbered in the order given, as the editor numbers them."""

    import uuid

    return [
        {
            **item,
            "uid": item.get("uid") or str(uuid.uuid4()),
            # A name is plain text; models often quote it like a formula.
            **(
                {"name": item["name"][1:-1]}
                if isinstance(item.get("name"), str)
                and len(item["name"]) > 1
                and item["name"][0] == item["name"][-1] == "'"
                else {}
            ),
            "menu_item_order": item.get("menu_item_order", index),
            **(
                {"children": _ordered_menu_items(item["children"])}
                if item.get("children")
                else {}
            ),
        }
        if isinstance(item, dict)
        else item
        for index, item in enumerate(items)
    ]


def _prepare(element_type, settings: dict) -> dict:
    settings = _as_formulas(element_type, settings)
    if isinstance(settings.get("menu_items"), list):
        settings["menu_items"] = _ordered_menu_items(settings["menu_items"])
    return settings


def _element_summary(element) -> dict:
    from jadawel.contrib.builder.api.elements.serializers import ElementSerializer
    from jadawel.contrib.builder.elements.models import Element
    from jadawel.contrib.builder.elements.registries import element_type_registry

    data = dict(element_type_registry.get_serializer(element, ElementSerializer).data)
    settings = {
        key: value
        for key, value in data.items()
        if not key.startswith("style_")
        and key not in ("id", "page_id", "type", "order", "parent_element_id", "roles")
        and value not in (None, "", [], {})
    }
    # Styles that differ from their default, so the model sees that a style it
    # set took effect (it once re-applied styles it could not see here, then
    # told the user they had not been saved).
    styles = {}
    for key, value in data.items():
        if not key.startswith("style_") or value in (None, ""):
            continue
        try:
            default = Element._meta.get_field(key).get_default()
        except Exception:  # noqa: BLE001 - not a model field (e.g. a file URL)
            default = None
        if value != default:
            styles[key] = value
    return {
        "id": data["id"],
        "type": data["type"],
        "page_id": element.page_id,
        "application_id": element.page.builder_id,
        "parent_element_id": data.get("parent_element_id"),
        "place_in_container": data.get("place_in_container"),
        "settings": settings,
        "styles": styles,
    }


# ---------------------------------------------------------------------------
# Elements
# ---------------------------------------------------------------------------


class ListPageElementsInput(BaseModel):
    page_id: int = Field(..., description="The page whose elements to list.")


def list_page_elements(endpoint: SanadEndpoint, args: ListPageElementsInput) -> dict:
    from jadawel.contrib.builder.data_sources.service import DataSourceService
    from jadawel.contrib.builder.elements.service import ElementService

    page = _get_page(endpoint, args.page_id)
    shared = page.builder.shared_page
    elements = ElementService().get_elements(endpoint.user, page)
    shared_elements = [
        element
        for element in ElementService().get_elements(endpoint.user, shared)
        if element.get_type().type in MULTI_PAGE_TYPES
        or element.parent_element_id is not None
    ]
    data_sources = [
        *DataSourceService().get_data_sources(endpoint.user, page),
        *DataSourceService().get_data_sources(endpoint.user, shared),
    ]
    return {
        "page_id": page.id,
        "application_id": page.builder_id,
        "path": page.path,
        "path_params": page.path_params,
        "elements": [_element_summary(element.specific) for element in elements],
        "shared_elements": [
            _element_summary(element.specific) for element in shared_elements
        ],
        "data_sources": [
            {
                "id": data_source.id,
                "name": data_source.name,
                "shared": data_source.page_id == shared.id,
                "type": data_source.service.get_type().type
                if data_source.service
                else None,
                "table_id": getattr(data_source.service.specific, "table_id", None)
                if data_source.service
                else None,
            }
            for data_source in data_sources
        ],
    }


class DescribePageElementInput(BaseModel):
    type: Optional[str] = Field(
        None, description="An element type to describe. Omit to list every type."
    )


def describe_page_element(
    endpoint: SanadEndpoint, args: DescribePageElementInput
) -> dict:
    from arabase.sanad.app_tools import _describe_serializer
    from jadawel.contrib.builder.elements.registries import element_type_registry

    if not args.type:
        return {
            "element_types": [
                {
                    "type": element_type.type,
                    "description": ELEMENT_DESCRIPTIONS.get(element_type.type, ""),
                }
                for element_type in element_type_registry.get_all()
            ],
            "styles": STYLE_NOTE,
        }
    element_type = element_type_registry.get(args.type)
    settings = {
        name: info
        for name, info in _describe_serializer(
            _request_serializer(element_type)
        ).items()
        if not name.startswith("style_")
        and name
        not in ("parent_element_id", "place_in_container", "roles", "before_id")
    }
    return {
        "type": element_type.type,
        "description": ELEMENT_DESCRIPTIONS.get(element_type.type, ""),
        "settings": settings,
        "formula_settings": sorted(_formula_fields(element_type)),
        "styles": STYLE_NOTE,
    }


class AddPageElementInput(BaseModel):
    page_id: int = Field(..., description="The page to add the element to.")
    type: str = Field(..., description="The element type (describe_page_element).")
    settings: dict = Field(
        default_factory=dict,
        description=(
            "The element's settings as describe_page_element lists them, plus "
            "any box styles. Formula settings take a formula; plain text is "
            "taken literally."
        ),
    )
    parent_element_id: Optional[int] = Field(
        None,
        description="A container (column, simple_container, repeat, form, "
        "header, footer) to put the element in.",
    )
    place_in_container: Optional[str | int] = Field(
        None, description="Inside a column: the column index, '0' for the first."
    )
    before_element_id: Optional[int] = Field(
        None, description="Insert before this element; omit to add at the end."
    )


def add_page_element(endpoint: SanadEndpoint, args: AddPageElementInput) -> dict:
    from jadawel.api.utils import validate_data_custom_fields
    from jadawel.contrib.builder.api.elements.serializers import (
        CreateElementSerializer,
    )
    from jadawel.contrib.builder.application_types import BuilderApplicationType
    from jadawel.contrib.builder.elements.registries import element_type_registry
    from jadawel.contrib.builder.elements.service import ElementService

    page = _get_page(endpoint, args.page_id)
    if args.type in MULTI_PAGE_TYPES:
        page = page.builder.shared_page
    element_type = element_type_registry.get(args.type)
    settings = dict(args.settings)
    # A menu is created empty and then given its items, as the editor does:
    # the menu type only accepts items on update.
    menu_items = settings.pop("menu_items", None) if args.type == "menu" else None
    payload = {"type": args.type, **_prepare(element_type, settings)}
    if args.parent_element_id is not None:
        parent = _get_element(endpoint, args.parent_element_id)
        payload["parent_element_id"] = parent.id
        page = parent.page
    if args.place_in_container is not None:
        # Models send 0, "0" and even '"0"'; the column index is the digits.
        payload["place_in_container"] = str(args.place_in_container).strip("\"' ")
    data = validate_data_custom_fields(
        args.type,
        element_type_registry,
        payload,
        base_serializer_class=CreateElementSerializer,
        serializer_class_context={"application_type": BuilderApplicationType},
        return_validated=True,
    )
    data.pop("type", None)
    data.pop("before_id", None)
    before = (
        _get_element(endpoint, args.before_element_id)
        if args.before_element_id
        else None
    )
    with transaction.atomic():
        element = ElementService().create_element(
            endpoint.user, element_type, page, before=before, **data
        )
        if menu_items:
            return update_page_element(
                endpoint,
                UpdatePageElementInput(
                    element_id=element.id, settings={"menu_items": menu_items}
                ),
            )
    return _element_summary(element.specific)


class UpdatePageElementInput(BaseModel):
    element_id: int = Field(..., description="The element to change.")
    settings: dict = Field(..., description="Only the settings to change.")


def update_page_element(endpoint: SanadEndpoint, args: UpdatePageElementInput):
    from jadawel.api.utils import validate_data_custom_fields
    from jadawel.contrib.builder.api.elements.serializers import (
        UpdateElementSerializer,
    )
    from jadawel.contrib.builder.application_types import BuilderApplicationType
    from jadawel.contrib.builder.elements.handler import ElementHandler
    from jadawel.contrib.builder.elements.registries import element_type_registry
    from jadawel.contrib.builder.elements.service import ElementService

    element = _get_element(endpoint, args.element_id)
    element_type = element.get_type()
    data = validate_data_custom_fields(
        element_type.type,
        element_type_registry,
        _prepare(element_type, args.settings),
        base_serializer_class=UpdateElementSerializer,
        serializer_class_context={"application_type": BuilderApplicationType},
        partial=True,
        return_validated=True,
    )
    # Locked for the update, as the editor's API does inside its transaction.
    with transaction.atomic():
        element = ElementService().update_element(
            endpoint.user, ElementHandler().get_element_for_update(element.id), **data
        )
    return _element_summary(element.specific)


class DeletePageElementInput(BaseModel):
    element_id: int = Field(
        ..., description="The element to delete, with its children."
    )


def delete_page_element(endpoint: SanadEndpoint, args: DeletePageElementInput):
    from jadawel.contrib.builder.elements.handler import ElementHandler
    from jadawel.contrib.builder.elements.service import ElementService

    element = _get_element(endpoint, args.element_id)
    with transaction.atomic():
        ElementService().delete_element(
            endpoint.user, ElementHandler().get_element_for_update(element.id)
        )
    return {"deleted_element_id": args.element_id, "page_id": element.page_id}


# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------


class AddPageDataSourceInput(BaseModel):
    page_id: int = Field(..., description="The page the data is for.")
    name: str = Field(..., description="A short name, unique on the page.")
    kind: Literal["list_rows", "get_row"] = Field(
        ...,
        description="list_rows: many rows (tables, repeats, dropdowns). get_row: "
        "one row, e.g. the record a detail page shows.",
    )
    table_id: int = Field(..., description="The table to read.")
    view_id: Optional[int] = Field(
        None, description="A view whose filters and sorts to apply."
    )
    row_id: Optional[str] = Field(
        None,
        description="get_row only: a formula for the row, usually "
        "get('page_parameter.id').",
    )
    rows_per_page: Optional[int] = Field(
        None, ge=1, le=200, description="list_rows only: rows per page (default 20)."
    )
    shared: bool = Field(
        False, description="Make it available on every page (e.g. for a menu)."
    )


def add_page_data_source(endpoint: SanadEndpoint, args: AddPageDataSourceInput):
    from arabase.sanad.app_tools import _data_source_name, _local_integration
    from jadawel.contrib.builder.data_sources.service import DataSourceService
    from jadawel.contrib.database.mcp import services
    from jadawel.core.services.registries import service_type_registry

    page = _get_page(endpoint, args.page_id)
    table = services.get_table(endpoint.user, endpoint.workspace, args.table_id)
    target = page.builder.shared_page if args.shared else page
    values = {"table_id": table.id, "view_id": args.view_id}
    if args.kind == "get_row":
        values["row_id"] = args.row_id or ""
    elif args.rows_per_page:
        values["default_result_count"] = args.rows_per_page
    with transaction.atomic():
        values["integration_id"] = _local_integration(endpoint, page.builder).id
        data_source = DataSourceService().create_data_source(
            endpoint.user,
            target,
            service_type_registry.get(f"local_jadawel_{args.kind}"),
            name=_data_source_name(target, args.name),
            **values,
        )
    rows = f"data_source.{data_source.id}"
    return {
        "data_source_id": data_source.id,
        "name": data_source.name,
        "page_id": target.id,
        "application_id": page.builder_id,
        "read_it_with": (
            f"get('{rows}.field_<field id>')"
            if args.kind == "get_row"
            else f"a table or repeat with data_source_id {data_source.id}, or "
            f"get('{rows}.*.field_<field id>') for every row"
        ),
    }


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


class GetAppThemeInput(BaseModel):
    application_id: int = Field(..., description="The builder application.")


def get_app_theme(endpoint: SanadEndpoint, args: GetAppThemeInput) -> dict:
    from arabase.sanad.app_tools import _get_application
    from jadawel.contrib.builder.api.theme.serializers import (
        serialize_builder_theme,
    )

    builder = _get_application(endpoint, args.application_id, "builder")
    return {"application_id": builder.id, "theme": serialize_builder_theme(builder)}


class UpdateAppThemeInput(BaseModel):
    application_id: int = Field(..., description="The builder application.")
    settings: dict = Field(
        ...,
        description="Theme properties to change, named as get_app_theme returns "
        "them, e.g. primary_color, body_font_family, heading_1_font_size.",
    )


def update_app_theme(endpoint: SanadEndpoint, args: UpdateAppThemeInput) -> dict:
    from arabase.sanad.app_tools import _get_application
    from jadawel.api.utils import validate_data
    from jadawel.contrib.builder.api.theme.serializers import (
        CombinedThemeConfigBlocksRequestSerializer,
    )
    from jadawel.contrib.builder.theme.service import ThemeService

    builder = _get_application(endpoint, args.application_id, "builder")
    unknown = set(args.settings) - set(
        CombinedThemeConfigBlocksRequestSerializer().fields
    )
    if unknown:
        raise ValueError(f"Unknown theme properties: {sorted(unknown)}.")
    data = validate_data(
        CombinedThemeConfigBlocksRequestSerializer,
        args.settings,
        partial=True,
        return_validated=True,
    )
    with transaction.atomic():
        ThemeService().update_theme(endpoint.user, builder, **data)
    return {"application_id": builder.id, "updated": sorted(data)}


def get_page_tools() -> list[SanadTool]:
    return [
        SanadTool(
            "list_page_elements",
            "List a page's elements (with their settings and containers), the "
            "header/footer shown on it, and its data sources.",
            ListPageElementsInput,
            list_page_elements,
            skill=SKILL,
        ),
        SanadTool(
            "describe_page_element",
            "List the page element types, or describe one type's settings.",
            DescribePageElementInput,
            describe_page_element,
            skill=SKILL,
        ),
        SanadTool(
            "add_page_element",
            "Add any element to a page or into a container, with its settings "
            "and styles.",
            AddPageElementInput,
            add_page_element,
            skill=SKILL,
        ),
        SanadTool(
            "update_page_element",
            "Change an element's settings or styles.",
            UpdatePageElementInput,
            update_page_element,
            skill=SKILL,
        ),
        SanadTool(
            "delete_page_element",
            "Delete an element and everything inside it. Needs the user's approval.",
            DeletePageElementInput,
            delete_page_element,
            skill=SKILL,
        ),
        SanadTool(
            "add_page_data_source",
            "Give a page data from a table: many rows (list_rows) or one row "
            "(get_row), for tables, repeats and texts to read.",
            AddPageDataSourceInput,
            add_page_data_source,
            skill=SKILL,
        ),
        SanadTool(
            "get_app_theme",
            "Read an app's theme: colours, fonts, buttons, links, inputs, tables.",
            GetAppThemeInput,
            get_app_theme,
            skill=SKILL,
        ),
        SanadTool(
            "update_app_theme",
            "Change an app's theme properties.",
            UpdateAppThemeInput,
            update_app_theme,
            skill=SKILL,
        ),
    ]
