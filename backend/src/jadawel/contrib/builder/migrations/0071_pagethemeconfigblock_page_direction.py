from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("builder", "0070_columnelement_layout_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="pagethemeconfigblock",
            name="page_direction",
            field=models.CharField(
                choices=[("auto", "Auto"), ("rtl", "Rtl"), ("ltr", "Ltr")],
                db_default="auto",
                default="auto",
                help_text="The direction of the page content: auto, rtl or ltr",
                max_length=8,
            ),
        ),
    ]
