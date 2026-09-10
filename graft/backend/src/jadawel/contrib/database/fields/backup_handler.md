# backend/src/jadawel/contrib/database/fields/backup_handler.py

- FieldDataBackupHandler · class · L16-L349 — class FieldDataBackupHandler
- duplicate_field_data · method · L38-L80 — def duplicate_field_data( cls, original_field: Field, duplicated_field: Field ) -> None
- _get_values_map_from_original_to_duplicated · method · L83-L93 — def _get_values_map_from_original_to_duplicated( cls, original_field, duplicated_field )
- backup_field_data · method · L96-L150 — def backup_field_data( cls, field_to_backup: Field, identifier_to_backup_into: str, ) -> BackupData
- restore_backup_data_into_field · method · L153-L192 — def restore_backup_data_into_field( cls, field_to_restore_backup_data_into: Field, backup_data: BackupData, )
- clean_up_backup_data · method · L195-L218 — def clean_up_backup_data( cls, backup_data: BackupData, )
- _create_duplicate_m2m_table · method · L221-L230 — def _create_duplicate_m2m_table( model: GeneratedTableModel, m2m_model_field_to_duplicate: ManyToManyField, new_m2m_table_name: str, )
- _truncate_table · method · L233-L239 — def _truncate_table(target_table)
- _drop_table · method · L242-L248 — def _drop_table(backup_name: str)
- _get_source_column_sql_with_mapping · method · L251-L266 — def _get_source_column_sql_with_mapping( cls, source_column: str, mapping: Optional[Dict[int, int]] = None )
- _copy_m2m_data_between_tables · method · L269-L305 — def _copy_m2m_data_between_tables( cls, source_table: str, target_table: str, m2m_model_field: ManyToManyField, through_model: GeneratedTableModel, m2m_target_model_field: Optional[ManyToManyField] = None, mapping_values: Optional[Dict[int, int]] = None, )
- _create_duplicate_nullable_column · method · L308-L319 — def _create_duplicate_nullable_column( model: GeneratedTableModel, model_field_to_duplicate, new_column_name: str )
- _copy_not_null_column_data · method · L322-L339 — def _copy_not_null_column_data( cls, table_name, source_column, target_column, mapping_values=None )
- _drop_column · method · L342-L349 — def _drop_column(table_name: str, column_to_drop: str)
