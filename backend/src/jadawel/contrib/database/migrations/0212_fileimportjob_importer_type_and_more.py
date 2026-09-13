from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds the two metadata columns the spreadsheet importer needs: which frontend
    importer parsed the upload, and the original file name (kept so the created
    table can be named after the workbook rather than the temporary upload).

    Ported from upstream Baserow 2.3.3 `database/0210_fileimportjob_importer_type_and_more`,
    re-pointed at this fork's migration head (`0211_jadawel_rename_table_usage_functions`).
    """

    dependencies = [
        ("database", "0211_jadawel_rename_table_usage_functions"),
    ]

    operations = [
        migrations.AddField(
            model_name="fileimportjob",
            name="importer_type",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="The frontend importer identifier used to parse the file.",
            ),
        ),
        migrations.AddField(
            model_name="fileimportjob",
            name="original_file_name",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="The original name of the uploaded file.",
            ),
        ),
    ]
