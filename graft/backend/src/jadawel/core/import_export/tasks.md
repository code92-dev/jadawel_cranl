# backend/src/jadawel/core/import_export/tasks.py

- mark_import_export_resources_for_deletion · function · L31-L47 — def mark_import_export_resources_for_deletion( self, older_than_days: int = settings.JADAWEL_IMPORT_EXPORT_RESOURCE_REMOVAL_AFTER_DAYS, )
- delete_marked_import_export_resources · function · L59-L64 — def delete_marked_import_export_resources(self)
- setup_periodic_tasks · function · L68-L80 — def setup_periodic_tasks(sender, **kwargs)
