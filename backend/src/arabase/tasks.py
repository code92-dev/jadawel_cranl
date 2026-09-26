"""Celery tasks for the Jadawel fork.

Autodiscovered by ``jadawel.config.celery``: ``arabase`` is an installed app,
so this module needs no registration in ``ArabaseConfig.ready()``.
"""

import logging
from datetime import timedelta

from django.conf import settings

from celery_singleton import Singleton

from arabase.backup.config import BackupConfig
from arabase.backup.runner import BackupError, dump_timeout_seconds, run_backup
from jadawel.config.celery import app

logger = logging.getLogger(__name__)

BACKUP_TASK_NAME = "arabase-backup-database"
"""RedBeat entry name. Stable so that republishing the schedule replaces the
existing entry rather than adding a second one beside it."""

# Derived from the dump timeout rather than fixed, so that raising
# JADAWEL_BACKUP_TIMEOUT_SECONDS for a large database actually takes effect
# instead of being cut short by a hard-coded limit an operator cannot see.
# The margin covers the upload and the prune that follow the dump.
_SOFT_TIME_LIMIT = dump_timeout_seconds() + 600


@app.task(
    name="arabase.tasks.reconcile_local_template_catalog",
    base=Singleton,
    raise_on_duplicate=False,
    queue="export",
    time_limit=settings.JADAWEL_SYNC_TEMPLATES_TIME_LIMIT,
    lock_expiry=settings.JADAWEL_SYNC_TEMPLATES_TIME_LIMIT,
)
def reconcile_local_template_catalog_task():
    """Ensure the database picker matches the six bundled local templates."""

    from arabase.template_catalog import reconcile_local_template_catalog

    return reconcile_local_template_catalog()


@app.task(
    name="arabase.tasks.backup_database",
    queue="export",
    # The deployment runs one worker at concurrency 1, so a dump occupies the
    # only slot for its duration. The soft limit lets a stuck pg_dump be
    # interrupted rather than blocking exports and imports indefinitely.
    soft_time_limit=_SOFT_TIME_LIMIT,
    time_limit=_SOFT_TIME_LIMIT + 300,
)
def backup_database(trigger=None):
    from arabase.backup.handler import record_run
    from arabase.backup.models import BackupRun

    config = BackupConfig.from_env()
    if not config.enabled:
        logger.debug("Skipping the database backup: JADAWEL_BACKUP_ENABLED is not set.")
        return

    trigger = trigger or BackupRun.TRIGGER_SCHEDULED

    # The row is written before the dump starts and updated either way, so a run
    # that fails leaves evidence. A failed run uploads nothing, so without this
    # the only trace would be a log line nobody reads.
    with record_run(trigger) as run:
        try:
            result = run_backup(config)
        except BackupError:
            # Logged with the traceback so it reaches Sentry once a DSN is set;
            # re-raised so the task is recorded as failed rather than silently
            # succeeding, which is the failure mode that makes a backup useless.
            logger.exception("The scheduled database backup failed.")
            raise
        run.mark_succeeded(result)

    return {"key": result.key, "size_bytes": result.size_bytes}


@app.task(
    name="arabase.tasks.restore_backup",
    queue="export",
    soft_time_limit=3600,
    time_limit=3900,
)
def restore_backup_task(key: str, sealed_target: str):
    """Restore ``key`` into a database that is not the live one.

    Deliberately takes an explicit target: there is no code path here that can
    write over the running database. The target arrives sealed
    (``restore.seal_target``) so its password never sits in the broker.
    """

    from arabase.backup.restore import restore_backup, unseal_target

    result = restore_backup(key, unseal_target(sealed_target))
    return {"key": result.key, "target": result.target}


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_backup_tasks(sender, **kwargs):
    """Register the periodic backup from the stored schedule.

    The frequency comes from the database so the admin page can change it;
    JADAWEL_BACKUP_ENABLED still decides whether the feature runs at all.
    Reading a model here is guarded because this signal also fires in contexts
    where the database is not reachable yet, such as during a build.
    """

    config = BackupConfig.from_env()
    if not config.enabled:
        return

    from arabase.backup.handler import parse_crontab

    try:
        from arabase.backup.models import BackupSchedule

        schedule_expression = BackupSchedule.get_solo().crontab
    except Exception:
        schedule_expression = config.crontab
        logger.warning(
            "Could not read the backup schedule from the database; falling back to %s.",
            schedule_expression,
        )

    sender.add_periodic_task(
        parse_crontab(schedule_expression),
        backup_database.s(),
        name=BACKUP_TASK_NAME,
    )


MCP_MASK_TOKEN_PURGE_TASK_NAME = "arabase-purge-expired-mcp-mask-tokens"


@app.task(name="arabase.tasks.purge_expired_mcp_mask_tokens")
def purge_expired_mcp_mask_tokens():
    """Remove expired records from the PostgreSQL mask-token vault.

    Expired records are already ignored and issuance purges a batch on the way,
    so this only keeps the table small on an instance that issues rarely.
    """

    from arabase.mcp.protection.vault import purge_expired_mask_tokens

    deleted = purge_expired_mask_tokens()
    if deleted:
        logger.info("Purged %d expired MCP mask-token records.", deleted)


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_mcp_mask_token_purge(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(hours=1),
        purge_expired_mcp_mask_tokens.s(),
        name=MCP_MASK_TOKEN_PURGE_TASK_NAME,
    )
