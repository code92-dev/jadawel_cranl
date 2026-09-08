import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "jadawel_billing",
            "0010_subscription_next_retry_at_subscription_retry_count_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="billingorder",
            name="purpose",
            field=models.CharField(
                choices=[("initial", "Initial"), ("seat_increase", "Seat Increase")],
                default="initial",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="billingorder",
            name="subscription",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="change_orders",
                to="jadawel_billing.subscription",
            ),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="source_order",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="source_subscription",
                to="jadawel_billing.billingorder",
            ),
        ),
    ]
