from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Q

from arabase.mcp.protection.models import (
    MCPProtectedField,
    MCPProtectedFieldState,
    MCPProtectionLifecycleStatus,
    MCPProtectionMutationAudit,
    MCPProtectionPolicy,
)
from arabase.mcp.protection.readiness import check_mcp_protection_policy_readiness
from arabase.mcp.protection.vault import (
    VAULT_BACKEND_REDIS,
    MaskTokenVaultUnavailable,
    load_active_fingerprint_key,
    mask_token_vault_backend,
)
from jadawel.core.mcp.models import MCPEndpoint


class Command(BaseCommand):
    help = "Validate the durable MCP protected-field safety boundary."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true")

    def handle(self, *args, **options):
        violations = []
        endpoint_count = MCPEndpoint.objects.count()
        policy_count = MCPProtectionPolicy.objects.count()
        if endpoint_count != policy_count:
            violations.append("POLICY_COUNT_MISMATCH")

        if MCPProtectionPolicy.objects.filter(
            Q(revision__lt=1)
            | Q(access_generation__lt=1)
            | Q(
                lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
                safe_reason_code__gt="",
            )
            | Q(
                lifecycle_status__in=(
                    MCPProtectionLifecycleStatus.SUSPENDED,
                    MCPProtectionLifecycleStatus.PROTECTION_BLOCKED,
                ),
                safe_reason_code="",
            )
        ).exists():
            violations.append("POLICY_STATE_INVALID")

        if (
            MCPProtectedField.objects.annotate(
                endpoint_workspace_id=F("policy__endpoint__workspace_id"),
                field_workspace_id=F("field__table__database__workspace_id"),
            )
            .filter(
                Q(state=MCPProtectedFieldState.ACTIVE, safe_reason_code__gt="")
                | Q(state=MCPProtectedFieldState.SUSPENDED, safe_reason_code="")
                | Q(field__trashed=True)
                | Q(field__table__trashed=True)
                | Q(field__table__database__trashed=True)
                | ~Q(endpoint_workspace_id=F("field_workspace_id"))
            )
            .exists()
        ):
            violations.append("POLICY_RELATION_INVALID")

        if (
            MCPProtectionMutationAudit.objects.exclude(outcome="success").exists()
            or MCPProtectionMutationAudit.objects.filter(row_count__lt=0).exists()
        ):
            violations.append("AUDIT_SCHEMA_INVALID")
        if MCPProtectionMutationAudit.objects.filter(
            protected_field_ids__isnull=True
        ).exists():
            violations.append("AUDIT_BINDING_INVALID")

        if MCPProtectedField.objects.filter(
            state=MCPProtectedFieldState.ACTIVE,
            policy__lifecycle_status=MCPProtectionLifecycleStatus.ACTIVE,
        ).exists():
            try:
                load_active_fingerprint_key()
            except MaskTokenVaultUnavailable:
                violations.append("FINGERPRINT_KEY_INVALID")
            if (
                mask_token_vault_backend() == VAULT_BACKEND_REDIS
                and not settings.MCP_PROTECTION_REDIS_URL
                and not settings.MCP_PROTECTION_ALLOW_SHARED_REDIS
            ):
                violations.append("DEDICATED_REDIS_REQUIRED")
            readiness = check_mcp_protection_policy_readiness()
            if not readiness.ready:
                violations.append(readiness.safe_reason_code)

        if violations and options["strict"]:
            raise CommandError("MCP protection check failed: " + ", ".join(violations))
        if violations:
            self.stdout.write(self.style.WARNING("MCP protection warnings present"))
        else:
            self.stdout.write(self.style.SUCCESS("MCP protection check passed"))
