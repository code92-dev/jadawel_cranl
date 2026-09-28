# Jadawel fork: the widget board moves from 3 columns and 160 px rows to 12
# columns and 72 px rows, and widgets gain an `appearance` dict.

import django.core.validators
from django.db import migrations, models

WIDTH_SCALE = 4
"""One of the old 3 columns is 4 of the new 12."""

HEIGHT_SCALE = 2
"""One old 160 px row is two new 72 px rows plus the 16 px gap between them."""


def forwards(apps, schema_editor):
    Widget = apps.get_model("dashboard", "Widget")
    Widget.objects.update(
        width=models.F("width") * WIDTH_SCALE,
        height=models.F("height") * HEIGHT_SCALE,
    )


def backwards(apps, schema_editor):
    Widget = apps.get_model("dashboard", "Widget")
    for widget in Widget.objects.only("id", "width", "height"):
        widget.width = min(3, max(1, round(widget.width / WIDTH_SCALE)))
        widget.height = min(3, max(1, round(widget.height / HEIGHT_SCALE)))
        widget.save(update_fields=["width", "height"])


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0004_widget_width_height"),
    ]

    operations = [
        migrations.AlterField(
            model_name="widget",
            name="width",
            field=models.PositiveSmallIntegerField(
                default=12,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(12),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="widget",
            name="height",
            field=models.PositiveSmallIntegerField(
                default=4,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(12),
                ],
            ),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AddField(
            model_name="widget",
            name="appearance",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Presentation options the frontend reads, such as the "
                "accent colour, icon and number format.",
            ),
        ),
    ]
