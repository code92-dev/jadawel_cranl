# backend/src/arabase/integrations/local_jadawel/models.py

- LocalJadawelGroupedAggregateRows · class · L19-L34 — class LocalJadawelGroupedAggregateRows( LocalJadawelViewService, LocalJadawelFilterableServiceMixin, SearchableServiceMixin, )
- LocalJadawelTableServiceAggregationSeries · class · L37-L77 — class LocalJadawelTableServiceAggregationSeries(models.Model)
- Meta · class · L57-L58 — class Meta
- __repr__ · method · L60-L64 — def __repr__(self)
- key · method · L67-L77 — def key(self) -> str
- series_key · function · L80-L81 — def series_key(field_id: int | None, aggregation_type: str) -> str
- LocalJadawelTableServiceAggregationGroupBy · class · L84-L105 — class LocalJadawelTableServiceAggregationGroupBy(models.Model)
- Meta · class · L101-L102 — class Meta
- __repr__ · method · L104-L105 — def __repr__(self)
- LocalJadawelTableServiceAggregationSortBy · class · L108-L147 — class LocalJadawelTableServiceAggregationSortBy(models.Model)
- Meta · class · L140-L141 — class Meta
- __repr__ · method · L143-L147 — def __repr__(self)
- LocalJadawelUpcomingRows · class · L150-L186 — class LocalJadawelUpcomingRows( LocalJadawelViewService, LocalJadawelFilterableServiceMixin, LocalJadawelFilterableSortableMixin, SearchableServiceMixin, )
