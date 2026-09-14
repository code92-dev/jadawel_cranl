"""
Boundary tests for the XLSX and ODS spreadsheet exporters' format limits.

XLSX hard-limits a worksheet to 1,048,576 rows x 16,384 columns; ODS has no
format-imposed row limit, but a named row/column pair is defined anyway so
both formats fail the same way. Exceeding a limit must raise a translated,
actionable error instead of streaming a file a spreadsheet application would
silently truncate, and a failed job must not leave a partial downloadable
file behind.

These are the RED phase of the remediation plan: they capture behaviour that
does not exist yet. The module imports the named limit constants at the top,
so today the whole file fails at *collection* with:

    ImportError: cannot import name 'XLSX_MAX_ROWS' ... from
    'jadawel.contrib.database.export.table_exporters.spreadsheet_table_exporter'

That ImportError is the expected, documented failure. Once the constants
land, every test below must hold. All tests stay fast: limits are
monkeypatched down to 2, at most 3 rows/fields are created, and storage is a
MagicMock backed by an in-memory buffer.
"""

from contextlib import contextmanager
from io import BytesIO
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree
import zipfile

import pytest

from jadawel.contrib.database.export.models import (
    EXPORT_JOB_FAILED_STATUS,
    EXPORT_JOB_FINISHED_STATUS,
)
from jadawel.contrib.database.export.table_exporters import (
    spreadsheet_table_exporter,
)
from jadawel.contrib.database.export.table_exporters.spreadsheet_table_exporter import (
    ODS_MAX_COLUMNS,
    ODS_MAX_ROWS,
    XLSX_MAX_COLUMNS,
    XLSX_MAX_ROWS,
)

TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"


def read_xlsx_rows(payload):
    from openpyxl import load_workbook

    workbook = load_workbook(BytesIO(payload), read_only=True)
    worksheet = workbook.active
    return [[cell for cell in row] for row in worksheet.iter_rows(values_only=True)]


def read_ods_rows(payload):
    """Extract the sheet as a list of rows of cell text, straight from the zip."""

    with zipfile.ZipFile(BytesIO(payload)) as archive:
        content = ElementTree.fromstring(archive.read("content.xml"))

    rows = []
    for row in content.iter(f"{{{TABLE_NS}}}table-row"):
        values = []
        for cell in row.findall(f"{{{TABLE_NS}}}table-cell"):
            paragraph = cell.find(f"{{{TEXT_NS}}}p")
            values.append(paragraph.text if paragraph is not None else None)
        rows.append(values)
    return rows


def make_table_with_rows(data_fixture, row_count):
    """A table with a single primary text field and the given number of rows."""

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    name_field = data_fixture.create_text_field(table=table, name="Name", primary=True)
    model = table.get_model()
    for index in range(row_count):
        model.objects.create(**{f"field_{name_field.id}": f"row-{index}"})
    return user, table


def make_table_with_fields(data_fixture, field_count):
    """A table with the given number of text fields (the first one primary)."""

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, name="Primary", primary=True)
    for index in range(field_count - 1):
        data_fixture.create_text_field(table=table, name=f"Field {index}")
    return user, table


@contextmanager
def export_job(table, user, options):
    """
    Create a pending export job whose storage is an in-memory mock.

    Yields ``(handler, job, storage_mock, buffer)`` so the caller decides
    whether running the job may raise. The mock mirrors how the CSV export
    tests stub storage, and the buffer lets a test inspect exactly what the
    job left behind in "storage".
    """

    storage_mock = MagicMock()
    buffer = BytesIO()
    storage_mock.open.return_value = buffer
    buffer.close = lambda: None

    with patch("jadawel.core.storage.get_default_storage", return_value=storage_mock):
        from jadawel.contrib.database.export.handler import ExportHandler

        handler = ExportHandler()
        job = handler.create_pending_export_job(user, table, None, options)
        yield handler, job, storage_mock, buffer


@pytest.mark.django_db
def test_spreadsheet_limit_constants_match_the_format_limits():
    """
    The named limits must match what the formats actually allow: XLSX caps a
    worksheet at 1,048,576 rows and 16,384 columns. The ODS pair has no
    format-imposed row bound but must still be defined so both exporters
    share one enforcement path.
    """

    assert XLSX_MAX_ROWS == 1_048_576
    assert XLSX_MAX_COLUMNS == 16_384
    assert ODS_MAX_ROWS >= 1
    assert ODS_MAX_COLUMNS >= 1


