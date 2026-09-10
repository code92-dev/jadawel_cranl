# backend/src/jadawel/contrib/database/search/models.py

- PendingSearchValueUpdateTrashManager · class · L8-L10 — class PendingSearchValueUpdateTrashManager(CTEManager)
- get_queryset · method · L9-L10 — def get_queryset(self)
- PendingSearchValueUpdate · class · L13-L72 — class PendingSearchValueUpdate(models.Model)
- Meta · class · L51-L72 — class Meta: # Avoid duplicate entries for the same field and row.
- AbstractSearchValue · class · L75-L102 — class AbstractSearchValue(models.Model)
- Meta · class · L101-L102 — class Meta
- get_search_indexes · function · L105-L116 — def get_search_indexes(workspace_id: int) -> list[models.Index]
