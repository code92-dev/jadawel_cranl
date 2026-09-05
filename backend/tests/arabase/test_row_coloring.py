"""Row coloring (#29): background decorator fed by single select colors.

The decoration framework itself (model, CRUD, permissions, undo) lives in
core; what is asserted here is the fork's additive surface: our two types
are registered, the API accepts them end to end on a grid view, the
one-per-view rule holds, and bad configurations are rejected with a 400
instead of leaking in or blowing up.
"""

from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from arabase.row_coloring.value_providers import (
    ConditionalColorValueProviderType,
    SingleSelectColorValueProviderType,
)
from jadawel.contrib.database.views.models import ViewDecoration
from jadawel.contrib.database.views.registries import (
    decorator_type_registry,
    decorator_value_provider_type_registry,
)


def decorations_url(view):
    return reverse("api:database:views:list_decorations", kwargs={"view_id": view.id})


def decoration_url(decoration):
    return reverse(
        "api:database:views:decoration_item",
        kwargs={"view_decoration_id": decoration.id},
    )


@pytest.fixture
def coloring_setup(data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    view = data_fixture.create_grid_view(table=table)
    status = data_fixture.create_single_select_field(table=table, name="Status")
    data_fixture.create_select_option(field=status, value="Open", color="blue")
    text = data_fixture.create_text_field(table=table, name="Notes")
    other_table = data_fixture.create_database_table(user=user)
    foreign = data_fixture.create_single_select_field(table=other_table, name="Other")
    return {
        "user": user,
        "token": token,
        "table": table,
        "view": view,
        "status": status,
        "text": text,
        "foreign": foreign,
    }


def auth(token):
    return {"HTTP_AUTHORIZATION": f"JWT {token}"}


@pytest.mark.django_db
def test_row_coloring_types_are_registered():
    assert decorator_type_registry.get("background_color").type == "background_color"
    provider = decorator_value_provider_type_registry.get("single_select_color")
    assert isinstance(provider, SingleSelectColorValueProviderType)
    assert provider.decorator_is_compatible(
        decorator_type_registry.get("background_color")
    )


@pytest.mark.django_db
def test_create_background_color_from_single_select(
    api_client, data_fixture, coloring_setup
):
    setup = coloring_setup
    response = api_client.post(
        decorations_url(setup["view"]),
        {
            "type": "background_color",
            "value_provider_type": "single_select_color",
            "value_provider_conf": {"field_id": setup["status"].id},
        },
        format="json",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_200_OK, response.content
    body = response.json()
    assert body["type"] == "background_color"
    assert body["value_provider_type"] == "single_select_color"
    assert body["value_provider_conf"] == {"field_id": setup["status"].id}
    assert ViewDecoration.objects.filter(view=setup["view"]).count() == 1


@pytest.mark.django_db
def test_coloring_reads_and_writes_stay_inside_the_workspace(
    api_client, data_fixture, coloring_setup
):
    """#29: colors are visible to everyone who can see the view, and the
    configuration can only be changed from inside the workspace.

    This fork has no viewer role (enterprise RBAC was stripped with premium:
    workspace roles are ADMIN and MEMBER), so the contract pinned here is the
    core decoration API's own: any workspace member reads and manages
    decorations, users outside the workspace are rejected on both.
    """
    setup = coloring_setup
    outsider, outsider_token = data_fixture.create_user_and_token()
    payload = {
        "type": "background_color",
        "value_provider_type": "single_select_color",
        "value_provider_conf": {"field_id": setup["status"].id},
    }

    outsider_list = api_client.get(
        decorations_url(setup["view"]), **auth(outsider_token)
    )
    assert outsider_list.status_code == HTTP_400_BAD_REQUEST
    assert outsider_list.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    outsider_create = api_client.post(
        decorations_url(setup["view"]), payload, format="json", **auth(outsider_token)
    )
    assert outsider_create.status_code == HTTP_400_BAD_REQUEST
    assert outsider_create.json()["error"] == "ERROR_USER_NOT_IN_GROUP"
    assert ViewDecoration.objects.filter(view=setup["view"]).count() == 0

    member, member_token = data_fixture.create_user_and_token()
    data_fixture.create_user_workspace(
        workspace=setup["table"].database.workspace,
        user=member,
        permissions="MEMBER",
    )
    member_list = api_client.get(decorations_url(setup["view"]), **auth(member_token))
    assert member_list.status_code == HTTP_200_OK

    member_create = api_client.post(
        decorations_url(setup["view"]), payload, format="json", **auth(member_token)
    )
    assert member_create.status_code == HTTP_200_OK, member_create.content
    assert ViewDecoration.objects.filter(view=setup["view"]).count() == 1


@pytest.mark.django_db
def test_second_background_color_is_rejected(api_client, data_fixture, coloring_setup):
    setup = coloring_setup
    payload = {
        "type": "background_color",
        "value_provider_type": "single_select_color",
        "value_provider_conf": {"field_id": setup["status"].id},
    }
    first = api_client.post(
        decorations_url(setup["view"]), payload, format="json", **auth(setup["token"])
    )
    assert first.status_code == HTTP_200_OK, first.content

    second = api_client.post(
        decorations_url(setup["view"]), payload, format="json", **auth(setup["token"])
    )
    assert second.status_code == HTTP_400_BAD_REQUEST
    assert second.json()["error"] == "ERROR_VIEW_DECORATION_NOT_SUPPORTED"


@pytest.mark.django_db
def test_conf_must_reference_a_field(api_client, data_fixture, coloring_setup):
    setup = coloring_setup
    response = api_client.post(
        decorations_url(setup["view"]),
        {
            "type": "background_color",
            "value_provider_type": "single_select_color",
            "value_provider_conf": {},
        },
        format="json",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_update_conf_shape_is_validated(api_client, data_fixture, coloring_setup):
    setup = coloring_setup
    created = api_client.post(
        decorations_url(setup["view"]),
        {
            "type": "background_color",
            "value_provider_type": "single_select_color",
            "value_provider_conf": {"field_id": setup["status"].id},
        },
        format="json",
        **auth(setup["token"]),
    )
    assert created.status_code == HTTP_200_OK, created.content
    decoration = ViewDecoration.objects.get(pk=created.json()["id"])

    response = api_client.patch(
        decoration_url(decoration),
        {"value_provider_conf": {}},
        format="json",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_type_change_away_from_single_select_cleans_up(data_fixture, coloring_setup):
    from jadawel.contrib.database.fields.handler import FieldHandler

    setup = coloring_setup
    decoration = ViewDecoration.objects.create(
        view=setup["view"],
        type="background_color",
        value_provider_type="single_select_color",
        value_provider_conf={"field_id": setup["status"].id},
        order=1,
    )
    FieldHandler().update_field(
        user=setup["user"],
        table=setup["table"],
        field=setup["status"],
        new_type_name="text",
        name="Status",
    )
    assert not ViewDecoration.objects.filter(pk=decoration.pk).exists()


@pytest.mark.django_db
def test_validate_conf_for_view_rejects_bad_fields(coloring_setup):
    from arabase.row_coloring.value_providers import get_single_select_field_or_raise
    from jadawel.contrib.database.views.exceptions import (
        DecoratorValueProviderTypeNotCompatible,
    )

    setup = coloring_setup
    field = get_single_select_field_or_raise(
        setup["view"], {"field_id": setup["status"].id}
    )
    assert field.id == setup["status"].id
    for bad_conf in (
        {},
        {"field_id": setup["text"].id},
        {"field_id": setup["foreign"].id},
        {"field_id": 999999},
    ):
        with pytest.raises(DecoratorValueProviderTypeNotCompatible):
            get_single_select_field_or_raise(setup["view"], bad_conf)


@pytest.mark.django_db
def test_field_delete_cleans_up_decorations(data_fixture, coloring_setup):
    from jadawel.contrib.database.fields.handler import FieldHandler

    setup = coloring_setup
    decoration = ViewDecoration.objects.create(
        view=setup["view"],
        type="background_color",
        value_provider_type="single_select_color",
        value_provider_conf={"field_id": setup["status"].id},
        order=1,
    )
    FieldHandler().delete_field(setup["user"], setup["status"])
    assert not ViewDecoration.objects.filter(pk=decoration.pk).exists()


@pytest.mark.django_db
def test_import_remaps_field_id(coloring_setup):
    provider = decorator_value_provider_type_registry.get("single_select_color")
    value = {
        "type": "background_color",
        "value_provider_type": "single_select_color",
        "value_provider_conf": {"field_id": 41},
        "order": 1,
    }
    remapped = provider.set_import_serialized_value(
        value, {"database_fields": {41: 77}}
    )
    assert remapped["value_provider_conf"] == {"field_id": 77}

    dropped = provider.set_import_serialized_value(dict(value), {"database_fields": {}})
    assert dropped["value_provider_conf"] == {"field_id": None}


def conditional_conf(field_id, **overrides):
    """Build a conditional color conf: one matching rule plus a default."""

    conf = {
        "colors": [
            {
                "filters": [
                    {"id": "01F", "type": "contains", "field": field_id, "value": "x"}
                ],
                "filter_groups": [],
                "operator": "OR",
                "color": "red",
            },
            {
                "filters": [],
                "filter_groups": [],
                "operator": "AND",
                "color": "gray",
            },
        ]
    }
    conf["colors"][0].update(overrides)
    return conf


@pytest.mark.django_db
def test_all_row_coloring_types_are_registered():
    assert decorator_type_registry.get("left_border_color").type == "left_border_color"
    assert decorator_type_registry.get("background_color").type == "background_color"

    conditions = decorator_value_provider_type_registry.get("conditional_color")
    assert isinstance(conditions, ConditionalColorValueProviderType)
    for decorator in ("background_color", "left_border_color"):
        assert conditions.decorator_is_compatible(
            decorator_type_registry.get(decorator)
        )


@pytest.mark.django_db
def test_create_left_border_color_from_single_select(
    api_client, data_fixture, coloring_setup
):
    setup = coloring_setup
    response = api_client.post(
        decorations_url(setup["view"]),
        {
            "type": "left_border_color",
            "value_provider_type": "single_select_color",
            "value_provider_conf": {"field_id": setup["status"].id},
        },
        format="json",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_200_OK, response.content
    assert response.json()["type"] == "left_border_color"


@pytest.mark.django_db
def test_left_border_and_background_coexist(api_client, data_fixture, coloring_setup):
    setup = coloring_setup
    for decoration_type in ("background_color", "left_border_color"):
        response = api_client.post(
            decorations_url(setup["view"]),
            {
                "type": decoration_type,
                "value_provider_type": "single_select_color",
                "value_provider_conf": {"field_id": setup["status"].id},
            },
            format="json",
            **auth(setup["token"]),
        )
        assert response.status_code == HTTP_200_OK, response.content
    assert ViewDecoration.objects.filter(view=setup["view"]).count() == 2


@pytest.mark.django_db
def test_second_left_border_is_rejected(api_client, data_fixture, coloring_setup):
    setup = coloring_setup
    payload = {
        "type": "left_border_color",
        "value_provider_type": "single_select_color",
        "value_provider_conf": {"field_id": setup["status"].id},
    }
    first = api_client.post(
        decorations_url(setup["view"]), payload, format="json", **auth(setup["token"])
    )
    assert first.status_code == HTTP_200_OK, first.content

    second = api_client.post(
        decorations_url(setup["view"]), payload, format="json", **auth(setup["token"])
    )
    assert second.status_code == HTTP_400_BAD_REQUEST
    assert second.json()["error"] == "ERROR_VIEW_DECORATION_NOT_SUPPORTED"


@pytest.mark.django_db
def test_conditional_conf_rejects_unknown_filter_type(
    api_client, data_fixture, coloring_setup
):
    setup = coloring_setup
    bad = {
        "colors": [
            {
                "filters": [
                    {
                        "id": "01F",
                        "type": "not_a_filter",
                        "field": setup["text"].id,
                        "value": "x",
                    }
                ],
                "filter_groups": [],
                "operator": "OR",
                "color": "red",
            }
        ]
    }
    response = api_client.post(
        decorations_url(setup["view"]),
        {
            "type": "background_color",
            "value_provider_type": "conditional_color",
            "value_provider_conf": bad,
        },
        format="json",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_create_conditional_color_decoration(api_client, data_fixture, coloring_setup):
    setup = coloring_setup
    conf = conditional_conf(setup["text"].id)
    response = api_client.post(
        decorations_url(setup["view"]),
        {
            "type": "background_color",
            "value_provider_type": "conditional_color",
            "value_provider_conf": conf,
        },
        format="json",
        **auth(setup["token"]),
    )
    assert response.status_code == HTTP_200_OK, response.content
    decoration = ViewDecoration.objects.get(pk=response.json()["id"])
    stored = decoration.value_provider_conf
    # The conf serializer fills field defaults, so compare the semantic
    # content rather than the exact payload.
    assert [rule["color"] for rule in stored["colors"]] == ["red", "gray"]
    first_rule = stored["colors"][0]
    assert first_rule["operator"] == "OR"
    assert first_rule["filters"][0]["type"] == "contains"
    assert first_rule["filters"][0]["field"] == setup["text"].id
    assert first_rule["filters"][0]["value"] == "x"
    assert stored["colors"][1]["filters"] == []


@pytest.mark.django_db
def test_conditional_conf_rejects_bad_operator_and_color(
    api_client, data_fixture, coloring_setup
):
    setup = coloring_setup
    for overrides in ({"operator": "XOR"}, {"color": "#ff0000"}):
        response = api_client.post(
            decorations_url(setup["view"]),
            {
                "type": "background_color",
                "value_provider_type": "conditional_color",
                "value_provider_conf": conditional_conf(setup["text"].id, **overrides),
            },
            format="json",
            **auth(setup["token"]),
        )
        assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_conditional_update_backstops_stored_conf(coloring_setup):
    setup = coloring_setup
    provider = decorator_value_provider_type_registry.get("conditional_color")
    decoration = ViewDecoration.objects.create(
        view=setup["view"],
        type="background_color",
        value_provider_type="conditional_color",
        value_provider_conf=conditional_conf(999999),
        order=1,
    )
    problems = provider.validate_conf_for_view(
        setup["view"], decoration.value_provider_conf
    )
    assert "does not exist on the view's table" in problems[0]

    from jadawel.contrib.database.views.exceptions import (
        DecoratorValueProviderTypeNotCompatible,
    )

    with pytest.raises(DecoratorValueProviderTypeNotCompatible):
        provider.before_update_decoration(decoration, None)


@pytest.mark.django_db
def test_conditional_import_drops_unmapped_fields(coloring_setup):
    setup = coloring_setup
    provider = decorator_value_provider_type_registry.get("conditional_color")
    value = {
        "value_provider_conf": {
            "colors": [
                {
                    "filters": [
                        {"id": "1", "type": "contains", "field": 10, "value": "x"},
                        {"id": "2", "type": "equal", "field": 11, "value": "y"},
                    ],
                    "filter_groups": [],
                    "operator": "AND",
                    "color": "red",
                }
            ]
        }
    }
    result = provider.set_import_serialized_value(value, {"database_fields": {10: 100}})
    filters = result["value_provider_conf"]["colors"][0]["filters"]
    assert [condition["field"] for condition in filters] == [100]


@pytest.mark.django_db
def test_conditional_field_delete_cleans_up_decorations(data_fixture, coloring_setup):
    from jadawel.contrib.database.fields.handler import FieldHandler

    setup = coloring_setup
    decoration = ViewDecoration.objects.create(
        view=setup["view"],
        type="background_color",
        value_provider_type="conditional_color",
        value_provider_conf=conditional_conf(setup["text"].id),
        order=1,
    )
    FieldHandler().delete_field(user=setup["user"], field=setup["text"])
    assert not ViewDecoration.objects.filter(pk=decoration.pk).exists()
