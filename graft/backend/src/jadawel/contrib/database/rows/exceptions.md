# backend/src/jadawel/contrib/database/rows/exceptions.py

- RowDoesNotExist · class · L1-L8 — class RowDoesNotExist(Exception)
- __init__ · method · L4-L8 — def __init__(self, ids, *args, **kwargs)
- RowIdsNotUnique · class · L11-L16 — class RowIdsNotUnique(Exception)
- __init__ · method · L14-L16 — def __init__(self, ids, *args, **kwargs)
- ReportMaxErrorCountExceeded · class · L19-L26 — class ReportMaxErrorCountExceeded(Exception)
- __init__ · method · L24-L26 — def __init__(self, report, *args, **kwargs)
- CannotCreateRowsInTable · class · L29-L32 — class CannotCreateRowsInTable(Exception)
- CannotDeleteRowsInTable · class · L35-L38 — class CannotDeleteRowsInTable(Exception)
- InvalidRowLength · class · L41-L47 — class InvalidRowLength(Exception)
- __init__ · method · L46-L47 — def __init__(self, row_idx: int)
