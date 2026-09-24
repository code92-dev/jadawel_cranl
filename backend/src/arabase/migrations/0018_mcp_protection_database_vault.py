# MCP protection: the PostgreSQL mask-token vault and two new readiness reasons.
#
# Only the vault table and the reason choices are here. `makemigrations arabase`
# also reports the pending core `UserProfile.language` choices change; that is
# unrelated to this app and left out, as in 0017.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arabase", "0017_table_access_grants"),
        ("core", "0117_jadawel_rename_show_help_request"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mcpprotectedfield",
            name="safe_reason_code",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "None"),
                    ("POLICY_COUNT_MISMATCH", "Policy count mismatch"),
                    ("POLICY_STATE_INVALID", "Policy state invalid"),
                    ("POLICY_RELATION_INVALID", "Policy relation invalid"),
                    ("WORKSPACE_SUSPENDED", "Workspace suspended"),
                    ("MEMBERSHIP_CHANGED", "Membership changed"),
                    ("USER_INACTIVE", "User inactive"),
                    ("CREDENTIAL_ROTATED", "Credential rotated"),
                    (
                        "FIELD_TYPE_CONVERSION_UNSUPPORTED",
                        "Field type conversion requires review",
                    ),
                    ("PROTECTION_REDIS_UNAVAILABLE", "Protection Redis unavailable"),
                    ("PROTECTION_VAULT_UNAVAILABLE", "Protection vault unavailable"),
                    (
                        "PROTECTION_KEY_UNAVAILABLE",
                        "Protection fingerprint key unavailable",
                    ),
                ],
                default="",
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="mcpprotectionpolicy",
            name="safe_reason_code",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "None"),
                    ("POLICY_COUNT_MISMATCH", "Policy count mismatch"),
                    ("POLICY_STATE_INVALID", "Policy state invalid"),
                    ("POLICY_RELATION_INVALID", "Policy relation invalid"),
                    ("WORKSPACE_SUSPENDED", "Workspace suspended"),
                    ("MEMBERSHIP_CHANGED", "Membership changed"),
                    ("USER_INACTIVE", "User inactive"),
                    ("CREDENTIAL_ROTATED", "Credential rotated"),
                    (
                        "FIELD_TYPE_CONVERSION_UNSUPPORTED",
                        "Field type conversion requires review",
                    ),
                    ("PROTECTION_REDIS_UNAVAILABLE", "Protection Redis unavailable"),
                    ("PROTECTION_VAULT_UNAVAILABLE", "Protection vault unavailable"),
                    (
                        "PROTECTION_KEY_UNAVAILABLE",
                        "Protection fingerprint key unavailable",
                    ),
                ],
                default="",
                max_length=64,
            ),
        ),
        migrations.CreateModel(
            name="MCPMaskTokenRecord",
            fields=[
                (
                    "digest",
                    models.CharField(max_length=64, primary_key=True, serialize=False),
                ),
                ("expires_at", models.DateTimeField()),
                ("record", models.JSONField()),
                (
                    "endpoint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="core.mcpendpoint",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["expires_at"], name="ara_mcp_token_expiry_idx"
                    ),
                    models.Index(
                        fields=["endpoint", "expires_at"],
                        name="ara_mcp_token_ep_expiry_idx",
                    ),
                ],
            },
        ),
    ]
