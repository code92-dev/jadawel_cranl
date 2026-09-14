"""
Tests for the additive XLSX and ODS table exporters.

These put a real table through the real export pipeline (export job, permission
check, paginated writer, storage) and then read the produced workbook back, so
they cover the row values, the header behaviour, the row-id/primary-field
options and the formula-injection escaping together.
"""

import csv
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree

import pytest

TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"


@pytest.fixture
def export_setup(data_fixture):
    """A table with one text field and two rows of values worth asserting on."""

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    name_field = data_fixture.create_text_field(table=table, name="Name", primary=True)
    model = table.get_model()
    model.objects.create(**{f"field_{name_field.id}": "Tesla"})
    model.objects.create(**{f"field_{name_field.id}": "مرسيدس"})
    return user, table, name_field, model


def run_export(table, user, options):
    """
    Run an export job writing into an in-memory file and return the raw bytes.

    This mirrors ``run_export_job_with_mock_storage`` in the CSV export tests but
    returns bytes, because both workbooks are binary.
    """

    storage_mock = MagicMock()
    stub_file = BytesIO()
    storage_mock.open.return_value = stub_file
    stub_file.close = lambda: None

    with patch("jadawel.core.storage.get_default_storage", return_value=storage_mock):
        from jadawel.contrib.database.export.handler import ExportHandler

        handler = ExportHandler()
        job = handler.create_pending_export_job(user, table, None, options)
        handler.run_export_job(job)

    return stub_file.getvalue()


def read_xlsx_rows(payload):
    from openpyxl import load_workbook

    workbook = load_workbook(BytesIO(payload), read_only=True)
    worksheet = workbook.active
    return [[cell for cell in row] for row in worksheet.iter_rows(values_only=True)]


def read_ods_rows(payload):
    """Extract the sheet as a list of rows of cell text, straight from the zip."""

    with zipfile.ZipFile(BytesIO(payload)) as archive:
        # S314: parsing our own exporter's generated output in a test, not
        # untrusted user data.
        content = ElementTree.fromstring(archive.read("content.xml"))  # noqa: S314

    rows = []
    for row in content.iter(f"{{{TABLE_NS}}}table-row"):
        values = []
        for cell in row.findall(f"{{{TABLE_NS}}}table-cell"):
            paragraph = cell.find(f"{{{TEXT_NS}}}p")
            values.append(paragraph.text if paragraph is not None else None)
        rows.append(values)
    return rows


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("exporter_type", "reader"),
    [("xlsx", read_xlsx_rows), ("ods", read_ods_rows)],
)
def test_spreadsheet_export_writes_header_and_rows(export_setup, exporter_type, reader):
    """Both exporters write the field names, then every row, in table order."""

    user, table, _, _ = export_setup

    payload = run_export(table, user, {"exporter_type": exporter_type})

    rows = reader(payload)
    assert rows[0][:2] == ["id", "Name"]
    assert [row[1] for row in rows[1:]] == ["Tesla", "مرسيدس"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("exporter_type", "reader"),
    [("xlsx", read_xlsx_rows), ("ods", read_ods_rows)],
)
def test_spreadsheet_export_can_omit_the_header(export_setup, exporter_type, reader):
    user, table, _, _ = export_setup

    payload = run_export(
        table,
        user,
        {"exporter_type": exporter_type, "excel_include_header": False},
    )

    rows = reader(payload)
    assert [row[1] for row in rows] == ["Tesla", "مرسيدس"]


@pytest.mark.django_db
@pytest.mark.parametrize("exporter_type", ["xlsx", "ods"])
def test_spreadsheet_export_row_id_and_primary_field_are_optional(
    export_setup, exporter_type
):
    """
    Both switches drop their column, matching the CSV exporter's semantics: the
    id column is separate from the primary field column.
    """

    user, table, _, _ = export_setup

    payload = run_export(
        table,
        user,
        {
            "exporter_type": exporter_type,
            "include_row_id": False,
            "include_primary_field": False,
        },
    )

    rows = (
        read_xlsx_rows(payload) if exporter_type == "xlsx" else read_ods_rows(payload)
    )
    # No header and no columns at all: the sheet holds row placeholders but no values.
    assert all(not any(value for value in row) for row in rows)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("exporter_type", "read_cell"),
    [
        ("xlsx", lambda payload: read_xlsx_rows(payload)[1][1]),
        ("ods", lambda payload: read_ods_rows(payload)[1][1]),
    ],
)
@pytest.mark.parametrize(
    "dangerous",
    ["=1+1", "+cmd|'/C calc'!A0", "-2+3", "@SUM(A1)"],
)
def test_spreadsheet_export_stores_formula_like_text_as_text(
    data_fixture, exporter_type, read_cell, dangerous
):
    """
    A cell whose text would be read as a formula must be stored inert and
    round-trip exactly: the writers use explicitly string-typed cells, so no
    apostrophe escape is needed and the stored value equals the original.
    (Formula injection, CWE-1236.)
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    name_field = data_fixture.create_text_field(table=table, name="Name", primary=True)
    table.get_model().objects.create(**{f"field_{name_field.id}": dangerous})

    payload = run_export(table, user, {"exporter_type": exporter_type})

    stored = read_cell(payload)
    assert stored == dangerous


@pytest.mark.django_db
def test_xlsx_cell_beginning_with_equals_is_not_a_formula(data_fixture):
    """The xlsx export must store the escaped value as a string cell, not a formula."""

    from openpyxl import load_workbook

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    name_field = data_fixture.create_text_field(table=table, name="Name", primary=True)
    table.get_model().objects.create(**{f"field_{name_field.id}": "=SUM(1)"})

    payload = run_export(table, user, {"exporter_type": "xlsx"})
    worksheet = load_workbook(BytesIO(payload)).active
    cell = worksheet.cell(row=2, column=2)
    assert cell.value == "=SUM(1)"
    assert cell.data_type == "s"


@pytest.mark.django_db
def test_ods_export_is_a_valid_odf_package(export_setup):
    user, table, _, _ = export_setup

    payload = run_export(table, user, {"exporter_type": "ods"})

    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert archive.testzip() is None
        # The mimetype entry must come first and be stored uncompressed so a
        # reader can identify the file without unpacking the archive.
        info = archive.infolist()[0]
        assert info.filename == "mimetype"
        assert info.compress_type == zipfile.ZIP_STORED
        assert (
            archive.read("mimetype").decode()
            == "application/vnd.oasis.opendocument.spreadsheet"
        )


@pytest.mark.django_db
def test_spreadsheet_export_of_an_empty_table_still_has_a_header(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, name="Name", primary=True)

    payload = run_export(table, user, {"exporter_type": "xlsx"})

    assert read_xlsx_rows(payload) == [["id", "Name"]]


@pytest.mark.django_db
def test_csv_export_unchanged_by_the_row_id_option(data_fixture):
    """
    The option is honoured by the shared serializer base, so the pre-existing CSV
    exporter must keep working with it too.
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    name_field = data_fixture.create_text_field(table=table, name="Name", primary=True)
    table.get_model().objects.create(**{f"field_{name_field.id}": "Tesla"})

    payload = run_export(table, user, {"exporter_type": "csv", "include_row_id": False})

    rows = list(csv.reader(payload.decode().lstrip("\ufeff").splitlines()))
    assert rows[0] == ["Name"]
    assert rows[1] == ["Tesla"]
