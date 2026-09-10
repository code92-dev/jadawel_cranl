# backend/src/jadawel/contrib/builder/pages/models.py

- PageWithoutSharedManager · class · L23-L30 — class PageWithoutSharedManager(models.Manager)
- get_queryset · method · L29-L30 — def get_queryset(self)
- Page · class · L33-L109 — class Page( HierarchicalModelMixin, TrashableModelMixin, CreatedAndUpdatedOnMixin, OrderableMixin, models.Model, )
- VISIBILITY_TYPES · class · L40-L42 — class VISIBILITY_TYPES(models.TextChoices)
- ROLE_TYPES · class · L44-L47 — class ROLE_TYPES(models.TextChoices)
- Meta · class · L89-L98 — class Meta
- get_parent · method · L100-L101 — def get_parent(self)
- get_last_order · method · L104-L106 — def get_last_order(cls, builder: "Builder")
- __str__ · method · L108-L109 — def __str__(self)
- DuplicatePageJob · class · L112-L129 — class DuplicatePageJob( JobWithUserIpAddress, JobWithWebsocketId, JobWithUndoRedoIds, Job )
