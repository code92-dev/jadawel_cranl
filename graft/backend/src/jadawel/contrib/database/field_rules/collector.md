# backend/src/jadawel/contrib/database/field_rules/collector.py

- CascadeUpdatedRows · class · L10-L13 — class CascadeUpdatedRows
- FieldRuleCollector · class · L16-L92 — class FieldRuleCollector
- __init__ · method · L37-L39 — def __init__(self, for_model: "GeneratedTableModel")
- set_starting_rows · method · L41-L43 — def set_starting_rows(self, rows: "list[GeneratedTableModel]")
- add_starting_rows · method · L45-L47 — def add_starting_rows(self, rows: "list[GeneratedTableModel]")
- is_starting_row_processed · method · L49-L50 — def is_starting_row_processed(self, row: "GeneratedTableModel")
- add_changes · method · L52-L64 — def add_changes(self, changes: "list[RowRuleChanges]")
- get_processed_rows · method · L66-L76 — def get_processed_rows(self) -> CascadeUpdatedRows
- visited · method · L79-L80 — def visited(self)
- reset · method · L82-L92 — def reset(self)
