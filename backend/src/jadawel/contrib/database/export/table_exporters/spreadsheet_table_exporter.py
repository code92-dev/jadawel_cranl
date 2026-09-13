"""
XLSX and ODS table exporters.

Both are additive: they register against the existing
:data:`jadawel.contrib.database.export.registries.table_exporter_registry`, so an
export runs through the normal export job, which keeps the permission checks,
the progress/cancellation signalling and the download lifecycle the CSV
exporter already has. Nothing here downloads rows into the browser.

Both emit computed cell values, never live spreadsheet formulas (see
:func:`_spreadsheet_text`), and both stream straight into the destination file
handle, so the worker's memory does not grow with the size of the table.

Why ODS does not use a third-party writer
-----------------------------------------
`odfpy` was the obvious candidate, but a spike writing 200,000 rows peaked at
1233 MB and took 583 s, because it builds the whole document as a DOM before
saving. The export worker's container limit is 768 MB, so odfpy would have
OOM-killed a representative export. An ODS file is a ZIP whose `content.xml`
can be written sequentially, so this module writes the package directly with
the standard library and streams the sheet XML: the same 200,000 rows peak at
354 MB and take 4.4 s, and the result opens in LibreOffice and Excel.
"""

from collections import OrderedDict
from typing import List, Optional, Type
from xml.sax.saxutils import escape
import zipfile

from jadawel.contrib.database.api.export.serializers import (
    BaseExporterOptionsSerializer,
    ExcelExporterOptionsSerializer,
    OdsExporterOptionsSerializer,
)
from jadawel.contrib.database.export.file_writer import FileWriter, QuerysetSerializer
from jadawel.contrib.database.export.registries import TableExporter
from jadawel.contrib.database.views.view_types import GridViewType

# A leading character that a spreadsheet application treats as the start of a
# formula. A cell whose text begins with one of these is written as an explicit
# text cell, otherwise opening a downloaded workbook would execute user data
# (CWE-1236). The tab/CR/LF cases matter because some parsers skip leading
# whitespace before deciding.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "|", "%", "\t", "\r", "\n")

ODS_MIMETYPE = "application/vnd.oasis.opendocument.spreadsheet"


def _spreadsheet_text(value) -> str:
    """
    Convert a value to the string that will be stored in a spreadsheet cell.

    A value that would be interpreted as a formula is prefixed with an
    apostrophe, the conventional spreadsheet escape for "this is text", so the
    stored string still reads as the original value in the cell.

    :param value: The already-exported field value.
    :return: The text to place in the cell.
    """

    text = str(value)
    if text.startswith(_FORMULA_PREFIXES):
        return "'" + text
    return text


class SpreadsheetQuerysetSerializer(QuerysetSerializer):
    """
    Shared behaviour for the workbook exporters: build the header row and
    iterate the queryset through the paginated file writer.
    """

    def __init__(self, queryset, ordered_field_objects, **kwargs):
        super().__init__(queryset, ordered_field_objects, **kwargs)

        self.headers = OrderedDict()
        if self.include_row_id:
            self.headers["id"] = "id"

        for field_object in self.ordered_field_objects:
            self.headers[field_object["name"]] = field_object["field"].name

    def _header_row(self) -> List[str]:
        return [str(value) for value in self.headers.values()]

    def _serialize_row(self, row) -> List[str]:
        return [
            _spreadsheet_text(field_serializer(row)[2])
            for field_serializer in self.field_serializers
        ]


class XlsxQuerysetSerializer(SpreadsheetQuerysetSerializer):
    """
    Writes an .xlsx workbook using openpyxl's write-only mode, which emits rows
    to the file as they are appended instead of holding the worksheet in memory.
    """

    def write_to_file(
        self,
        file_writer: FileWriter,
        export_charset: Optional[str] = None,
        excel_include_header: bool = True,
        **kwargs,
    ):
        """
        :param file_writer: The file writer wrapping the destination file.
        :param export_charset: Accepted for interface compatibility; the workbook
            is always UTF-8.
        :param excel_include_header: Whether to write the field names as the
            first row.
        """

        # openpyxl is imported lazily so importing this module (and therefore the
        # exporter registry) does not cost the workbook library on every worker.
        from openpyxl import Workbook
        from openpyxl.cell.cell import WriteOnlyCell

        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet()

        def cell(value: str):
            cell = WriteOnlyCell(worksheet, value=value)
            # openpyxl types a string beginning with "=" as a live formula; force
            # an explicit string cell for every value we write.
            cell.data_type = "s"
            return cell

        if excel_include_header:
            worksheet.append([cell(value) for value in self._header_row()])

        def write_row(row, _):
            worksheet.append([cell(value) for value in self._serialize_row(row)])

        file_writer.write_rows(self.queryset, write_row)

        workbook.save(file_writer._file)


