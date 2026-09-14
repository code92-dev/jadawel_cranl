from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds the ``priority`` column used by the Enhanced Group By feature: sortings and
    group-bys are now applied in the order the user arranged them, not by row id.

    Ported from upstream Baserow 2.3.3 ``database/0211_viewsort_viewgroupby_priority``,
    re-pointed at this fork's migration head (``0212_fileimportjob_importer_type_and_more``).
    The ``db_default``/``default`` values are inlined (32767) instead of importing the
    live ``MAX_ORDER_VALUE`` model constant, as a migration must not depend on model code.
    """

    dependencies = [
        ("database", "0212_fileimportjob_importer_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="viewsort",
            name="priority",
            field=models.PositiveSmallIntegerField(
                db_default=32767,
                default=32767,
                help_text="Position of this sorting in the ordering chain. The "
                "sorting with the lowest priority is applied first.",
            ),
        ),
        migrations.AddField(
            model_name="viewgroupby",
            name="priority",
            field=models.PositiveSmallIntegerField(
                db_default=32767,
                default=32767,
                help_text="Position of this group by in the ordering chain. The "
                "group by with the lowest priority is applied first.",
            ),
        ),
        migrations.AlterModelOptions(
            name="viewsort",
            options={"ordering": ("priority", "id")},
        ),
        migrations.AlterModelOptions(
            name="viewgroupby",
            options={"ordering": ("priority", "id")},
        ),
    ]
