"""Admin endpoints behind the Backup section.

Everything here is `IsAdminUser`: the run history names object keys and can
carry an error message from the storage provider, and the restore endpoint runs
pg_restore.
"""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from arabase.api.backup.serializers import (
    BackupOverviewSerializer,
    BackupRunSerializer,
    RestoreBackupResponseSerializer,
    RestoreBackupSerializer,
    UpdateBackupScheduleSerializer,
)
from arabase.backup.config import BackupConfig
from arabase.backup.handler import get_health, republish_schedule
from arabase.backup.models import BackupRun, BackupSchedule
from arabase.backup.restore import RestoreError
from jadawel.api.decorators import validate_body
from jadawel.api.schemas import get_error_schema

MAX_RUNS = 50
"""The history is a monitoring aid, not an archive. Fifty rows covers roughly
two days of hourly backups, which is as far back as a `did it run?` question
ever reaches."""


def overview_payload() -> dict:
    config = BackupConfig.from_env()
    schedule = BackupSchedule.get_solo()
    health = get_health()

    return {
        "enabled": config.enabled,
        "schedule": {"frequency": schedule.frequency, "crontab": schedule.crontab},
        "health": {
            "status": health.status,
            "healthy": health.healthy,
            "last_success_on": health.last_success_on,
            "next_run_on": health.next_run_on,
            "configuration_errors": health.configuration_errors,
            "last_run": BackupRunSerializer(health.last_run).data
            if health.last_run
            else None,
        },
    }


class AdminBackupView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Arabase backup"],
        operation_id="get_backup_overview",
        description=(
            "Whether backups are enabled, how often they run, and whether they "
            "can currently be relied on."
        ),
        responses={200: BackupOverviewSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(overview_payload())

    @extend_schema(
        tags=["Arabase backup"],
        operation_id="update_backup_schedule",
        description=(
            "Changes how often backups run. Applies immediately: the schedule "
            "is republished to the beat scheduler rather than waiting for a "
            "redeploy."
        ),
        request=UpdateBackupScheduleSerializer,
        responses={
            200: BackupOverviewSerializer,
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
        },
    )
    @validate_body(UpdateBackupScheduleSerializer, return_validated=True)
    def patch(self, request: Request, data: dict) -> Response:
        schedule = BackupSchedule.get_solo()
        schedule.frequency = data["frequency"]
        schedule.save()

        republish_schedule()

        return Response(overview_payload())


class AdminBackupRunsView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Arabase backup"],
        operation_id="list_backup_runs",
        description=(
            "The most recent backup attempts, newest first. Failed attempts are "
            "included: a failed run uploads nothing, so listing the bucket "
            "would not show it."
        ),
        responses={200: BackupRunSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        runs = BackupRun.objects.all()[:MAX_RUNS]
        return Response(BackupRunSerializer(runs, many=True).data)


class AdminBackupRunNowView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Arabase backup"],
        operation_id="run_backup_now",
        description=(
            "Queues a backup immediately. Returns as soon as it is queued; the "
            "run appears in the history with a `running` status."
        ),
        request=None,
        responses={202: BackupRunSerializer},
    )
    def post(self, request: Request) -> Response:
        from arabase.tasks import backup_database

        backup_database.delay(trigger=BackupRun.TRIGGER_MANUAL)
        return Response(status=202, data=None)


class AdminBackupRestoreView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        tags=["Arabase backup"],
        operation_id="restore_backup",
        description=(
            "Restores a backup into a database you nominate. It will not "
            "restore over the live database: the target is validated against "
            "the running connection and rejected if it matches. Verify the "
            "restored copy and switch over yourself."
        ),
        request=RestoreBackupSerializer,
        responses={
            202: RestoreBackupResponseSerializer,
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
        },
    )
    @validate_body(RestoreBackupSerializer, return_validated=True)
    def post(self, request: Request, data: dict) -> Response:
        from arabase.backup.restore import redact, seal_target, validate_target
        from arabase.tasks import restore_backup_task

        # Validated synchronously so an unusable target is a 400 the operator
        # sees, rather than a task that fails somewhere they have to go looking.
        try:
            validate_target(data["target_database_url"])
        except RestoreError as exc:
            return Response(
                {
                    "error": "ERROR_INVALID_RESTORE_TARGET",
                    "detail": str(exc),
                },
                status=400,
            )

        restore_backup_task.delay(data["key"], seal_target(data["target_database_url"]))

        return Response(
            status=202,
            data={
                "key": data["key"],
                "target": redact(data["target_database_url"]),
            },
        )
