import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jadawel_billing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="billingaccount",
            name="suspended",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="ManualEntitlementGrant",
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
                ("seat_limit", models.PositiveIntegerField()),
                ("starts_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("reason", models.CharField(max_length=500)),
                ("revision", models.PositiveIntegerField(default=1)),
                (
                    "account",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="manual_grant",
                        to="jadawel_billing.billingaccount",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="jadawel_billing.plan",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("seat_limit__gte", 1)),
                        name="billing_grant_positive_seats",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("expires_at__isnull", True),
                            ("expires_at__gt", models.F("starts_at")),
                            _connector="OR",
                        ),
                        name="billing_grant_valid_period",
                    ),
                ],
            },
        ),
    ]
