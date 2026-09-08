import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Plan",
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
                ("code", models.SlugField(unique=True)),
                ("name", models.CharField(max_length=100)),
                (
                    "kind",
                    models.CharField(
                        choices=[("INDIVIDUAL", "Individual"), ("TEAM", "Team")],
                        max_length=10,
                    ),
                ),
                ("available", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="BillingAuditEvent",
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
                ("action", models.CharField(max_length=60)),
                ("target", models.CharField(max_length=80)),
                ("details", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PlanPrice",
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
                ("amount", models.PositiveIntegerField()),
                (
                    "currency",
                    models.CharField(default="SAR", editable=False, max_length=3),
                ),
                (
                    "interval",
                    models.CharField(
                        choices=[("MONTH", "Month"), ("YEAR", "Year")], max_length=5
                    ),
                ),
                ("available", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="prices",
                        to="jadawel_billing.plan",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BillingAccount",
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
                (
                    "kind",
                    models.CharField(
                        choices=[("INDIVIDUAL", "Individual"), ("TEAM", "Team")],
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "responsible_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("kind", "INDIVIDUAL")),
                        fields=("responsible_user",),
                        name="billing_one_personal_account",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("kind__in", ["INDIVIDUAL", "TEAM"])),
                        name="billing_account_valid_kind",
                    ),
                ],
            },
        ),
    ]
