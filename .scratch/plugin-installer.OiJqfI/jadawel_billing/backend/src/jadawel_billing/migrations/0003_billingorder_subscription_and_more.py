import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jadawel_billing", "0002_billingaccount_suspended_manualentitlementgrant"),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingOrder",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("seats", models.PositiveIntegerField(default=1)),
                ("amount", models.PositiveIntegerField()),
                ("currency", models.CharField(default="SAR", max_length=3)),
                (
                    "interval",
                    models.CharField(
                        choices=[("MONTH", "Month"), ("YEAR", "Year")], max_length=5
                    ),
                ),
                (
                    "payment_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("mode", models.CharField(default="test", max_length=4)),
                ("status", models.CharField(default="pending", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("paid_at", models.DateTimeField(null=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="jadawel_billing.billingaccount",
                    ),
                ),
                (
                    "price",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="jadawel_billing.planprice",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("seats", models.PositiveIntegerField()),
                ("period_start", models.DateTimeField()),
                ("period_end", models.DateTimeField()),
                ("cancel_at_period_end", models.BooleanField(default=True)),
                (
                    "account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="jadawel_billing.billingaccount",
                    ),
                ),
                (
                    "price",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="jadawel_billing.planprice",
                    ),
                ),
                (
                    "source_order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="jadawel_billing.billingorder",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="billingorder",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "pending")),
                fields=("account",),
                name="billing_one_pending_order",
            ),
        ),
        migrations.AddConstraint(
            model_name="billingorder",
            constraint=models.CheckConstraint(
                condition=models.Q(("seats__gte", 1)),
                name="billing_order_positive_seats",
            ),
        ),
    ]
