# backend/src/jadawel/contrib/database/export/handler.py

- ExportHandler · class · L46-L201 — class ExportHandler
- _raise_if_no_export_permissions · method · L48-L62 — def _raise_if_no_export_permissions( user: Optional[User], table: Table, view: Optional[View] )
- create_and_start_new_job · method · L65-L90 — def create_and_start_new_job( user: Optional[User], table: Table, view: Optional[View], export_options: Dict[str, Any], ) -> ExportJob
- create_pending_export_job · method · L93-L138 — def create_pending_export_job( user: Optional[User], table: Table, view: Optional[View], export_options: Dict[str, Any], )
- run_export_job · method · L141-L165 — def run_export_job(job) -> ExportJob
- export_file_path · method · L168-L177 — def export_file_path(exported_file_name) -> str
- clean_up_old_jobs · method · L180-L201 — def clean_up_old_jobs()
- _raise_if_invalid_view_or_table_for_exporter · function · L204-L223 — def _raise_if_invalid_view_or_table_for_exporter( exporter_type: str, view: Optional[View] )
- _raise_if_invalid_order_by_or_filters · function · L226-L268 — def _raise_if_invalid_order_by_or_filters( table: Table, view: Optional[View], export_options: dict )
- _cancel_unfinished_jobs · function · L271-L285 — def _cancel_unfinished_jobs(user)
- _mark_job_as_finished · function · L288-L299 — def _mark_job_as_finished(export_job: ExportJob) -> ExportJob
- _mark_job_as_failed · function · L302-L315 — def _mark_job_as_failed(job, e)
- _register_action · function · L318-L330 — def _register_action(job)
- _open_file_and_run_export · function · L333-L384 — def _open_file_and_run_export(job: ExportJob) -> ExportJob
- _generate_random_file_name_with_extension · function · L387-L388 — def _generate_random_file_name_with_extension(file_extension)
