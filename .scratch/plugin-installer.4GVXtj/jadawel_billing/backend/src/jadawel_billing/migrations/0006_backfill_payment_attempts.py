from typing import Any

from django.db import migrations


def create_attempts_for_existing_orders(apps: Any, schema_editor: Any) -> None:
    BillingOrder = apps.get_model("jadawel_billing", "BillingOrder")
    PaymentAttempt = apps.get_model("jadawel_billing", "PaymentAttempt")
    PaymentAttempt.objects.bulk_create(
        [
            PaymentAttempt(order_id=order.pk, given_id=order.payment_id)
            for order in BillingOrder.objects.all().only("pk", "payment_id")
            if not PaymentAttempt.objects.filter(order_id=order.pk).exists()
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        (
            "jadawel_billing",
            "0005_paymentattempt_alter_providerevent_payment_id_and_more",
        )
    ]

    operations = [
        migrations.RunPython(
            create_attempts_for_existing_orders, migrations.RunPython.noop
        )
    ]