@pytest.mark.django_db
@pytest.mark.parametrize("exporter_type", ["xlsx", "ods"])
def test_export_exceeding_the_row_limit_fails_without_a_downloadable_file(
    data_fixture, monkeypatch, exporter_type
):
    """
    A table with more rows than the exporter allows must fail the job with an
    actionable error about the row limit, and must not leave a partial
    workbook behind that a user could download.
    """

    if exporter_type == "xlsx":
        monkeypatch.setattr(spreadsheet_table_exporter, "XLSX_MAX_ROWS", 2)
    else:
        monkeypatch.setattr(spreadsheet_table_exporter, "ODS_MAX_ROWS", 2)

    user, table = make_table_with_rows(data_fixture, row_count=3)

    with export_job(table, user, {"exporter_type": exporter_type}) as (
        handler,
        job,
        storage_mock,
        buffer,
    ):
        with pytest.raises(Exception, match="rows"):
            handler.run_export_job(job)

    job.refresh_from_db()
    assert job.state == EXPORT_JOB_FAILED_STATUS
    assert "rows" in job.error
    # Nothing the job wrote may be a complete, downloadable file: the fix
    # validates before writing (or stops generation at the boundary), so the
    # storage entry holds at most a partial stream, never a valid workbook.
    assert not zipfile.is_zipfile(BytesIO(buffer.getvalue()))


@pytest.mark.django_db
@pytest.mark.parametrize("exporter_type", ["xlsx", "ods"])
def test_export_exceeding_the_column_limit_fails_before_writing_rows(
    data_fixture, monkeypatch, exporter_type
):
    """
    A table with more fields than the exporter allows must fail with an
    actionable error about the column limit; the field count is known before
    any row is generated, so the error must come before row iteration.
    """

    if exporter_type == "xlsx":
        monkeypatch.setattr(spreadsheet_table_exporter, "XLSX_MAX_COLUMNS", 2)
    else:
        monkeypatch.setattr(spreadsheet_table_exporter, "ODS_MAX_COLUMNS", 2)

    user, table = make_table_with_fields(data_fixture, field_count=3)

    with export_job(table, user, {"exporter_type": exporter_type}) as (
        handler,
        job,
        storage_mock,
        buffer,
    ):
        with pytest.raises(Exception, match="columns"):
            handler.run_export_job(job)

    job.refresh_from_db()
    assert job.state == EXPORT_JOB_FAILED_STATUS
    assert "columns" in job.error
    assert not zipfile.is_zipfile(BytesIO(buffer.getvalue()))


@pytest.mark.django_db
@pytest.mark.parametrize("exporter_type", ["xlsx", "ods"])
def test_export_exactly_at_the_row_limit_still_succeeds(
    data_fixture, monkeypatch, exporter_type
):
    """
    The anti-regression guard: a table exactly at the limit exports fine and
    every row is present. The header is disabled so the limit can be set to
    exactly the number of data rows without having to budget for it.
    """

    if exporter_type == "xlsx":
        monkeypatch.setattr(spreadsheet_table_exporter, "XLSX_MAX_ROWS", 2)
    else:
        monkeypatch.setattr(spreadsheet_table_exporter, "ODS_MAX_ROWS", 2)

    user, table = make_table_with_rows(data_fixture, row_count=2)

    with export_job(
        table,
        user,
        {"exporter_type": exporter_type, "excel_include_header": False},
    ) as (handler, job, storage_mock, buffer):
        handler.run_export_job(job)

    job.refresh_from_db()
    assert job.state == EXPORT_JOB_FINISHED_STATUS
    payload = buffer.getvalue()
    if exporter_type == "xlsx":
        rows = read_xlsx_rows(payload)
    else:
        rows = read_ods_rows(payload)
    # The row-id column is included by default, so each row is [id, "row-N"].
    assert [row[-1] for row in rows] == ["row-0", "row-1"]
    assert len(rows) == 2


@pytest.mark.django_db
@pytest.mark.parametrize("exporter_type", ["xlsx", "ods"])
def test_header_row_consumes_one_row_of_the_limit(
    data_fixture, monkeypatch, exporter_type
):
    """
    The written header shares the row budget, so a table whose rows plus the
    header exactly fill the limit must still export completely.
    """

    if exporter_type == "xlsx":
        monkeypatch.setattr(spreadsheet_table_exporter, "XLSX_MAX_ROWS", 3)
    else:
        monkeypatch.setattr(spreadsheet_table_exporter, "ODS_MAX_ROWS", 3)

    user, table = make_table_with_rows(data_fixture, row_count=2)

    with export_job(table, user, {"exporter_type": exporter_type}) as (
        handler,
        job,
        storage_mock,
        buffer,
    ):
        handler.run_export_job(job)

    job.refresh_from_db()
    assert job.state == EXPORT_JOB_FINISHED_STATUS
    payload = buffer.getvalue()
    if exporter_type == "xlsx":
        rows = read_xlsx_rows(payload)
    else:
        rows = read_ods_rows(payload)
    assert rows[0] == ["id", "Name"]
    assert [row[1] for row in rows[1:]] == ["row-0", "row-1"]
