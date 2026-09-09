# backend/src/jadawel/core/psycopg.py

- is_deadlock_error · function · L28-L29 — def is_deadlock_error(exc: OperationalError) -> bool
- is_unique_violation_error · function · L32-L35 — def is_unique_violation_error(exc: Exception) -> bool
- is_index_row_size_error · function · L38-L53 — def is_index_row_size_error(exc: Exception) -> bool