class OdsQuerysetSerializer(SpreadsheetQuerysetSerializer):
    """
    Writes an .ods package by streaming `content.xml` into a ZIP, so memory use
    stays flat regardless of how many rows the table holds.
    """

    # The manifest and the shared document skeleton are fixed for our purposes:
    # a single sheet with no declared styles. Keeping them as constants avoids
    # an XML library dependency for output that never changes shape.
    _MANIFEST = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest '
        'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" '
        'manifest:version="1.2">'
        '<manifest:file-entry manifest:full-path="/" '
        f'manifest:media-type="{ODS_MIMETYPE}"/>'
        '<manifest:file-entry manifest:full-path="content.xml" '
        'manifest:media-type="text/xml"/>'
        "</manifest:manifest>"
    )
    _CONTENT_HEAD = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<office:document-content "
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        'office:version="1.2">'
        "<office:body><office:spreadsheet>"
    )
    _CONTENT_TAIL = (
        "</office:spreadsheet></office:body></office:document-content>"
    )

    def write_to_file(
        self,
        file_writer: FileWriter,
        export_charset: Optional[str] = None,
        excel_include_header: bool = True,
        **kwargs,
    ):
        """
        :param file_writer: The file writer wrapping the destination file.
        :param export_charset: Accepted for interface compatibility; the package
            is always UTF-8.
        :param excel_include_header: Whether to write the field names as the
            first row.
        """

        sheet_name = escape("export", {'"': "&quot;"})

        with zipfile.ZipFile(file_writer._file, "w", zipfile.ZIP_DEFLATED) as archive:
            # The mimetype entry must be first and stored uncompressed, which is
            # what lets a reader identify the file as ODF without unpacking it.
            archive.writestr(
                zipfile.ZipInfo("mimetype"), ODS_MIMETYPE, zipfile.ZIP_STORED
            )
            archive.writestr("META-INF/manifest.xml", self._MANIFEST)

            with archive.open("content.xml", "w") as content:
                content.write(self._CONTENT_HEAD.encode("utf-8"))
                content.write(
                    f'<table:table table:name="{sheet_name}">'.encode("utf-8")
                )

                def write_cells(values):
                    content.write(b"<table:table-row>")
                    for value in values:
                        content.write(
                            (
                                '<table:table-cell office:value-type="string">'
                                f"<text:p>{escape(value)}</text:p>"
                                "</table:table-cell>"
                            ).encode("utf-8")
                        )
                    content.write(b"</table:table-row>")

                if excel_include_header:
                    write_cells(self._header_row())

                def write_row(row, _):
                    write_cells(self._serialize_row(row))

                file_writer.write_rows(self.queryset, write_row)

                content.write(b"</table:table>")
                content.write(self._CONTENT_TAIL.encode("utf-8"))


class XlsxTableExporter(TableExporter):
    type = "xlsx"

    @property
    def option_serializer_class(self) -> Type[BaseExporterOptionsSerializer]:
        return ExcelExporterOptionsSerializer

    @property
    def can_export_table(self) -> bool:
        return True

    @property
    def supported_views(self) -> List[str]:
        return [GridViewType.type]

    @property
    def file_extension(self) -> str:
        return ".xlsx"

    @property
    def queryset_serializer_class(self):
        return XlsxQuerysetSerializer


class OdsTableExporter(TableExporter):
    type = "ods"

    @property
    def option_serializer_class(self) -> Type[BaseExporterOptionsSerializer]:
        return OdsExporterOptionsSerializer

    @property
    def can_export_table(self) -> bool:
        return True

    @property
    def supported_views(self) -> List[str]:
        return [GridViewType.type]

    @property
    def file_extension(self) -> str:
        return ".ods"

    @property
    def queryset_serializer_class(self):
        return OdsQuerysetSerializer
