from collections import defaultdict

import pytest

from jadawel.contrib.builder.workflow_actions.models import EventTypes
from jadawel.core.utils import MirrorDict


@pytest.mark.django_db
def test_service_action_formulas_are_imported_once(data_fixture):
    """
    A service-backed workflow action used to map its service formulas twice, so
    an id that the first pass produced was mapped again whenever it also
    appeared as an old id in the export. Here data source A becomes B, and B
    (an id the export also uses) would become C on a second pass.
    """

    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, _ = data_fixture.build_table(
        user=user, columns=[("Animal", "text")], rows=[]
    )
    integration = data_fixture.create_local_jadawel_integration(user=user)
    source_a, source_b, source_c = (
        data_fixture.create_builder_local_jadawel_list_rows_data_source(
            table=table, page=page
        )
        for _ in range(3)
    )
    field = fields[0]
    service = data_fixture.create_local_jadawel_upsert_row_service(
        integration=integration, table=table
    )
    service.field_mappings.create(
        field=field, value=f"get('data_source.{source_a.id}.{field.db_column}')"
    )
    action = data_fixture.create_local_jadawel_create_row_workflow_action(
        page=page,
        element=data_fixture.create_builder_button_element(page=page),
        event=EventTypes.CLICK,
        service=service,
    )
    action_type = action.get_type()
    exported = action_type.export_serialized(action)

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["builder_data_sources"] = {
        source_a.id: source_b.id,
        source_b.id: source_c.id,
    }
    imported = action_type.import_serialized(page, exported, id_mapping)

    mapping = imported.service.specific.field_mappings.get()
    assert mapping.value["formula"] == (
        f"get('data_source.{source_b.id}.{field.db_column}')"
    )
