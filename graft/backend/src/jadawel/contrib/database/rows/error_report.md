# backend/src/jadawel/contrib/database/rows/error_report.py

- RowErrorReport · class · L10-L75 — class RowErrorReport
- __init__ · method · L11-L29 — def __init__( self, rows: List[Dict[str, Any]], error_limit: int = settings.JADAWEL_MAX_ROW_REPORT_ERROR_COUNT, )
- add_error · method · L31-L45 — def add_error(self, row_index: RowIndex, error: Dict[str, Any])
- update_row · method · L47-L48 — def update_row(self, row_index: RowIndex, new_row: Dict[str, Any])
- get_valid_rows_and_mapping · method · L50-L64 — def get_valid_rows_and_mapping( self, ) -> Tuple[List[Dict[str, Any]], Dict[RowIndex, RowIndex]]
- to_dict · method · L66-L75 — def to_dict(self) -> Dict[RowIndex, Dict[str, Any]]
