from typing import Any

from django.db import migrations, models


def copy_order_mode(apps: Any, schema_editor: Any) -> None:
    PaymentAttempt = apps.get_model("jadawel_billing", "PaymentAttempt")
    for attempt in PaymentAttempt.objects.select_related("order").all().iterator():
        attempt.provider_mode = attempt.order.mode
        attempt.save(update_fields=["provider_mode"])


class Migration(migrations.Migration):
    dependencies = [
        ("jadawel_billing", "0008_providerevent_updated_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentattempt",
            name="provider_mode",
            field=models.CharField(default="test", editable=False, max_length=4),
        ),
        migrations.RunPython(copy_order_mode, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="paymentattempt",
            name="billing_unique_provider_payment",
        ),
        migrations.AddConstraint(
            model_name="paymentattempt",
            constraint=models.UniqueConstraint(
                condition=models.Q(("provider_payment_id__isnull", False)),
                fields=("provider_mode", "provider_payment_id"),
                name="billing_unique_provider_payment_by_mode",
            ),
        ),
    ]
