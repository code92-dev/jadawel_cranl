"""Re-check managed workspace authority when queued jobs actually start.

Job creation validates the submitting user, but a worker may run after a member
was suspended, removed, or the organization entered restricted mode.  The core
job signal gives this plugin a registry-safe execution boundary without
changing the upstream job runner.
"""

from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from jadawel.core.handler import CoreHandler
from jadawel.core.jobs.exceptions import JobTypeDoesNotExist
from jadawel.core.jobs.registries import job_type_registry


def _workspace_context(job: Any) -> tuple[str, Any, Any] | None:
    """Return ``(operation, workspace, context)`` for workspace-bound jobs."""

    job_type = job_type_registry.get_by_model(job).type
    if job_type == "duplicate_application":
        application = job.original_application
        return "application.duplicate", application.workspace, application
    if job_type == "install_template":
        return "workspace.create_application", job.workspace, job.workspace
    if job_type == "export_applications":
        return "workspace.export", job.workspace, job.workspace
    if job_type == "import_applications":
        return "workspace.create_application", job.workspace, job.workspace
    if job_type == "create_snapshot":
        application = job.snapshot.snapshot_from_application
        return "application.create_snapshot", application.workspace, application
    if job_type == "restore_snapshot":
        application = job.snapshot.snapshot_from_application
        return "application.snapshot.restore", application.workspace, job.snapshot
    if job_type == "duplicate_table":
        table = job.original_table
        return "database.table.duplicate", table.database.workspace, table
    if job_type == "duplicate_field":
        field = job.original_field
        return "database.table.field.duplicate", field.table.database.workspace, field
    if job_type == "file_import":
        if job.table_id:
            table = job.table
            return "database.table.import_rows", table.database.workspace, table
        database = job.database
        return "database.create_table", database.workspace, database
    if job_type == "sync_data_sync_table":
        data_sync = job.data_sync
        table = data_sync.table
        return "database.data_sync.sync_table", table.database.workspace, table
    if job_type == "airtable":
        return "workspace.run_airtable_import", job.workspace, job.workspace
    if job_type == "duplicate_automation_workflow":
        workflow = job.original_automation_workflow
        return (
            "automation.workflow.duplicate",
            workflow.automation.workspace,
            workflow,
        )
    if job_type == "publish_automation_workflow":
        workflow = job.automation_workflow
        return "automation.publish_workflow", workflow.automation.workspace, workflow
    if job_type == "duplicate_page":
        page = job.original_page
        return "builder.page.duplicate", page.builder.workspace, page
    if job_type == "publish_domain":
        domain = job.domain
        return "builder.domain.publish", domain.builder.workspace, domain
    return None


def enforce_managed_job_access(sender: Any, job: Any, user: Any, **kwargs: Any) -> None:
    """Reject a queued job whose managed workspace authority has since changed."""

    del sender, kwargs
    try:
        permission = _workspace_context(job)
    except (
        AttributeError,
        KeyError,
        TypeError,
        ObjectDoesNotExist,
        JobTypeDoesNotExist,
    ):
        # Deleted or non-workspace jobs are handled by their existing job type.
        return
    if permission is None:
        return
    operation, workspace, context = permission
    CoreHandler().check_permissions(
        user, operation, workspace=workspace, context=context
    )
